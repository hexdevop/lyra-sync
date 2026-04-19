"""Unit tests for app.services.separation.

Key finding: separate_vocals() runs Demucs on the PREPROCESSED 16kHz mono WAV
(not the original), which degrades separation quality. Tests document this
behavior so it's visible when fixing the pipeline order.
"""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.separation import separate_vocals


def _ok_run():
    m = MagicMock()
    m.returncode = 0
    m.stderr = ""
    return m


def _fail_run(stderr="demucs error"):
    m = MagicMock()
    m.returncode = 1
    m.stderr = stderr
    return m


class TestSeparateVocals:
    def test_returns_two_paths(self, tmp_path):
        with patch("subprocess.run", return_value=_ok_run()):
            vocals, instrumental = separate_vocals(str(tmp_path / "processed.wav"), str(tmp_path))
        assert isinstance(vocals, str)
        assert isinstance(instrumental, str)

    def test_vocals_path_contains_vocals(self, tmp_path):
        with patch("subprocess.run", return_value=_ok_run()):
            vocals, _ = separate_vocals(str(tmp_path / "processed.wav"), str(tmp_path))
        assert "vocals.wav" in vocals

    def test_instrumental_path(self, tmp_path):
        with patch("subprocess.run", return_value=_ok_run()):
            _, instrumental = separate_vocals(str(tmp_path / "processed.wav"), str(tmp_path))
        assert "no_vocals.wav" in instrumental

    def test_output_dir_structure(self, tmp_path):
        """Demucs outputs to: output_dir/htdemucs/{stem}/vocals.wav"""
        input_wav = str(tmp_path / "my_song.wav")
        with patch("subprocess.run", return_value=_ok_run()):
            vocals, _ = separate_vocals(input_wav, str(tmp_path))
        expected = str(tmp_path / "htdemucs" / "my_song" / "vocals.wav")
        assert vocals == expected

    def test_raises_on_failure(self, tmp_path):
        with patch("subprocess.run", return_value=_fail_run("GPU OOM")):
            with pytest.raises(RuntimeError, match="Demucs failed"):
                separate_vocals(str(tmp_path / "processed.wav"), str(tmp_path))

    def test_uses_htdemucs_model(self, tmp_path):
        with patch("subprocess.run", return_value=_ok_run()) as mock_run:
            separate_vocals(str(tmp_path / "processed.wav"), str(tmp_path))
        cmd = mock_run.call_args[0][0]
        assert "htdemucs" in cmd

    def test_two_stems_flag(self, tmp_path):
        with patch("subprocess.run", return_value=_ok_run()) as mock_run:
            separate_vocals(str(tmp_path / "processed.wav"), str(tmp_path))
        cmd = " ".join(mock_run.call_args[0][0])
        assert "--two-stems" in cmd and "vocals" in cmd

    def test_output_dir_passed(self, tmp_path):
        with patch("subprocess.run", return_value=_ok_run()) as mock_run:
            separate_vocals(str(tmp_path / "processed.wav"), str(tmp_path))
        cmd = mock_run.call_args[0][0]
        assert str(tmp_path) in cmd

    # ── Pipeline order issue ────────────────────────────────────────────────
    # KNOWN ISSUE: The pipeline passes preprocessed 16kHz mono audio to Demucs.
    # Demucs (htdemucs) expects 44100Hz stereo for best quality.
    # This test documents the expected (buggy) behavior so the issue is visible.
    def test_pipeline_receives_preprocessed_not_raw(self, tmp_path):
        """
        separate_vocals() is called with 'processed.wav' (16kHz mono),
        not the original raw file. This is a quality regression.
        The fix: run Demucs on raw audio BEFORE ffmpeg preprocessing.
        """
        input_path = str(tmp_path / "processed.wav")  # 16kHz mono — suboptimal
        with patch("subprocess.run", return_value=_ok_run()) as mock_run:
            separate_vocals(input_path, str(tmp_path))
        cmd = " ".join(mock_run.call_args[0][0])
        # Confirm it received the preprocessed (not raw) path
        assert "processed.wav" in cmd
