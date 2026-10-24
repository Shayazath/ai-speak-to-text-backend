
from pydub import AudioSegment

audio = AudioSegment.from_file(
    r"C:\Users\gowth\OneDrive\Documents\Sound Recordings\check.m4a",
    format="m4a",
)

audio = audio.set_channels(1).set_frame_rate(16000)

audio.export("sample3.wav", format="wav")

print("Audio converted successfully: sample.wav")
