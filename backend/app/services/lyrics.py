import re

import lyricsgenius
from rapidfuzz import fuzz

from app.config import settings


def _clean(text: str) -> str:
    return re.sub(r"\[.*?\]", "", text).strip()


def fetch_lyrics(whisper_segments: list) -> list[str] | None:
    """
    Use first 3-5 Whisper lines to identify song via Genius, then fetch full lyrics.
    Returns list of lyric lines or None if not found.
    """
    if not settings.genius_token:
        return None

    probe = " ".join(seg.text for seg in whisper_segments[:5])

    try:
        genius = lyricsgenius.Genius(settings.genius_token, verbose=False, timeout=10)
        song = genius.search_song(probe)
        if song is None:
            return None

        raw = song.lyrics or ""
        lines = [_clean(ln) for ln in raw.splitlines()]
        lines = [ln for ln in lines if ln]
        return lines
    except Exception:
        return None


def best_match_line(asr_text: str, lyric_lines: list[str]) -> str:
    """Return the lyric line that best matches the ASR text."""
    best, score = asr_text, 0
    for line in lyric_lines:
        s = fuzz.ratio(asr_text.lower(), line.lower())
        if s > score:
            score, best = s, line
    return best
