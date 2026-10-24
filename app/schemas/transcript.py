from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TranscriptCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    language: str | None = Field(default=None, max_length=50)
    duration_seconds: int | None = Field(default=None, ge=0)


class TranscriptUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, min_length=1)


class TranscriptResponse(BaseModel):
    id: int
    title: str
    content: str
    language: str | None
    duration_seconds: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)