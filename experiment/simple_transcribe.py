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
    if torch.cuda.is_available():
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    torch.manual_seed(42)
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    if language == "te" and model_name != "large-v3":
        print(f"For Telugu songs, large-v3 model is recommended. Current: {model_name}")
    
    model = whisper.load_model(model_name, device=device)
    
    language_map = {
        "hi": "hi",
        "te": "te",
    }
    
    whisper_language = language_map.get(language, language)
    
    if language == "te":
        beam_size = max(beam_size, 20)  # Increased from 40 to 60
    
    base_options = {
        "language": whisper_language,
        "task": "transcribe",
        "verbose": True,
        "beam_size": beam_size,
        "temperature": 0.0,    
        "best_of": 10 if language == "te" else 1,  # Changed from 15 to 10 for Telugu
        "fp16": True,
        "word_timestamps": True,
        "patience": 2.0 if language == "te" else 1.0,  # Increased patience for Telugu
        "condition_on_previous_text": True,
    }
    
    if language == "te":
        # Telugu-specific configuration with multi-pass decoding
        result = model.transcribe(
            audio_path,
            language="te",
            task="transcribe",
            beam_size=10,  # More aggressive
            best_of=10,  # Better candidate selection
            temperature=[0.0, 0.2, 0.4, 0.6],  # Multi-pass decoding
            patience=2.0,  # Let beam search explore more
            fp16=True,
            word_timestamps=True,
            condition_on_previous_text=True,
            compression_ratio_threshold=2.8,
            logprob_threshold=-1.0,
            initial_prompt="తెలుగు పాటల లిరిక్స్",  # Domain prompt
        )
    else:
        result = model.transcribe(audio_path, **base_options)
    
    return {
        "text": result["text"].strip(),
        "segments": result["segments"]
    }