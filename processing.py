#!/usr/bin/env python3
"""
Whisper large-v3 - high-accuracy, CPU-friendly, project-compatible
"""

# ─── Imports & helpers (identical to previous) ─────────────────────────────
import os, random, subprocess, json, argparse, textwrap, time, sys, logging
from pathlib import Path
import numpy as np, torch, whisper, requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'processing.log'))
    ]
)
logger = logging.getLogger('lyrics-processor')

# Global dummy mode flag
DUMMY_MODE = False

# Dummy data for testing
DUMMY_TRANSCRIPTION = {
    "text": " दुनिया वेद मेरी सब कुछ मेरा जो मेरा नहीं है वो भी मेरा दुनिया मेरी सब कुछ मेरा जो मेरा नहीं है वो भी मेरा चलू अपनी ही दुन में करू है जो मन में गलत को सही में बनाता चाहे ऐसा हो ऐसा हो कैसे भी पैसा तो मुझे को बोल रे सारी दौलत शौरत इस्जत ताखत मेरे ही पास है जाना है कौन यहां जो मुझे को रोके अपने इन सपनों के नाते तोडेंगे सब रिष्टे नाते पालूंगा जो मेरा सपना है चंदा से सूरज से आगे दुनिया को आँखे दिखला के पाऊंगा जो मुझे को पाना है कमाना है कमाना है आगे दुनिया को आँखे दिखला के पाऊंगा जो मुझे को पाना है आगे दुनिया को आँखे दिखला के पाऊंगा जो मुझे को पाना है आगे दुनिया को आँखे दिखला के पाऊंगा जो मुझे को पाना है आगे दुनिया को आँखे दिखला के पाऊंगा जो मुझे को पाऊंगा जो मुझे को पाऊंगा जो मुझे को पाऊंगा जो सबका सपना है वो अपना है वो अपना है",
    "segments": [
        {
            "id": 0,
            "start": 28.28,
            "end": 29.98,
            "text": " दुनिया वेद"
        },
        {
            "id": 1,
            "start": 29.98,
            "end": 40.72,
            "text": " मेरी सब कुछ मेरा जो मेरा नहीं है वो भी मेरा"
        },
        {
            "id": 2,
            "start": 40.72,
            "end": 52.82,
            "text": " दुनिया मेरी सब कुछ मेरा जो मेरा नहीं है वो भी मेरा"
        },
        {
            "id": 3,
            "start": 52.82,
            "end": 59.08,
            "text": " चलू अपनी ही दुन में करू है जो मन में गलत को सही में बनाता"
        },
        {
            "id": 4,
            "start": 59.08,
            "end": 64.7,
            "text": " चाहे ऐसा हो ऐसा हो कैसे भी पैसा तो मुझे को बोल रे"
        },
        {
            "id": 5,
            "start": 64.7,
            "end": 71.08,
            "text": " सारी दौलत शौरत इस्जत ताखत मेरे ही पास है जाना"
        },
        {
            "id": 6,
            "start": 71.08,
            "end": 78.84,
            "text": " है कौन यहां जो मुझे को रोके अपने इन सपनों के नाते तोडेंगे"
        },
        {
            "id": 7,
            "start": 78.84,
            "end": 84.6,
            "text": " सब रिष्टे नाते पालूंगा जो मेरा सपना है"
        },
        {
            "id": 8,
            "start": 86.16,
            "end": 89.06,
            "text": " चंदा से सूरज से"
        },
        {
            "id": 9,
            "start": 89.08,
            "end": 96.24,
            "text": " आगे दुनिया को आँखे दिखला के पाऊंगा जो मुझे को पाना है"
        },
        {
            "id": 10,
            "start": 96.24,
            "end": 99.8,
            "text": " कमाना है"
        },
        {
            "id": 11,
            "start": 103.32000000000001,
            "end": 105.72,
            "text": " कमाना है"
        },
        {
            "id": 12,
            "start": 130.32,
            "end": 143.04,
            "text": " आगे दुनिया को आँखे दिखला के पाऊंगा जो मुझे को पाना है"
        },
        {
            "id": 13,
            "start": 143.04,
            "end": 149.06,
            "text": " आगे दुनिया को आँखे दिखला के पाऊंगा जो मुझे को पाना है"
        },
        {
            "id": 14,
            "start": 162.16,
            "end": 177.8,
            "text": " आगे दुनिया को आँखे दिखला के पाऊंगा जो मुझे को पाना है"
        },
        {
            "id": 15,
            "start": 186.94,
            "end": 207.72,
            "text": " आगे दुनिया को आँखे दिखला के पाऊंगा जो मुझे को पाऊंगा जो मुझे को पाऊंगा जो मुझे को पाऊंगा"
        },
        {
            "id": 16,
            "start": 207.72,
            "end": 220.04,
            "text": " जो सबका सपना है वो अपना है वो अपना है"
        }
    ]
}

