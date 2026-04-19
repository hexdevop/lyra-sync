from uuid import UUID

from pydantic import BaseModel


class UploadResponse(BaseModel):
    audio_id: UUID
    status: str


class StatusResponse(BaseModel):
    audio_id: UUID
    status: str
    error_message: str | None = None


class LyricLine(BaseModel):
    start: float
    end: float
    text: str


class ResultResponse(BaseModel):
    audio_id: UUID
    status: str
    json: list[LyricLine] | None = None
    lrc: str | None = None
    srt: str | None = None
