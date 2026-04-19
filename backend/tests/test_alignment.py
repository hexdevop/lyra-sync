"""Unit tests for app.services.alignment."""
import json
import subprocess
from dataclasses import dataclass
from unittest.mock import MagicMock, mock_open, patch

import pytest

from app.services.alignment import AlignedLine, align_from_whisper, align_with_aeneas


# ── Helpers ───────────────────────────────────────────────────────────────────

@dataclass
class FakeSegment:
    start: float
    end: float
    text: str


def make_aeneas_json(fragments: list[dict]) -> str:
    return json.dumps({"fragments": fragments})


# ── align_from_whisper ────────────────────────────────────────────────────────

class TestAlignFromWhisper:
    def test_basic(self):
        segs = [
            FakeSegment(0.0, 2.5, "Hello"),
            FakeSegment(2.5, 5.0, "World"),
        ]
        result = align_from_whisper(segs)
        assert len(result) == 2
        assert result[0] == AlignedLine(0.0, 2.5, "Hello")
        assert result[1] == AlignedLine(2.5, 5.0, "World")

    def test_empty(self):
        assert align_from_whisper([]) == []

    def test_preserves_order(self):
        segs = [FakeSegment(float(i), float(i + 1), f"Line {i}") for i in range(5)]
        result = align_from_whisper(segs)
        assert [r.text for r in result] == [f"Line {i}" for i in range(5)]

    def test_returns_aligned_line_type(self):
        segs = [FakeSegment(0.0, 1.0, "test")]
        result = align_from_whisper(segs)
        assert isinstance(result[0], AlignedLine)


# ── align_with_aeneas ─────────────────────────────────────────────────────────

class TestAlignWithAeneas:
    def _make_run_result(self, fragments: list[dict], returncode: int = 0):
        mock = MagicMock()
        mock.returncode = returncode
        mock.stderr = ""
        return mock, make_aeneas_json(fragments)

    def test_happy_path(self, tmp_path):
        fragments = [
            {"begin": "0.000", "end": "2.500", "lines": ["Hello world"]},
            {"begin": "2.500", "end": "5.000", "lines": ["Second line"]},
        ]
        out_json = make_aeneas_json(fragments)

        with patch("subprocess.run") as mock_run, \
             patch("pathlib.Path.write_text"), \
             patch("pathlib.Path.read_text", return_value=out_json):
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            result = align_with_aeneas("/fake/vocals.wav", ["Hello world", "Second line"])

        assert len(result) == 2
        assert result[0].start == 0.0
        assert result[0].end == 2.5
        assert result[0].text == "Hello world"

    def test_raises_on_nonzero_exit(self, tmp_path):
        with patch("subprocess.run") as mock_run, \
             patch("pathlib.Path.write_text"):
            mock_run.return_value = MagicMock(returncode=1, stderr="aeneas error msg")
            with pytest.raises(RuntimeError, match="aeneas failed"):
                align_with_aeneas("/fake/vocals.wav", ["line one"])

    def test_empty_lines_in_fragment(self, tmp_path):
        """Fragment with empty lines list should produce empty text, not crash."""
        fragments = [{"begin": "0.0", "end": "1.0", "lines": []}]
        out_json = make_aeneas_json(fragments)

        with patch("subprocess.run") as mock_run, \
             patch("pathlib.Path.write_text"), \
             patch("pathlib.Path.read_text", return_value=out_json):
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            result = align_with_aeneas("/fake/vocals.wav", [""])
        assert result[0].text == ""

    def test_no_fragments_key(self, tmp_path):
        out_json = json.dumps({})
        with patch("subprocess.run") as mock_run, \
             patch("pathlib.Path.write_text"), \
             patch("pathlib.Path.read_text", return_value=out_json):
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            result = align_with_aeneas("/fake/vocals.wav", ["x"])
        assert result == []

    def test_correct_command_built(self, tmp_path):
        out_json = make_aeneas_json([])
        with patch("subprocess.run") as mock_run, \
             patch("pathlib.Path.write_text"), \
             patch("pathlib.Path.read_text", return_value=out_json):
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            align_with_aeneas("/vocals.wav", ["x"])

        cmd = mock_run.call_args[0][0]
        assert "aeneas.tools.execute_task" in cmd
        assert "/vocals.wav" in cmd