def set_seed(seed:int=42):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    try:
        torch.use_deterministic_algorithms(True)
    except Exception as e:
        logger.warning(f"Could not set deterministic algorithms: {e}")
    if torch.backends.cudnn.is_available():
        torch.backends.cudnn.deterministic=True; torch.backends.cudnn.benchmark=False

# Initialize with error handling
try:
    set_seed(42)
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {DEVICE}")
    model = whisper.load_model("large-v3", device=DEVICE)
    logger.info("Whisper model loaded successfully")
except Exception as e:
    logger.error(f"Failed to initialize Whisper model: {e}")
    model = None

AZURE_OPENAI_ENDPOINT = (
    "https://scout-llm-2.openai.azure.com/"
    "openai/deployments/gpt-4o/chat/completions?api-version=2024-02-15-preview"
)
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "c1b98148632f4133a5f5aa1146f640ed")

def get_absolute_path(path):
    """Convert relative paths to absolute, handle tilde expansion"""
    if not path:
        return path
    return os.path.abspath(os.path.expanduser(path))

def separate_vocals(input_path:str, output_dir:str="demucs_out")->str:
    input_path = get_absolute_path(input_path)
    output_dir = get_absolute_path(output_dir)
    
    logger.info(f"Separating vocals from: {input_path} to {output_dir}")
    
    if DUMMY_MODE:
        logger.info("DUMMY MODE: Simulating vocal separation...")
        time.sleep(3)  # Simulate 3 seconds of processing
        song=Path(input_path).stem
        return os.path.join(output_dir,"htdemucs",song,"vocals.wav")
    
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        cmd=["demucs","--two-stems","vocals","--device","cpu","-o",output_dir,input_path]
        logger.info(f"Running command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        song=Path(input_path).stem
        output_path = os.path.join(output_dir,"htdemucs",song,"vocals.wav")
        
        if not os.path.exists(output_path):
            logger.error(f"Vocals extraction completed but output file not found: {output_path}")
            return None
            
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Vocal separation failed: {e}")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Error in vocal separation: {e}")
        return None

