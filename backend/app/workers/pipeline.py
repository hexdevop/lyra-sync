"""
RQ worker: full pipeline for one audio job.
Runs synchronously inside the worker process (no asyncio).
"""
import json
import tempfile
import uuid
from pathlib import Path

import psycopg2
from psycopg2.extras import register_uuid

from app.config import settings
from app.services.alignment import align_from_whisper, align_with_lyrics
from app.services.asr import transcribe
from app.services.formatter import build_result
from app.services.lyrics import fetch_lyrics
from app.services.preprocessing import get_duration, preprocess_audio
from app.services.separation import separate_vocals
from app.services.storage import storage

register_uuid()


def _db_conn():
    dsn = settings.database_url.replace("+asyncpg", "")
    return psycopg2.connect(dsn)


def _update_status(conn, job_id: str, status: str, error: str | None = None):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE audio_jobs SET status=%s, error_message=%s, updated_at=NOW() WHERE id=%s",
            (status, error, uuid.UUID(job_id)),
        )
    conn.commit()


def process_audio_job(job_id: str) -> None:
    conn = _db_conn()
    try:
        _update_status(conn, job_id, "processing")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            # 1. Fetch raw file from S3
            with conn.cursor() as cur:
                cur.execute("SELECT file_url FROM audio_jobs WHERE id=%s", (uuid.UUID(job_id),))
                row = cur.fetchone()
            if not row:
                raise RuntimeError("Job not found")
            raw_key = row[0]
            suffix = Path(raw_key).suffix
            raw_local = str(tmp_path / f"raw{suffix}")
            storage.download_to_file_sync(raw_key, raw_local)

            # 2. Check duration
            dur = get_duration(raw_local)
            if dur > settings.max_duration_sec:
                raise RuntimeError(f"Аудио превышает {settings.max_duration_sec // 60} минут")

            # 3. Preprocess
            processed = str(tmp_path / "processed.wav")
            preprocess_audio(raw_local, processed)

            # 4. Vocal separation
            vocals, _ = separate_vocals(processed, tmp)

            # 5. ASR
            segments = transcribe(vocals)

            # 6. Fetch Genius lyrics
            lyric_lines = fetch_lyrics(segments)

            # 7. Align lyrics to timestamps
            if lyric_lines:
                aligned = align_with_lyrics(segments, lyric_lines)
            else:
                aligned = align_from_whisper(segments)

            # 8. Build result
            result = build_result(aligned)

            # 9. Upload result to S3
            result_key = f"results/{job_id}/result.json"
            result_bytes = json.dumps(result, ensure_ascii=False).encode()
            storage.upload_bytes_sync(result_bytes, result_key)

            # 10. Mark done
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE audio_jobs SET status='done', result_url=%s, updated_at=NOW() WHERE id=%s",
                    (result_key, uuid.UUID(job_id)),
                )
            conn.commit()

    except Exception as exc:
        _update_status(conn, job_id, "failed", str(exc))
        raise
    finally:
        conn.close()
