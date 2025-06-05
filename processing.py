import os
import subprocess
import whisper
from pathlib import Path

model = whisper.load_model("large-v3")

def separate_vocals(input_path: str, output_dir: str):
    cmd = [
        "demucs",
        "--two-stems", "vocals",
        "--device", "cpu",
        "-o", output_dir,
        input_path
    ]
    subprocess.run(cmd, check=True)
    song_name = Path(input_path).stem
    return os.path.join(output_dir, "htdemucs", song_name, "vocals.wav")

def transcribe_audio(audio_path: str, language="Telugu", return_segments=False):
    result = model.transcribe(audio_path, language=language, verbose=True, task="transcribe")
    if return_segments:
        return {
            "text": result["text"],
            "segments": result["segments"]
        }
    return result["text"]
