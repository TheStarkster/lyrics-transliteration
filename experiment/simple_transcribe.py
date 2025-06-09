import argparse
import whisper
import os
import torch
from datetime import timedelta

def format_timestamp(seconds):
    """Convert seconds to a formatted timestamp string (HH:MM:SS.mmm)"""
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

def transcribe(audio_path, model_name="large-v3", language="hi", beam_size=20):
    """
    Transcribe audio using Whisper model
    
    Parameters:
    - audio_path: Path to the audio file
    - model_name: Whisper model name (tiny, base, small, medium, large-v3)
    - language: Language code ('hi' for Hindi, 'te' for Telugu)
    - beam_size: Beam size for the decoding algorithm (higher = more accurate but slower)
    
    Returns:
    - Dictionary with transcription text and segments
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model(model_name, device=device)
    
    # Map language codes to Whisper language codes if needed
    language_map = {
        "hi": "hi",
        "te": "te",
        # Add more mappings if needed
    }
    
    # Use the mapped language or fallback to the original
    whisper_language = language_map.get(language, language)
    
    # Enhanced parameters for better accuracy
    result = model.transcribe(
        audio_path, 
        language=whisper_language,
        task="transcribe",
        word_timestamps=False,
        verbose=True,
        beam_size=beam_size,
        temperature=0.0,  # Lower temperature for more focused sampling
        best_of=5,        # Consider more candidates
        fp16=False        # Disable fp16 for higher precision
    )
    
    # Return both the full text and the segments with timestamps
    return {
        "text": result["text"].strip(),
        "segments": result["segments"]
    }

def main():
    parser = argparse.ArgumentParser(description="Transcribe Hindi audio using Whisper large-v3")
    parser.add_argument("audio", help="Path to input .wav file")
    parser.add_argument("--model", default="large-v3", help="Model to use (tiny, base, small, medium, large-v3)")
    parser.add_argument("--language", default="hi", help="Language code (e.g., 'hi' for Hindi)")
    args = parser.parse_args()

    if not os.path.isfile(args.audio):
        print(f"Error: File not found: {args.audio}")
        return

    print(f"Transcribing with model {args.model}...")
    result = transcribe(args.audio, model_name=args.model, language=args.language)
    
    print("\n====== TRANSCRIPTION ======\n")
    print(result["text"])
    
    print("\n====== TRANSCRIPTION WITH TIMESTAMPS ======\n")
    for segment in result["segments"]:
        start = format_timestamp(segment["start"])
        end = format_timestamp(segment["end"])
        text = segment["text"].strip()
        print(f"[{start} --> {end}] {text}")

if __name__ == "__main__":
    main()
