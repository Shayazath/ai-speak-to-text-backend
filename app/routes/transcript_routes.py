from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Transcript
from app.schemas.transcript import (
    TranscriptCreate,
    TranscriptResponse,
)
from sqlalchemy import desc, or_
from fastapi import Query
router = APIRouter(
    prefix="/api/transcripts",
    tags=["Transcripts"],
)


@router.post(
    "",
    response_model=TranscriptResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_transcript(
    payload: TranscriptCreate,
    db: Session = Depends(get_db),
):
    transcript = Transcript(
        title=payload.title.strip(),
        content=payload.content,
        language=payload.language,
        duration_seconds=payload.duration_seconds,
    )

    db.add(transcript)
    db.commit()
    db.refresh(transcript)

    return transcript


@router.get("", response_model=list[TranscriptResponse])
def get_transcripts(
    search: str | None = Query(default=None, max_length=255),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Transcript)

    if search and search.strip():
        search_term = f"%{search.strip()}%"

        query = query.filter(
            or_(
                Transcript.title.ilike(search_term),
                Transcript.content.ilike(search_term),
            )
        )

    transcripts = (
        query
        .order_by(desc(Transcript.created_at), desc(Transcript.id))
        .offset(skip)
        .limit(limit)
        .all()
    )

    return transcripts


@router.get("/{transcript_id}", response_model=TranscriptResponse)
def get_transcript(
    transcript_id: int,
    db: Session = Depends(get_db),
):
    transcript = (
        db.query(Transcript)
        .filter(Transcript.id == transcript_id)
        .first()
    )

    if not transcript:
        raise HTTPException(
            status_code=404,
            detail="Transcript not found",
        )

    return transcript


from app.schemas.transcript import TranscriptUpdate


@router.put(
    "/{transcript_id}",
    response_model=TranscriptResponse,
)
def update_transcript(
    transcript_id: int,
    payload: TranscriptUpdate,
    db: Session = Depends(get_db),
):
    transcript = (
        db.query(Transcript)
        .filter(Transcript.id == transcript_id)
        .first()
    )

    if not transcript:
        raise HTTPException(
            status_code=404,
            detail="Transcript not found",
        )

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="At least one field must be provided",
        )

    if "title" in update_data:
        update_data["title"] = update_data["title"].strip()

        if not update_data["title"]:
            raise HTTPException(
                status_code=422,
                detail="Title cannot be empty",
            )

    for field, value in update_data.items():
        setattr(transcript, field, value)

    db.commit()
    db.refresh(transcript)

    return transcript

@router.delete("/{transcript_id}")
def delete_transcript(
    transcript_id: int,
    db: Session = Depends(get_db),
):
    transcript = (
        db.query(Transcript)
        .filter(Transcript.id == transcript_id)
        .first()
    )

    if not transcript:
        raise HTTPException(
            status_code=404,
            detail="Transcript not found",
        )

    db.delete(transcript)
    db.commit()

    return {
        "status": "success",
        "message": "Transcript deleted successfully",
        "transcript_id": transcript_id,
    }