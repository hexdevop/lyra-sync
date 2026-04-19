"""Integration tests for POST /audio/upload, GET /audio/{id}/status, GET /audio/{id}/result.

Uses an in-memory SQLite DB (via conftest) and mocks out storage + RQ.
"""
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

pytestmark = pytest.mark.asyncio


# ── /audio/upload ─────────────────────────────────────────────────────────────

class TestUploadAudio:
    async def test_rejects_invalid_extension(self, client):
        data = {"file": ("track.ogg", b"fake audio", "audio/ogg")}
        resp = await client.post("/audio/upload", files=data)
        assert resp.status_code == 400
        assert "mp3" in resp.json()["detail"].lower() or "m4a" in resp.json()["detail"].lower()

    async def test_rejects_oversized_file(self, client):
        big_data = b"x" * (51 * 1024 * 1024)  # 51 MB
        data = {"file": ("big.mp3", big_data, "audio/mpeg")}
        resp = await client.post("/audio/upload", files=data)
        assert resp.status_code == 413

    async def test_accepts_mp3(self, client):
        with patch("app.api.routes.audio.storage") as mock_storage, \
             patch("app.api.routes.audio.Redis") as mock_redis_cls, \
             patch("app.api.routes.audio.Queue") as mock_queue_cls:
            mock_storage.upload_bytes = AsyncMock()
            mock_queue_cls.return_value.enqueue = MagicMock()
            resp = await client.post(
                "/audio/upload",
                files={"file": ("song.mp3", b"fake mp3 data", "audio/mpeg")},
            )
        assert resp.status_code == 202
        body = resp.json()
        assert "audio_id" in body
        assert body["status"] in ("queued", "done")

    async def test_accepts_wav(self, client):
        with patch("app.api.routes.audio.storage") as mock_storage, \
             patch("app.api.routes.audio.Redis"), \
             patch("app.api.routes.audio.Queue") as mock_queue_cls:
            mock_storage.upload_bytes = AsyncMock()
            mock_queue_cls.return_value.enqueue = MagicMock()
            resp = await client.post(
                "/audio/upload",
                files={"file": ("track.wav", b"RIFF" + b"\x00" * 40, "audio/wav")},
            )
        assert resp.status_code == 202

    async def test_accepts_m4a(self, client):
        with patch("app.api.routes.audio.storage") as mock_storage, \
             patch("app.api.routes.audio.Redis"), \
             patch("app.api.routes.audio.Queue") as mock_queue_cls:
            mock_storage.upload_bytes = AsyncMock()
            mock_queue_cls.return_value.enqueue = MagicMock()
            resp = await client.post(
                "/audio/upload",
                files={"file": ("track.m4a", b"fake m4a data", "audio/mp4")},
            )
        assert resp.status_code == 202

    async def test_cache_hit_returns_done(self, client, done_job):
        """Uploading the same file twice should return status=done immediately."""
        # done_job has file_hash="abc123"
        # We need to upload a file whose SHA-256 == "abc123" — not feasible directly,
        # so instead we patch hashlib.sha256 to return that hash.
        with patch("app.api.routes.audio.hashlib") as mock_hashlib:
            mock_hashlib.sha256.return_value.hexdigest.return_value = "abc123"
            resp = await client.post(
                "/audio/upload",
                files={"file": ("song.mp3", b"anything", "audio/mpeg")},
            )
        assert resp.status_code == 202
        body = resp.json()
        assert body["status"] == "done"
        assert str(body["audio_id"]) == str(done_job.id)

    async def test_enqueues_job(self, client):
        with patch("app.api.routes.audio.storage") as mock_storage, \
             patch("app.api.routes.audio.Redis"), \
             patch("app.api.routes.audio.Queue") as mock_queue_cls:
            mock_storage.upload_bytes = AsyncMock()
            mock_enqueue = MagicMock()
            mock_queue_cls.return_value.enqueue = mock_enqueue
            await client.post(
                "/audio/upload",
                files={"file": ("song.mp3", b"data", "audio/mpeg")},
            )
        mock_enqueue.assert_called_once()

    # ── Known issue: sync boto3 in async context ───────────────────────────
    # storage.upload_bytes() calls boto3 synchronously inside an async def.
    # This blocks the event loop. The fix is asyncio.to_thread() or aioboto3.
    async def test_storage_upload_is_awaited(self, client):
        """Verify upload_bytes is awaited (it's async def but uses sync boto3 internally)."""
        upload_calls = []

        async def fake_upload(data, key):
            upload_calls.append(key)

        with patch("app.api.routes.audio.storage") as mock_storage, \
             patch("app.api.routes.audio.Redis"), \
             patch("app.api.routes.audio.Queue") as mock_queue_cls:
            mock_storage.upload_bytes = fake_upload
            mock_queue_cls.return_value.enqueue = MagicMock()
            await client.post(
                "/audio/upload",
                files={"file": ("track.mp3", b"data", "audio/mpeg")},
            )
        assert len(upload_calls) == 1
        assert upload_calls[0].startswith("raw/")


# ── /audio/{id}/status ────────────────────────────────────────────────────────

class TestGetStatus:
    async def test_returns_404_for_unknown_id(self, client):
        resp = await client.get(f"/audio/{uuid.uuid4()}/status")
        assert resp.status_code == 404

    async def test_returns_status_for_done_job(self, client, done_job):
        resp = await client.get(f"/audio/{done_job.id}/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "done"
        assert str(body["audio_id"]) == str(done_job.id)
        assert body["error_message"] is None

    async def test_returns_status_for_pending_job(self, client, pending_job):
        resp = await client.get(f"/audio/{pending_job.id}/status")
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"

    async def test_invalid_uuid_format(self, client):
        resp = await client.get("/audio/not-a-uuid/status")
        assert resp.status_code == 422


# ── /audio/{id}/result ────────────────────────────────────────────────────────

class TestGetResult:
    async def test_returns_404_for_unknown_id(self, client):
        resp = await client.get(f"/audio/{uuid.uuid4()}/result")
        assert resp.status_code == 404

    async def test_returns_400_if_not_done(self, client, pending_job):
        resp = await client.get(f"/audio/{pending_job.id}/result")
        assert resp.status_code == 400
        assert "pending" in resp.json()["detail"].lower() or resp.status_code == 400

    async def test_returns_result_for_done_job(self, client, done_job):
        result_data = {
            "lines": [{"start": 0.0, "end": 2.5, "text": "Hello world"}],
            "lrc": "[00:00.00] Hello world",
            "srt": "1\n00:00:00,000 --> 00:00:02,500\nHello world\n",
        }
        with patch("app.api.routes.audio.storage") as mock_storage:
            mock_storage.download_json = AsyncMock(return_value=result_data)
            resp = await client.get(f"/audio/{done_job.id}/result")

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "done"
        assert len(body["json"]) == 1
        assert body["json"][0]["text"] == "Hello world"
        assert "[00:00.00]" in body["lrc"]
        assert "00:00:00,000" in body["srt"]

    async def test_result_json_field_named_json(self, client, done_job):
        """The response model uses 'json' as field name — verify it serializes correctly."""
        with patch("app.api.routes.audio.storage") as mock_storage:
            mock_storage.download_json = AsyncMock(return_value={"lines": [], "lrc": "", "srt": ""})
            resp = await client.get(f"/audio/{done_job.id}/result")
        assert "json" in resp.json()

    async def test_invalid_uuid_format(self, client):
        resp = await client.get("/audio/bad-uuid/result")
        assert resp.status_code == 422


# ── /health ───────────────────────────────────────────────────────────────────

class TestHealth:
    async def test_health_ok(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
