"""Generate JSON, LRC, and SRT from aligned lines."""
import json
from dataclasses import asdict

from app.services.alignment import AlignedLine


def _ts_lrc(seconds: float) -> str:
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m:02d}:{s:05.2f}"


def _ts_srt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def to_json(lines: list[AlignedLine]) -> list[dict]:
    return [{"start": ln.start, "end": ln.end, "text": ln.text} for ln in lines]


def to_lrc(lines: list[AlignedLine]) -> str:
    parts = []
    for ln in lines:
        parts.append(f"[{_ts_lrc(ln.start)}] {ln.text}")
    return "\n".join(parts)


def to_srt(lines: list[AlignedLine]) -> str:
    parts = []
    for i, ln in enumerate(lines, 1):
        parts.append(
            f"{i}\n{_ts_srt(ln.start)} --> {_ts_srt(ln.end)}\n{ln.text}\n"
        )
    return "\n".join(parts)


def build_result(lines: list[AlignedLine]) -> dict:
    return {
        "lines": to_json(lines),
        "lrc": to_lrc(lines),
        "srt": to_srt(lines),
    }
