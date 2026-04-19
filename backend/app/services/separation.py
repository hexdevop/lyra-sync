import subprocess
from pathlib import Path


def separate_vocals(input_wav: str, output_dir: str) -> tuple[str, str]:
    """
    Run Demucs htdemucs model on input_wav.
    Returns (vocals_path, instrumental_path).
    """
    cmd = [
        "python", "-m", "demucs",
        "--two-stems", "vocals",
        "-n", "htdemucs",
        "-o", output_dir,
        input_wav,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Demucs failed: {result.stderr}")

    stem = Path(input_wav).stem
    base = Path(output_dir) / "htdemucs" / stem
    vocals = str(base / "vocals.wav")
    instrumental = str(base / "no_vocals.wav")
    return vocals, instrumental
