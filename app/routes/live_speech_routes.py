
import asyncio
import array
import logging
import os
import tempfile
import wave
from collections import deque

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.live_speech_service import transcribe_audio_chunk

router = APIRouter(tags=["Live Transcription"])

SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2
MAX_AUDIO_BYTES = 5 * 1024 * 1024

WINDOW_SECONDS = 4
UPDATE_SECONDS = 1

WINDOW_SAMPLES = SAMPLE_RATE * WINDOW_SECONDS
UPDATE_SAMPLES = SAMPLE_RATE * UPDATE_SECONDS
MAX_BUFFER_SAMPLES = SAMPLE_RATE * 30


async def safe_send_json(websocket: WebSocket, data: dict) -> bool:
    """Return False if the client is no longer connected."""
    try:
        await websocket.send_json(data)
        return True
    except (WebSocketDisconnect, RuntimeError, OSError):
        return False


@router.websocket("/ws/transcribe")
async def live_transcription(websocket: WebSocket):
    await websocket.accept()

    # Store signed 16-bit PCM samples.
    audio_buffer = deque(maxlen=MAX_BUFFER_SAMPLES)
    samples_since_update = 0
    total_samples = 0

    async def transcribe_window(samples: list[int]) -> dict:
        temp_path = None

        try:
            pcm = array.array("h", samples)

            # WAV PCM data is little-endian.
            if os.sys.byteorder != "little":
                pcm.byteswap()

            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as temp_file:
                temp_path = temp_file.name

            with wave.open(temp_path, "wb") as wav_file:
                wav_file.setnchannels(CHANNELS)
                wav_file.setsampwidth(SAMPLE_WIDTH)
                wav_file.setframerate(SAMPLE_RATE)
                wav_file.writeframes(pcm.tobytes())

            return await asyncio.to_thread(
                transcribe_audio_chunk, temp_path
            )
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    logging.warning("Could not remove temporary WAV file")

    try:
        while True:
            message = await websocket.receive()

            if message["type"] == "websocket.disconnect":
                break

            audio_bytes = message.get("bytes")

            if not audio_bytes:
                continue

            if len(audio_bytes) > MAX_AUDIO_BYTES:
                if not await safe_send_json(websocket, {
                    "type": "error",
                    "message": "Audio frame exceeds the size limit.",
                }):
                    break
                continue

            if len(audio_bytes) % SAMPLE_WIDTH != 0:
                if not await safe_send_json(websocket, {
                    "type": "error",
                    "message": "Invalid PCM audio frame.",
                }):
                    break
                continue

            pcm = array.array("h")
            pcm.frombytes(audio_bytes)

            if os.sys.byteorder != "little":
                pcm.byteswap()

            audio_buffer.extend(pcm)
            total_samples += len(pcm)
            samples_since_update += len(pcm)

            if (
                len(audio_buffer) < WINDOW_SAMPLES
                or samples_since_update < UPDATE_SAMPLES
            ):
                continue

            # Keep only the latest window for this inference.
            samples_since_update = 0
            window = list(audio_buffer)[-WINDOW_SAMPLES:]

            try:
                result = await transcribe_window(window)

                window_end_seconds = total_samples / SAMPLE_RATE

                sent = await safe_send_json(websocket, {
                    "type": "transcript",
                    "text": result.get("text", ""),
                    "language": result.get("language"),
                    "language_probability": result.get(
                        "language_probability"
                    ),
                    "window_start_seconds": round(
                        max(0, window_end_seconds - WINDOW_SECONDS), 2
                    ),
                    "window_end_seconds": round(window_end_seconds, 2),
                })

                if not sent:
                    break

            except (WebSocketDisconnect, RuntimeError, OSError):
                logging.info("Live transcription client disconnected.")
                break

            except Exception:
                logging.exception("Live transcription failed")

                if not await safe_send_json(websocket, {
                    "type": "error",
                    "message": "Could not transcribe the audio window.",
                }):
                    break

    except WebSocketDisconnect:
        logging.info("Live transcription client disconnected.")

    except Exception:
        logging.exception("Unexpected live WebSocket error")

    finally:
        logging.info("Live transcription connection finished.")