def get_english_transliteration(text:str, lang:str)->str:
    if not text or not text.strip():
        return ""  # Return empty string for empty input
    
    logger.info(f"Getting transliteration for {len(text)} chars of {lang} text")
    
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_KEY
    }
    
    prompt = (f"Transliterate the following {lang} text to English "
            f"(use Latin characters only):\n\n{text}")
            
    payload = {
        "messages": [
            {"role": "system", "content": "You are a transliteration expert."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0,
        "top_p": 1,
        "max_tokens": 4000
    }
    
    try:
        r = requests.post(
            AZURE_OPENAI_ENDPOINT,
            headers=headers,
            json=payload
        )
        r.raise_for_status()
        result = r.json()["choices"][0]["message"]["content"].strip()
        logger.info(f"Transliteration successful: {len(result)} chars")
        return result
    except Exception as e:
        logger.error(f"❌ Transliteration error: {e}")
        if hasattr(r, 'text'):
            logger.error(f"Response text: {r.text}")
        return f"Transliteration failed: {e}"

def is_valid_audio_file(file_path: str) -> bool:
    """Check if file exists and is a valid audio file."""
    file_path = get_absolute_path(file_path)
    
    if not os.path.exists(file_path):
        logger.error(f"❌ Error: Audio file not found: {file_path}")
        return False
    
    # Check if file has content (not empty)
    try:
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            logger.error(f"❌ Error: Audio file is empty: {file_path}")
            return False
            
        logger.info(f"Audio file size: {file_size} bytes")
    except Exception as e:
        logger.error(f"❌ Error checking file size: {e}")
        return False
    
    # Check file permissions
    try:
        if not os.access(file_path, os.R_OK):
            logger.error(f"❌ Error: No read permission for file: {file_path}")
            return False
    except Exception as e:
        logger.error(f"❌ Error checking file permissions: {e}")
        return False
    
    # Check file extension
    valid_extensions = ['.mp3', '.wav', '.flac', '.ogg', '.m4a']
    if not any(file_path.lower().endswith(ext) for ext in valid_extensions):
        logger.warning(f"❌ Warning: File may not be an audio file: {file_path}")
    
    logger.info(f"Audio file validation passed for: {file_path}")
    return True

def transcribe_audio(
    audio_path: str,
    language: str = "Telugu",
    return_segments: bool = False,
    *,
    initial_prompt: str | None = None
) -> dict:
    """
    High-accuracy, deterministic transcription + transliteration.
    Signature is identical to your original codebase.
    """
    audio_path = get_absolute_path(audio_path)
    logger.info(f"Transcribing audio: {audio_path}, language: {language}")
    
    # Check if model was loaded successfully
    if model is None:
        error_msg = "Whisper model was not initialized properly"
        logger.error(f"❌ {error_msg}")
        return {
            "text": error_msg,
            "transliteration": error_msg,
            "segments": [] if return_segments else None
        }
    
    # Validate audio file before processing
    if not is_valid_audio_file(audio_path):
        error_msg = f"Invalid or missing audio file: {audio_path}"
        logger.error(f"❌ {error_msg}")
        return {
            "text": error_msg,
            "transliteration": error_msg,
            "segments": [] if return_segments else None
        }
    
    if DUMMY_MODE:
        logger.info("Using dummy transcription mode")
        result = DUMMY_TRANSCRIPTION.copy()
        # Always use real transliteration service even in dummy mode
        transliteration = get_english_transliteration(result["text"], language)
        
        if not return_segments:
            return {"text": result["text"], "transliteration": transliteration}
            
        segments_out = []
        for seg in result["segments"]:
            seg_text = seg["text"]
            # Use real transliteration for each segment
            segments_out.append({
                "id": seg["id"],
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
                "transliteration": get_english_transliteration(seg_text, language)
            })
            
        return {
            "text": result["text"],
            "transliteration": transliteration,
            "segments": segments_out
        }
    
    decode_opts = dict(
        language                     = language,
        task                         = "transcribe",
        beam_size                    = 20,    # wide beam for best accuracy
        patience                     = 1.2,
        temperature                  = 0.0,   # deterministic
        condition_on_previous_text   = True,
        word_timestamps              = True,  # safe in openai-whisper ≥2023-12
        initial_prompt               = initial_prompt,
        best_of                      = 1,
        fp16                         = False, # CPU-friendly
        verbose                      = True
    )

    try:
        logger.info(f"Starting transcription with options: {decode_opts}")
        result = model.transcribe(audio_path, **decode_opts)
        
        logger.info(f"Transcription successful, text length: {len(result['text'])}")
        
        transliteration = get_english_transliteration(result["text"], language)

        if not return_segments:
            return {"text": result["text"], "transliteration": transliteration}

        segments_out = []
        for seg in result["segments"]:
            segments_out.append({
                "id": seg["id"],
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
                "transliteration": get_english_transliteration(seg["text"], language),
            })
        
        logger.info(f"Processed {len(segments_out)} segments")

        return {
            "text": result["text"],
            "transliteration": transliteration,
            "segments": segments_out,
        }
    except torch.cuda.OutOfMemoryError:
        error_msg = "CUDA out of memory error. Try using CPU instead."
        logger.error(f"❌ {error_msg}")
        return {
            "text": error_msg,
            "transliteration": error_msg,
            "segments": [] if return_segments else None
        }
    except Exception as e:
        error_msg = f"Error transcribing audio: {str(e)}"
        logger.error(f"❌ {error_msg}")
        logger.exception("Detailed exception info:")
        return {
            "text": error_msg,
            "transliteration": error_msg,
            "segments": [] if return_segments else None
        }

# ─── Optional CLI driver for quick testing (unchanged) ─────────────────────
def main():
    p=argparse.ArgumentParser(description="High-accuracy Whisper transcription")
    p.add_argument("audio"); p.add_argument("--language",default="Telugu")
    p.add_argument("--prompt",dest="initial_prompt"); p.add_argument("--segments",action="store_true")
    p.add_argument("--separate-vocals",action="store_true")
    p.add_argument("--dummy",action="store_true",help="Run in dummy mode with predefined results")
    args=p.parse_args()
    
    global DUMMY_MODE
    DUMMY_MODE = args.dummy

    logger.info(f"Processing audio: {args.audio}, language: {args.language}, dummy: {args.dummy}")

    target=args.audio
    if args.separate_vocals:
        logger.info("Separating vocals before transcription")
        separated_path = separate_vocals(args.audio)
        if separated_path:
            target = separated_path
        else:
            logger.error("Vocal separation failed, using original audio")

    out=transcribe_audio(target,args.language,args.segments,initial_prompt=args.initial_prompt)

    print("\n====== TRANSCRIPTION ======\n",out["text"])
    print("\n====== TRANSLITERATION ====\n",out["transliteration"])
    if args.segments and "segments" in out:
        print("\n====== SEGMENTS ==========\n")
        for s in out["segments"]:
            print(f"[{s['start']:7.2f}-{s['end']:7.2f}] {s['transliteration']}")

if __name__=="__main__":                # harmless when imported in your project
    main()
