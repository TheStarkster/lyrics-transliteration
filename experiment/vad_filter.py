import os
import numpy as np
import torch
import soundfile as sf
from pathlib import Path
import warnings

# Make pyannote import optional
HAS_PYANNOTE = False
try:
    from pyannote.audio import Pipeline
    HAS_PYANNOTE = True
except ImportError:
    warnings.warn("pyannote.audio not installed. VAD filtering will be skipped. To install, run: pip install pyannote.audio")

def filter_vad(input_audio_path, output_audio_path=None):
    """
    Apply voice activity detection to filter out non-speech segments
    
    Args:
        input_audio_path (str): Path to input audio file
        output_audio_path (str, optional): Path to save filtered audio. If None, will create one based on input
        
    Returns:
        str: Path to the filtered audio file
    """
    print(f"Applying VAD filtering to {input_audio_path}")
    
    # Ensure input path exists
    if not os.path.exists(input_audio_path):
        raise FileNotFoundError(f"Input audio file not found: {input_audio_path}")
    
    # Generate output path if not provided
    if output_audio_path is None:
        input_path = Path(input_audio_path)
        output_audio_path = str(input_path.parent / f"{input_path.stem}_speech_only.wav")
    
    # If pyannote is not installed, return the original file with a warning
    if not HAS_PYANNOTE:
        print("⚠️ pyannote.audio not installed. Skipping VAD filtering.")
        print("To install pyannote.audio, run:")
        print("pip install pyannote.audio")
        print("pip install git+https://github.com/pyannote/pyannote-audio.git@main")
        print("You may also need to accept terms and get a token from: https://huggingface.co/pyannote/voice-activity-detection")
        return input_audio_path
    
    try:
        # Load the VAD pipeline
        vad = Pipeline.from_pretrained("pyannote/voice-activity-detection")
        
        # Load audio using soundfile
        audio, sr = sf.read(input_audio_path)
        
        # Convert to (channels, time) shape and torch tensor
        if audio.ndim == 1:
            audio = np.expand_dims(audio, axis=0)  # (1, time)
        else:
            audio = audio.T  # (channels, time)
        
        audio_tensor = torch.tensor(audio, dtype=torch.float32)
        
        # Run VAD
        speech_regions = vad({"waveform": audio_tensor, "sample_rate": sr})
        
        # Extract segments
        segments = []
        for speech in speech_regions.get_timeline().support():
            start, end = int(speech.start * sr), int(speech.end * sr)
            segments.append(audio[0][start:end])  # use audio[0] for mono
        
        # Check if we have any speech segments
        if not segments:
            print("No speech segments detected in the audio")
            return input_audio_path  # Return original file if no speech segments
        
        # Save the result
        sf.write(output_audio_path, np.concatenate(segments), sr)
        
        print(f"VAD filtering complete, saved to {output_audio_path}")
        return output_audio_path
        
    except Exception as e:
        print(f"Error in VAD filtering: {e}")
        return input_audio_path  # Return original file on error