"""Unit tests for app.services.preprocessing."""
from unittest.mock import MagicMock, patch

import pytest

from app.services.preprocessing import get_duration, preprocess_audio


class TestPreprocessAudio:
    def _make_run(self, returncode=0, stderr=""):
        m = MagicMock()
        m.returncode = returncode
        m.stderr = stderr
        return m

    def test_calls_ffmpeg(self):
        with patch("subprocess.run", return_value=self._make_run()) as mock_run:
            preprocess_audio("/in.mp3", "/out.wav")
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "ffmpeg"
        assert "/in.mp3" in cmd
        assert "/out.wav" in cmd

    def test_sets_16khz_mono(self):
        with patch("subprocess.run", return_value=self._make_run()) as mock_run:
            preprocess_audio("/in.mp3", "/out.wav")
        cmd = mock_run.call_args[0][0]
        assert "-ar" in cmd
        assert "16000" in cmd
        assert "-ac" in cmd
        assert "1" in cmd

    def test_applies_loudnorm(self):
        with patch("subprocess.run", return_value=self._make_run()) as mock_run:
            preprocess_audio("/in.mp3", "/out.wav")
        cmd = mock_run.call_args[0][0]
        assert "loudnorm" in " ".join(cmd)

    def test_raises_on_ffmpeg_failure(self):
        with patch("subprocess.run", return_value=self._make_run(returncode=1, stderr="codec error")):
            with pytest.raises(RuntimeError, match="ffmpeg failed"):
                preprocess_audio("/in.mp3", "/out.wav")

    def test_overwrite_flag(self):
        with patch("subprocess.run", return_value=self._make_run()) as mock_run:
            preprocess_audio("/in.mp3", "/out.wav")
        cmd = mock_run.call_args[0][0]
        assert "-y" in cmd


class TestGetDuration:
    def _make_run(self, stdout="", returncode=0, stderr=""):
        m = MagicMock()
        m.returncode = returncode
        m.stdout = stdout
        m.stderr = stderr
        return m

    def test_returns_float(self):
        with patch("subprocess.run", return_value=self._make_run(stdout="120.5\n")):
            result = get_duration("/audio.mp3")
        assert result == pytest.approx(120.5)

    def test_calls_ffprobe(self):
        with patch("subprocess.run", return_value=self._make_run(stdout="30.0\n")) as mock_run:
            get_duration("/audio.mp3")
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "ffprobe"
        assert "/audio.mp3" in cmd

    def test_raises_on_ffprobe_failure(self):
        with patch("subprocess.run", return_value=self._make_run(returncode=1, stderr="no such file")):
            with pytest.raises(RuntimeError, match="ffprobe failed"):
                get_duration("/missing.mp3")

    def test_integer_duration(self):
        with patch("subprocess.run", return_value=self._make_run(stdout="300\n")):
            assert get_duration("/x.mp3") == 300.0

    def test_strips_whitespace(self):
        with patch("subprocess.run", return_value=self._make_run(stdout="  45.123  \n")):
            result = get_duration("/x.mp3")
        assert result == pytest.approx(45.123)
