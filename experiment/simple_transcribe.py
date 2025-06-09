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
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    model = whisper.load_model(model_name, device=device)
    
    if language == "te":
        result = model.transcribe(
            audio_path,
            language="te",
            task="transcribe",
            beam_size=20,  
            best_of=1,  
            temperature=0.0,
            patience=1.0,  
            fp16=True,
            word_timestamps=True,
            condition_on_previous_text=False,
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
            verbose=True
        )
    else:
        result = model.transcribe(
            audio_path,
            language="hi",
            task="transcribe",
            beam_size=20,
            best_of=1,
            temperature=0.0,
            patience=1.0,
            fp16=True,
            word_timestamps=True,
            condition_on_previous_text=True,
            compression_ratio_threshold=2.4,
            verbose=True
        )
    
    return {
        "text": result["text"].strip(),
        "segments": result["segments"]
    }