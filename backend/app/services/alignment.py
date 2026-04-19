"""
Forced alignment: maps lyric lines to timestamps.

Strategy:
  1. If Genius lyrics found → fuzzy-match each line to the closest Whisper segment.
  2. Fallback → use Whisper segment timestamps and text directly.
"""
from dataclasses import dataclass

from rapidfuzz import fuzz


@dataclass
class AlignedLine:
    start: float
    end: float
    text: str


def align_with_lyrics(segments: list, lyric_lines: list[str]) -> list[AlignedLine]:
    """
    Map Genius lyric lines to Whisper segment timestamps via fuzzy matching.
    Each lyric line is paired with the best-scoring Whisper segment, then
    timestamps are made monotone so the result is always playable.
    """
    if not segments:
        return []
    if not lyric_lines:
        return align_from_whisper(segments)

    seg_texts = [s.text.strip().lower() for s in segments]

    # For each lyric line find the Whisper segment it most likely belongs to.
    assigned: list[int] = []
    for line in lyric_lines:
        best = max(range(len(segments)),
                   key=lambda j: fuzz.partial_ratio(line.lower(), seg_texts[j]))
        assigned.append(best)

    result: list[AlignedLine] = []
    prev_end = segments[0].start

    for i, (line, seg_idx) in enumerate(zip(lyric_lines, assigned)):
        seg = segments[seg_idx]
        start = max(prev_end, seg.start)

        if i + 1 < len(assigned):
            next_seg = segments[assigned[i + 1]]
            end = max(start + 0.3, min(next_seg.start, seg.end + 2.0))
        else:
            end = max(start + 0.3, segments[-1].end)

        result.append(AlignedLine(start=start, end=end, text=line))
        prev_end = end

    return result


def align_from_whisper(segments: list) -> list[AlignedLine]:
    return [AlignedLine(start=s.start, end=s.end, text=s.text) for s in segments]
