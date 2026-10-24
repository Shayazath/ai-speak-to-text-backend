
import time
from faster_whisper import WhisperModel

MODEL_SIZE = "base"
AUDIO_PATH = "save1.wav"

print(f"Loading Whisper model: {MODEL_SIZE}")
model = WhisperModel(
    MODEL_SIZE,
    device="cpu",
    compute_type="int8",
)

print(f"Transcribing: {AUDIO_PATH}")
started_at = time.perf_counter()

segments, info = model.transcribe(
    AUDIO_PATH,
    beam_size=5,
    vad_filter=True,
    condition_on_previous_text=True,
)

segments = list(segments)
elapsed = time.perf_counter() - started_at

print(f"\nDetected language: {info.language}")
print(f"Language probability: {info.language_probability:.2f}")
print(f"Audio duration: {info.duration:.2f} seconds")
print(f"Inference time: {elapsed:.2f} seconds")
print("\nTranscript:")

for segment in segments:
    print(
        f"[{segment.start:.2f}s - {segment.end:.2f}s] "
        f"{segment.text.strip()}"
    )

print("\nTranscription complete.")
