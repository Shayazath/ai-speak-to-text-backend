
import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.transcript import Transcript
from app.services.speech_service import transcribe_audio

router = APIRouter(
    prefix="/api/speech",
    tags=["Speech Transcription"],
)
import inspect
import logging

from app.services.speech_service import transcribe_audio

logging.warning(
    "Speech service loaded from: %s",
    inspect.getfile(transcribe_audio),
)

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac"}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


@router.post("/transcribe")
def transcribe_uploaded_audio(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    filename = file.filename or ""
    extension = os.path.splitext(filename)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio format.",
        )

    temp_path = None

    try:
        # Save the upload to a temporary file.
        with tempfile.NamedTemporaryFile(
            suffix=extension,
            delete=False,
        ) as temp_file:
            temp_path = temp_file.name
            total_size = 0

            while True:
                chunk = file.file.read(1024 * 1024)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="Audio file exceeds the 25 MB limit.",
                    )

                temp_file.write(chunk)

        if total_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded audio file is empty.",
            )

        result = transcribe_audio(temp_path)

        if not result["text"]:
            raise HTTPException(
                status_code=422,
                detail="No speech could be detected in the audio.",
            )

        transcript = Transcript(
            title=os.path.splitext(os.path.basename(filename))[0][:255]
            or "Audio transcription",
            content=result["text"],
            language=result["language"],
            duration_seconds=result["duration_seconds"],
        )

        db.add(transcript)
        db.commit()
        db.refresh(transcript)

        return {
            "message": "Audio transcribed and saved successfully.",
            "transcript": {
                "id": transcript.id,
                "title": transcript.title,
                "content": transcript.content,
                "language": transcript.language,
                "duration_seconds": transcript.duration_seconds,
                "created_at": transcript.created_at,
            },
        }

    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Audio transcription failed.",
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

        file.file.close()
