import logging
import time

from app.services.speech_service import model


def transcribe_audio_chunk(audio_path: str) -> dict:
    started_at = time.perf_counter()

    segments, info = model.transcribe(
        audio_path,
        task="transcribe",
        language=None,
        beam_size=3,
        best_of=3,
        temperature=0.0,
        vad_filter=True,
        vad_parameters={
            "min_silence_duration_ms": 500,
            "speech_pad_ms": 200,
        },
        condition_on_previous_text=False,
        no_speech_threshold=0.6,
        compression_ratio_threshold=2.4,
        log_prob_threshold=-0.8,
    )

    segments = list(segments)

    # Ignore segments that Whisper identifies as silence.
    valid_segments = [
        segment
        for segment in segments
        if segment.text.strip()
        and segment.no_speech_prob < 0.6
    ]

    text = " ".join(
        segment.text.strip()
        for segment in valid_segments
    ).strip()

    elapsed_seconds = round(time.perf_counter() - started_at, 2)

    logging.info(
        "Live transcription completed: duration=%.2fs, "
        "inference=%.2fs, language=%s, characters=%d",
        info.duration,
        elapsed_seconds,
        info.language,
        len(text),
    )

    return {
        "text": text,
        "language": info.language,
        "language_probability": info.language_probability,
        "audio_duration_seconds": round(info.duration, 2),
        "inference_seconds": elapsed_seconds,
    }