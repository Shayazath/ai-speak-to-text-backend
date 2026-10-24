from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.routes.transcript_routes import router as transcript_router
from app.routes.speech_routes import router as speech_router
from app.routes.live_speech_routes import router as live_speech_router
from fastapi.middleware.cors import CORSMiddleware

from app.database import get_db

app = FastAPI(
    title="AI Speak-to-Text API",
    description="Real-time multilingual speech transcription service",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://ai-speak-to-text-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "status": "success",
        "message": "AI Speak-to-Text API is running",
    }


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "success",
            "message": "Backend and database are connected",
        }
    except Exception as exc:
        print(f"Database health check failed: {exc}")
        from fastapi import HTTPException

        raise HTTPException(
            status_code=503,
            detail="Database connection failed",
        )

app.include_router(transcript_router)
app.include_router(speech_router)
app.include_router(live_speech_router)