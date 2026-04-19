from dataclasses import dataclass

from faster_whisper import WhisperModel

from app.config import settings

_model: WhisperModel | None = None


def get_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel(
            settings.whisper_model,
            device=settings.whisper_device,
            compute_type="float16" if settings.whisper_device == "cuda" else "int8",
        )
    return _model


@dataclass
class WordTimestamp:
    start: float
    end: float
    word: str


@dataclass
class Segment:
    start: float
    end: float
    text: str
    words: list[WordTimestamp]


def transcribe(audio_path: str) -> list[Segment]:
    model = get_model()
    segments_iter, info = model.transcribe(
        audio_path,
        word_timestamps=True,
        beam_size=5,
    )
    segments = []
    for seg in segments_iter:
        words = []
        if seg.words:
            for w in seg.words:
                words.append(WordTimestamp(start=w.start, end=w.end, word=w.word))
        segments.append(
            Segment(start=seg.start, end=seg.end, text=seg.text.strip(), words=words)
        )
    return segments
