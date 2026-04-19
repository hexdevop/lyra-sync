import hashlib
import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.audio_job import AudioJob
from app.schemas.audio import LyricLine, ResultResponse, StatusResponse, UploadResponse
from app.services.storage import storage
from app.workers.pipeline import process_audio_job

router = APIRouter(prefix="/audio", tags=["audio"])

ALLOWED_CONTENT_TYPES = {"audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp4", "audio/x-m4a"}
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a"}


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_audio(
    request: Request,
    file: Annotated[UploadFile, File(...)],
    db: AsyncSession = Depends(get_db),
):
    # Validate extension
    suffix = ""
    if file.filename:
        for ext in ALLOWED_EXTENSIONS:
            if file.filename.lower().endswith(ext):
                suffix = ext
                break
    if not suffix:
        raise HTTPException(400, "Поддерживаются только mp3, wav, m4a")

    # Read and check size
    data = await file.read()
    size_mb = len(data) / (1024 * 1024)
    if size_mb > settings.max_file_size_mb:
        raise HTTPException(413, f"Файл превышает {settings.max_file_size_mb} MB")

    # Hash for cache lookup
    file_hash = hashlib.sha256(data).hexdigest()

    # Check cache
    cached = await db.scalar(
        select(AudioJob).where(
            AudioJob.file_hash == file_hash,
            AudioJob.status == "done",
        )
    )
    if cached:
        return UploadResponse(audio_id=cached.id, status="done")

    # Create job record
    job = AudioJob(id=uuid.uuid4(), status="pending", file_hash=file_hash)
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Upload raw file to S3
    s3_key = f"raw/{job.id}{suffix}"
    await storage.upload_bytes(data, s3_key)
    job.file_url = s3_key
    job.status = "queued"
    await db.commit()

    # Enqueue worker job (sync RQ enqueue via redis)
    from redis import Redis
    from rq import Queue

    redis_conn = Redis.from_url(settings.redis_url)
    q = Queue("pipeline", connection=redis_conn)
    q.enqueue(process_audio_job, str(job.id), job_timeout=1800)

    return UploadResponse(audio_id=job.id, status="queued")


@router.get("/{audio_id}/status", response_model=StatusResponse)
async def get_status(audio_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    job = await db.get(AudioJob, audio_id)
    if not job:
        raise HTTPException(404, "Задача не найдена")
    return StatusResponse(
        audio_id=job.id,
        status=job.status,
        error_message=job.error_message,
    )


@router.get("/{audio_id}/result", response_model=ResultResponse)
async def get_result(audio_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    job = await db.get(AudioJob, audio_id)
    if not job:
        raise HTTPException(404, "Задача не найдена")
    if job.status != "done":
        raise HTTPException(400, f"Задача ещё не завершена: {job.status}")

    result_data = await storage.download_json(job.result_url)

    lines = [LyricLine(**ln) for ln in result_data.get("lines", [])]
    lrc = result_data.get("lrc", "")
    srt = result_data.get("srt", "")

    return ResultResponse(audio_id=job.id, status=job.status, json=lines, lrc=lrc, srt=srt)
