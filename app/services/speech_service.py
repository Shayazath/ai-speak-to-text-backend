
import logging
import time

from faster_whisper import WhisperModel

model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8",
    cpu_threads=8,
    num_workers=1,
)


def transcribe_audio(audio_path: str) -> dict:
    """Transcribe an audio file and return text, language, duration, and timing."""
    logging.warning("DEBUG: transcribe_audio() was called")
    started_at = time.perf_counter()
    logging.info("Starting Whisper transcription: %s", audio_path)

    segments, info = model.transcribe(
        audio_path,
        task="transcribe",
        language=None,
        beam_size=3,
        temperature=0.0,
        vad_filter=True,
        condition_on_previous_text=False,
        no_speech_threshold=0.6,
        compression_ratio_threshold=2.4,
        log_prob_threshold=-1.0,
    )
    # Whisper transcription is lazy; consume segments before measuring time.
    segments = list(segments)
    print("DEBUG: Whisper segments finished", flush=True)

    logging.warning(
        "DEBUG: Transcription segments=%d, language=%s",
        len(segments),
        info.language,
    )

    transcript_text = " ".join(
        segment.text.strip()
        for segment in segments
        if segment.text.strip()
    ).strip()

    inference_seconds = round(time.perf_counter() - started_at, 2)
    duration_seconds = round(info.duration, 2)

    # logging.info(
    #     "File transcription completed: audio=%.2fs, inference=%.2fs, "
    #     "language=%s, probability=%.2f, characters=%d",
    #     duration_seconds,
    #     inference_seconds,
    #     info.language,
    #     info.language_probability,
    #     len(transcript_text),
    # )
    print(
    f"File transcription completed: "
    f"audio={duration_seconds:.2f}s, "
    f"inference={inference_seconds:.2f}s, "
    f"language={info.language}, "
    f"probability={info.language_probability:.2f}, "
    f"characters={len(transcript_text)}",
    flush=True,
    )
    print("DEBUG: Returning transcription result", flush=True)

    return {
        "text": transcript_text,
        "language": info.language,
        "duration_seconds": round(info.duration),
    }
