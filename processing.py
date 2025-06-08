#!/usr/bin/env python3
"""
OpenAI Whisper with large-v3 model - accurate transcription for multilingual audio
"""

# ─── Imports & helpers (identical to previous) ─────────────────────────────
import os, random, subprocess, json, argparse, textwrap, time, sys, logging
from pathlib import Path
import numpy as np, torch, requests
import whisper
import warnings

# Suppress NVML initialization warning
warnings.filterwarnings("ignore", message="Can't initialize NVML")

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

def set_seed(seed:int=42):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    try:
        # Set CUBLAS workspace config for deterministic behavior with CUDA 10.2+
        os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
        torch.use_deterministic_algorithms(True)
    except Exception as e:
        logger.warning(f"Could not set deterministic algorithms: {e}")
    if torch.backends.cudnn.is_available():
        torch.backends.cudnn.deterministic=True; torch.backends.cudnn.benchmark=False
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

# Dictionary to store loaded models
models = {}

# Initialize with error handling
try:
    set_seed(42)
    # Always prefer CUDA and log warning if not available
    if not torch.cuda.is_available():
        logger.warning("CUDA not available! Using CPU instead, which will be significantly slower.")
        DEVICE = "cpu"
    else:
        DEVICE = "cuda"
        logger.info(f"Using CUDA: {torch.cuda.get_device_name(0)}")
    
    # Load the default model (large-v3) initially
    models["large-v3"] = whisper.load_model("large-v3", device=DEVICE)
    logger.info(f"Whisper large-v3 model loaded successfully")
except Exception as e:
    logger.error(f"Failed to initialize Whisper model: {e}")
    models = {}

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
    
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Use CUDA for demucs if available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        cmd=["demucs","--two-stems","vocals","--device",device,"-o",output_dir,input_path]
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
    """
    Single efficient call to transliterate text with robust fallback.
    """
    if not text or not text.strip():
        return ""  # Return empty string for empty input
    
    # Map ISO language codes to full names for prompting
    lang_map = {"te": "Telugu", "hi": "Hindi"}
    lang_name = lang_map.get(lang, lang)
    
    logger.info(f"Getting transliteration for {len(text)} chars of {lang_name} text")
    
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_KEY
    }
    
    # Direct, to-the-point system prompt
    system_prompt = "You are a transliteration tool that converts text between writing systems, preserving pronunciation."
    
    # Simplest, most direct user prompt
    user_prompt = f"Transliterate this {lang_name} text to Latin alphabet: {text}"
    
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0,
        "top_p": 1,
        "max_tokens": 4000
    }
    
    try:
        r = requests.post(
            AZURE_OPENAI_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if r.status_code == 200 and "choices" in r.json() and r.json()["choices"][0].get("message", {}).get("content"):
            result = r.json()["choices"][0]["message"]["content"].strip()
            logger.info(f"Transliteration successful: {len(result)} chars")
            return result
            
        # If we get here, something went wrong with the API call
        logger.warning(f"API request unsuccessful, using fallback transliteration")
    except Exception as e:
        logger.error(f"❌ Transliteration error: {e}")
        if 'r' in locals() and hasattr(r, 'text'):
            logger.error(f"Response text: {r.text[:200]}...")
    
    # Use fallback if API fails
    return _fallback_transliteration(text, lang)

def _fallback_transliteration(text: str, lang: str) -> str:
    """
    Local fallback transliteration when API calls fail.
    Implements a basic character mapping for common Indic scripts.
    """
    logger.info(f"Using fallback transliteration for {lang}")
    
    # Common character mappings for Hindi (Devanagari script)
    if lang in ["hi", "Hindi"]:
        # Enhanced Devanagari to Latin mapping
        devanagari_map = {
            # Vowels
            'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo',
            'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au', 'ऑ': 'o',
            # Consonants
            'क': 'ka', 'ख': 'kha', 'ग': 'ga', 'घ': 'gha', 'ङ': 'nga',
            'च': 'cha', 'छ': 'chha', 'ज': 'ja', 'झ': 'jha', 'ञ': 'nya',
            'ट': 'ta', 'ठ': 'tha', 'ड': 'da', 'ढ': 'dha', 'ण': 'na',
            'त': 'ta', 'थ': 'tha', 'द': 'da', 'ध': 'dha', 'न': 'na',
            'प': 'pa', 'फ': 'pha', 'ब': 'ba', 'भ': 'bha', 'म': 'ma',
            'य': 'ya', 'र': 'ra', 'ल': 'la', 'व': 'va', 'श': 'sha',
            'ष': 'sha', 'स': 'sa', 'ह': 'ha', 'क्ष': 'ksha', 'त्र': 'tra', 'ज्ञ': 'gya',
            # Matras (vowel signs)
            'ा': 'a', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo',
            'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au', 'ॉ': 'o',
            # Others
            'ं': 'n', 'ँ': 'n', 'ः': 'h', '्': '', 'ऋ': 'ri',
            '़': '', 'ॅ': 'e', 'ॐ': 'om', 'ृ': 'ri', 'ॄ': 'r',
            # Numbers
            '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
            '५': '5', '६': '6', '७': '7', '८': '8', '९': '9',
            # Common Conjuncts
            'क्क': 'kka', 'क्ख': 'kkha', 'क्त': 'kta', 'क्र': 'kra', 'क्ल': 'kla', 'क्व': 'kva', 'क्श': 'ksha',
            'ख्र': 'khra', 'ग्र': 'gra', 'ग्ल': 'gla', 'घ्र': 'ghra', 'ङ्क': 'nka', 'ङ्ख': 'nkha', 'ङ्ग': 'nga',
            'ङ्घ': 'ngha', 'च्च': 'chcha', 'च्छ': 'chchha', 'च्र': 'chra', 'छ्र': 'chhra', 'ज्ज': 'jja',
            'ज्झ': 'jjha', 'ज्ञ': 'gya', 'ज्र': 'jra', 'ज्व': 'jva', 'झ्र': 'jhra', 'ञ्च': 'ncha',
            'ञ्छ': 'nchha', 'ञ्ज': 'nja', 'ञ्झ': 'njha', 'ट्ट': 'tta', 'ट्ठ': 'ttha', 'ड्ड': 'dda',
            'ड्ढ': 'ddha', 'ण्ट': 'nta', 'ण्ठ': 'ntha', 'ण्ड': 'nda', 'ण्ढ': 'ndha', 'त्त': 'tta',
            'त्थ': 'ttha', 'त्न': 'tna', 'त्र': 'tra', 'त्व': 'tva', 'थ्र': 'thra', 'द्द': 'dda',
            'द्ध': 'ddha', 'द्न': 'dna', 'द्र': 'dra', 'द्व': 'dva', 'ध्र': 'dhra', 'ध्व': 'dhva',
            'न्न': 'nna', 'न्र': 'nra', 'प्त': 'pta', 'प्र': 'pra', 'प्ल': 'pla', 'फ्र': 'phra',
            'ब्र': 'bra', 'ब्ल': 'bla', 'भ्र': 'bhra', 'म्र': 'mra', 'म्ल': 'mla', 'य्र': 'yra',
            'र्क': 'rka', 'र्ट': 'rta', 'र्थ': 'rtha', 'र्द': 'rda', 'र्श': 'rsha', 'र्ष': 'rsha',
            'र्स': 'rsa', 'ल्क': 'lka', 'ल्ल': 'lla', 'व्र': 'vra', 'व्ल': 'vla', 'श्र': 'shra',
            'श्ल': 'shla', 'श्व': 'shva', 'ष्ट': 'shta', 'ष्ठ': 'shtha', 'स्त': 'sta', 'स्थ': 'stha',
            'स्न': 'sna', 'स्र': 'sra', 'स्व': 'sva', 'ह्न': 'hna', 'ह्र': 'hra', 'ह्ल': 'hla',
            'ह्व': 'hva', 'द्य': 'dya', 'क्य': 'kya', 'ह्य': 'hya', 'न्त': 'nta', 'न्द': 'nda',
            # Punctuation
            '।': '.', '॥': '.', ' ': ' ', ',': ',', '?': '?', '!': '!',
            '"': '"', "'": "'", '(': '(', ')': ')', '[': '[', ']': ']',
            '{': '{', '}': '}', '-': '-', '_': '_', '=': '=', '+': '+',
            '&': '&', '%': '%', '$': '$', '#': '#', '@': '@', '*': '*',
            ';': ';', ':': ':', '/': '/', '\\': '\\', '|': '|', '<': '<', '>': '>',
        }
        
        # Simple transliteration with handling of common conjuncts
        result = ""
        i = 0
        while i < len(text):
            # Try 3-character conjuncts
            if i < len(text) - 2 and text[i:i+3] in devanagari_map:
                result += devanagari_map[text[i:i+3]]
                i += 3
            # Try 2-character conjuncts
            elif i < len(text) - 1 and text[i:i+2] in devanagari_map:
                result += devanagari_map[text[i:i+2]]
                i += 2
            # Single character
            elif i < len(text) and text[i] in devanagari_map:
                result += devanagari_map[text[i]]
                i += 1
            # Unknown character - pass through
            else:
                result += text[i]
                i += 1
        
        return result
    
    # Basic Telugu to Latin mapping
    elif lang in ["te", "Telugu"]:
        # Enhanced Telugu mapping
        telugu_map = {
            # Vowels
            'అ': 'a', 'ఆ': 'aa', 'ఇ': 'i', 'ఈ': 'ee', 'ఉ': 'u', 'ఊ': 'oo',
            'ఋ': 'ru', 'ౠ': 'ruu', 'ఎ': 'e', 'ఏ': 'e', 'ఐ': 'ai', 
            'ఒ': 'o', 'ఓ': 'o', 'ఔ': 'au', 'ఌ': 'lu', 'ౡ': 'luu',
            # Consonants
            'క': 'ka', 'ఖ': 'kha', 'గ': 'ga', 'ఘ': 'gha', 'ఙ': 'nga',
            'చ': 'cha', 'ఛ': 'chha', 'జ': 'ja', 'ఝ': 'jha', 'ఞ': 'nya',
            'ట': 'ta', 'ఠ': 'tha', 'డ': 'da', 'ఢ': 'dha', 'ణ': 'na',
            'త': 'ta', 'థ': 'tha', 'ద': 'da', 'ధ': 'dha', 'న': 'na',
            'ప': 'pa', 'ఫ': 'pha', 'బ': 'ba', 'భ': 'bha', 'మ': 'ma',
            'య': 'ya', 'ర': 'ra', 'ల': 'la', 'వ': 'va', 'శ': 'sha',
            'ష': 'sha', 'స': 'sa', 'హ': 'ha', 'ళ': 'la', 'క్ష': 'ksha',
            'ఱ': 'ra',
            # Matras (vowel signs)
            'ా': 'a', 'ి': 'i', 'ీ': 'ee', 'ు': 'u', 'ూ': 'oo',
            'ృ': 'ru', 'ౄ': 'ruu', 'ె': 'e', 'ే': 'e', 'ై': 'ai',
            'ొ': 'o', 'ో': 'o', 'ౌ': 'au', 'ౢ': 'lu', 'ౣ': 'luu',
            # Others
            'ం': 'm', 'ః': 'h', '్': '', 
            # Common Telugu Conjuncts
            'క్క': 'kka', 'క్ర': 'kra', 'క్ల': 'kla', 'క్ష': 'ksha', 'ఖ్య': 'khya',
            'గ్గ': 'gga', 'గ్ర': 'gra', 'గ్ల': 'gla', 'ఘ్య': 'ghya', 'ఙ్క': 'nka',
            'చ్చ': 'chcha', 'చ్ఛ': 'chchha', 'జ్జ': 'jja', 'జ్ఞ': 'gna', 'ట్ట': 'tta',
            'డ్డ': 'dda', 'ణ్ణ': 'nna', 'త్త': 'tta', 'త్య': 'tya', 'త్ర': 'tra',
            'త్వ': 'tva', 'ద్ద': 'dda', 'ద్ధ': 'ddha', 'ద్య': 'dya', 'ద్వ': 'dva',
            'న్న': 'nna', 'ప్ప': 'ppa', 'ప్ర': 'pra', 'ప్ల': 'pla', 'బ్బ': 'bba',
            'మ్మ': 'mma', 'య్య': 'yya', 'ర్చ': 'rcha', 'ర్త': 'rta', 'ర్ద': 'rda',
            'ర్వ': 'rva', 'ల్ల': 'lla', 'వ్వ': 'vva', 'శ్చ': 'shcha', 'శ్ర': 'shra',
            'ష్ట': 'shta', 'ష్ఠ': 'shtha', 'స్త': 'sta', 'స్థ': 'stha', 'హ్మ': 'hma',
            # Numbers
            '౦': '0', '౧': '1', '౨': '2', '౩': '3', '౪': '4',
            '౫': '5', '౬': '6', '౭': '7', '౮': '8', '౯': '9',
            # Punctuation
            '।': '.', ' ': ' ', ',': ',', '?': '?', '!': '!',
        }
        
        # Simple transliteration with improved conjunct handling
        result = ""
        i = 0
        while i < len(text):
            # Try 3-character conjuncts
            if i < len(text) - 2 and text[i:i+3] in telugu_map:
                result += telugu_map[text[i:i+3]]
                i += 3
            # Try 2-character conjuncts
            elif i < len(text) - 1 and text[i:i+2] in telugu_map:
                result += telugu_map[text[i:i+2]]
                i += 2
            # Single character
            elif i < len(text) and text[i] in telugu_map:
                result += telugu_map[text[i]]
                i += 1
            # Unknown character - pass through
            else:
                result += text[i]
                i += 1
        
        return result
    
    # For any other language, just return the original text with a note
    return f"[Transliteration unavailable] {text}"

def batch_transliterate_segments(segments: list, lang: str) -> list:
    """
    Transliterate multiple segments at once using a single efficient API call.
    This is much more efficient than making separate calls for each segment.
    
    Args:
        segments: List of segment dictionaries with 'id', 'start', 'end', 'text'
        lang: Source language (ISO code or full name)
        
    Returns:
        List of segment dictionaries with added 'transliteration' field
    """
    if not segments or len(segments) == 0:
        return []
    
    # Map ISO language codes to full names for prompting
    lang_map = {"te": "Telugu", "hi": "Hindi"}
    lang_name = lang_map.get(lang, lang)
    
    logger.info(f"Batch transliterating {len(segments)} segments of {lang_name} text")
    
    # Create a single prompt with all segments in JSON format
    segments_data = [{"id": seg["id"], "text": seg["text"]} for seg in segments]
    
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_KEY
    }
    
    # Simple, direct system message
    system_message = "You are a transliteration tool that converts text between writing systems."
    
    # Clear, direct prompt with exact output format instructions
    prompt = (
        f"Transliterate each {lang_name} text segment to Latin alphabet. "
        f"The input is JSON with 'id' and 'text' fields. "
        f"Return a JSON object with this exact structure:\n"
        f"{{\n"
        f"  \"transliterations\": [\n"
        f"    {{ \"id\": 0, \"transliteration\": \"your transliteration here\" }},\n"
        f"    {{ \"id\": 1, \"transliteration\": \"your transliteration here\" }},\n"
        f"    ...\n"
        f"  ]\n"
        f"}}\n\n"
        f"Input segments:\n{json.dumps(segments_data, ensure_ascii=False)}"
    )
    
    payload = {
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0,
        "top_p": 1,
        "response_format": {"type": "json_object"},
        "max_tokens": 4000
    }
    
    try:
        logger.info(f"Making batch API call for {len(segments)} segments")
        r = requests.post(
            AZURE_OPENAI_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=40  # Longer timeout for batch processing
        )
        
        if r.status_code == 200 and "choices" in r.json() and r.json()["choices"][0].get("message", {}).get("content"):
            response_content = r.json()["choices"][0]["message"]["content"]
            
            # Parse the JSON response
            try:
                result = json.loads(response_content)
                if "transliterations" in result:
                    transliterations = {item["id"]: item["transliteration"] for item in result["transliterations"]}
                    
                    # Merge transliterations back into original segments
                    result_segments = []
                    for seg in segments:
                        new_seg = seg.copy()
                        new_seg["transliteration"] = transliterations.get(seg["id"], f"[Fallback] {_fallback_transliteration(seg['text'], lang)}")
                        result_segments.append(new_seg)
                        
                    logger.info(f"Batch transliteration successful for all {len(result_segments)} segments")
                    return result_segments
                else:
                    logger.error("Invalid API response format: missing 'transliterations' key")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
        
        # If we get here, API call failed
        logger.warning(f"API batch transliteration failed, using fallback for all segments")
    except Exception as e:
        logger.error(f"❌ Batch transliteration error: {e}")
        if 'r' in locals() and hasattr(r, 'text'):
            logger.error(f"Response text: {r.text[:200]}...")
    
    # If API failed, use fallback for all segments
    result_segments = []
    for seg in segments:
        new_seg = seg.copy()
        new_seg["transliteration"] = _fallback_transliteration(seg["text"], lang)
        result_segments.append(new_seg)
    
    return result_segments

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

def load_model(model_name: str):
    """Load a Whisper model if not already loaded"""
    if model_name in models and models[model_name] is not None:
        return models[model_name]
    
    try:
        logger.info(f"Loading Whisper model: {model_name}")
        # Always try to use CUDA if available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        if device == "cpu":
            logger.warning(f"CUDA not available for loading {model_name}. Using CPU instead, which will be significantly slower.")
        else:
            logger.info(f"Using CUDA for {model_name} model")
        
        models[model_name] = whisper.load_model(model_name, device=device)
        logger.info(f"Successfully loaded {model_name} model")
        return models[model_name]
    except Exception as e:
        logger.error(f"Failed to load {model_name} model: {e}")
        return None

def is_repetitive_transcription(text: str, threshold: float = 0.7) -> bool:
    """
    Detect if a transcription is just repetitive nonsense.
    Returns True if the text appears to be pathologically repetitive.
    
    Args:
        text: The transcription text to check
        threshold: What fraction of repeated content triggers detection (0.0-1.0)
    """
    if not text or len(text) < 10:
        return False
    
    # Look for common repetitive patterns in various languages
    common_repetitions = [
        "हुआ", "hua", "हूँ", "है", "है है", "ह", 
        "aaa", "ааа", "啊啊啊", "음음음", "응응응",
        "mmm", "hmm", "umm", "uh", "ah", "oh"
    ]
    
    # Count words/tokens in the text
    words = text.split()
    if not words:
        return False
    
    total_words = len(words)
    
    # Count the most common word
    word_counts = {}
    for word in words:
        word_counts[word] = word_counts.get(word, 0) + 1
    
    # Check if any single word is repeated too much
    most_common_word, count = max(word_counts.items(), key=lambda x: x[1])
    repetition_ratio = count / total_words
    
    # Check if the most common word is a known repetitive filler
    is_common_repetition = any(rep in most_common_word.lower() for rep in common_repetitions)
    
    # More aggressive threshold for known repetitive patterns
    effective_threshold = threshold * 0.8 if is_common_repetition else threshold
    
    if repetition_ratio > effective_threshold:
        logger.warning(f"Detected repetitive transcription: '{most_common_word}' repeated {count}/{total_words} times ({repetition_ratio:.2f})")
        return True
    
    # Also check for repeating sequences of 2-3 words
    if total_words >= 6:  # Only check if we have enough words
        for seq_len in [2, 3]:
            if total_words < seq_len * 2:
                continue
                
            sequences = [' '.join(words[i:i+seq_len]) for i in range(0, total_words - seq_len + 1)]
            seq_counts = {}
            for seq in sequences:
                seq_counts[seq] = seq_counts.get(seq, 0) + 1
            
            if seq_counts:
                most_common_seq, seq_count = max(seq_counts.items(), key=lambda x: x[1])
                seq_ratio = seq_count / (total_words - seq_len + 1)
                
                if seq_ratio > effective_threshold:
                    logger.warning(f"Detected repetitive sequence: '{most_common_seq}' repeated {seq_count} times ({seq_ratio:.2f})")
                    return True
    
    return False

def detect_audio_issues(audio_path: str) -> dict:
    """
    Analyze audio file to detect potential issues that could cause transcription problems.
    
    Returns:
        dict: Information about detected issues
    """
    try:
        import subprocess
        import json
        from pathlib import Path
        
        logger.info(f"Analyzing audio quality for {audio_path}")
        
        # Check file size
        file_size = Path(audio_path).stat().st_size
        if file_size < 10000:  # Less than 10KB
            return {"issue": "too_small", "message": f"Audio file too small: {file_size} bytes"}
            
        # Use ffprobe to get audio info
        cmd = [
            "ffprobe", 
            "-v", "quiet", 
            "-print_format", "json", 
            "-show_format", 
            "-show_streams", 
            audio_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return {"issue": "probe_failed", "message": f"Failed to analyze audio: {result.stderr}"}
            
        info = json.loads(result.stdout)
        
        # Check if audio stream exists
        if not info.get("streams"):
            return {"issue": "no_streams", "message": "No audio streams found"}
            
        audio_streams = [s for s in info["streams"] if s.get("codec_type") == "audio"]
        if not audio_streams:
            return {"issue": "no_audio", "message": "No audio streams found"}
            
        # Check duration
        duration = float(info["format"].get("duration", 0))
        if duration < 1.0:
            return {"issue": "too_short", "message": f"Audio too short: {duration:.2f} seconds"}
            
        # Check if very short but large file (possible corruption)
        if duration < 10 and file_size > 1000000:
            return {"issue": "possible_corruption", "message": f"Large file ({file_size} bytes) but short duration ({duration:.2f}s)"}
            
        # All checks passed
        return {"issue": None, "message": "No issues detected"}
            
    except Exception as e:
        logger.error(f"Error analyzing audio: {e}")
        return {"issue": "analysis_error", "message": f"Error analyzing audio: {e}"}

def transcribe_audio(
    audio_path: str,
    language: str = "te",
    return_segments: bool = False,
    *,
    model: str = "large-v3",
    beam_size: int = 20,
    initial_prompt: str | None = None,
    word_timestamps: bool = False
) -> dict:
    """
    High-accuracy transcription + transliteration using OpenAI Whisper.
    """
    audio_path = get_absolute_path(audio_path)
    logger.info(f"Transcribing audio: {audio_path}, language: {language}, model: {model}, beam_size: {beam_size}")
    
    # Map friendly language names to ISO codes if needed
    language_map = {"Telugu": "te", "Hindi": "hi"}
    iso_language = language_map.get(language, language)  # Use mapping if it's a full name, otherwise use as-is
    
    # Load the requested model if not already loaded
    whisper_model = load_model(model)
    
    # Check if model was loaded successfully
    if whisper_model is None:
        error_msg = f"Whisper model {model} could not be loaded"
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
    
    # Check for audio issues that might cause transcription problems
    audio_issues = detect_audio_issues(audio_path)
    if audio_issues["issue"]:
        logger.warning(f"⚠️ Potential audio issue detected: {audio_issues['message']}")

    # Configure whisper parameters
    decode_opts = {
        "language": iso_language,
        "beam_size": beam_size,
        "initial_prompt": initial_prompt,
        "temperature": 0.0,  # deterministic
        "word_timestamps": word_timestamps,
        "condition_on_previous_text": True,
        "verbose": True
    }

    try:
        logger.info(f"Starting transcription with options: {decode_opts}")
        
        # OpenAI Whisper API
        result = whisper_model.transcribe(audio_path, **decode_opts)
        
        full_text = result["text"].strip()
        segments_list = result["segments"]
        
        # Check for pathologically repetitive transcription
        if is_repetitive_transcription(full_text):
            logger.warning("Detected pathologically repetitive transcription. Retrying with different parameters.")
            
            # Retry with different settings that might help with difficult audio
            retry_opts = decode_opts.copy()
            retry_opts["temperature"] = 0.2  # Add some randomness
            retry_opts["beam_size"] = min(30, beam_size + 10)  # Increase beam size
            
            # Try with a different model if available (medium is less prone to hallucination)
            retry_model = whisper_model
            if model == "large-v3" and "medium" in models:
                retry_model = models["medium"]
                logger.info("Trying with medium model instead of large-v3")
            
            # Add an initial prompt to guide the model
            if not retry_opts["initial_prompt"]:
                retry_opts["initial_prompt"] = f"This is a song with lyrics in {language}."
            
            # Try to transcribe again
            logger.info(f"Retrying transcription with options: {retry_opts}")
            result = retry_model.transcribe(audio_path, **retry_opts)
            
            full_text = result["text"].strip()
            segments_list = result["segments"]
            
            # If still repetitive, try with a short sample of the audio
            if is_repetitive_transcription(full_text):
                logger.warning("Still getting repetitive output. Trying with a different section of audio.")
                
                # Create a shorter version of the audio file to try a different section
                import tempfile
                from pathlib import Path
                
                audio_dir = Path(audio_path).parent
                temp_audio = tempfile.NamedTemporaryFile(dir=audio_dir, suffix=".wav", delete=False)
                temp_audio_path = temp_audio.name
                temp_audio.close()
                
                # Try to extract a 30-second section starting at 30 seconds in
                # This might get past intro music or repetitive sections
                ffmpeg_cmd = [
                    "ffmpeg", "-y", "-i", audio_path,
                    "-ss", "30", "-t", "30", 
                    "-ar", "16000", "-ac", "1",
                    temp_audio_path
                ]
                
                try:
                    subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
                    logger.info(f"Created temporary audio sample: {temp_audio_path}")
                    
                    # Try to transcribe this section
                    sample_result = retry_model.transcribe(temp_audio_path, **retry_opts)
                    
                    # If better (not repetitive), use this result
                    if not is_repetitive_transcription(sample_result["text"]):
                        logger.info("Got better result from audio sample section")
                        full_text = sample_result["text"].strip()
                        segments_list = sample_result["segments"]
                    else:
                        logger.warning("Sample section also produced repetitive output")
                except Exception as e:
                    logger.error(f"Error creating audio sample: {e}")
                finally:
                    # Clean up temp file
                    try:
                        Path(temp_audio_path).unlink(missing_ok=True)
                    except:
                        pass
        
        # Format segments in the expected structure
        formatted_segments = []
        
        for i, segment in enumerate(segments_list):
            formatted_segment = {
                "id": i,
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"]
            }
            formatted_segments.append(formatted_segment)
        
        logger.info(f"Transcription successful, text length: {len(full_text)}")
        
        transliteration = get_english_transliteration(full_text, language)

        if not return_segments:
            return {"text": full_text, "transliteration": transliteration}

        # Use batch transliteration for all segments at once
        segments_out = batch_transliterate_segments(formatted_segments, language)
        
        logger.info(f"Processed {len(segments_out)} segments")

        result = {
            "text": full_text,
            "transliteration": transliteration,
            "segments": segments_out,
        }
        
        return result
    except torch.cuda.OutOfMemoryError:
        error_msg = "CUDA out of memory error. Try using a smaller model or reducing batch size."
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
    p.add_argument("audio"); p.add_argument("--language",default="te")
    p.add_argument("--prompt",dest="initial_prompt"); p.add_argument("--segments",action="store_true")
    p.add_argument("--separate-vocals",action="store_true")
    p.add_argument("--model",default="large-v3",help="Whisper model to use (large-v3, large, medium, small, base)")
    p.add_argument("--beam-size",type=int,default=20,help="Beam size for transcription (1-20)")
    p.add_argument("--cpu",action="store_true",help="Force CPU usage even if CUDA is available")
    p.add_argument("--word-timestamps",action="store_true",help="Enable word-level timestamps")
    args=p.parse_args()
    
    logger.info(f"Processing audio: {args.audio}, language: {args.language}, model: {args.model}, beam_size: {args.beam_size}")

    # Force CPU if requested
    if args.cpu and torch.cuda.is_available():
        logger.info("Forcing CPU usage as requested")
        torch.cuda.is_available = lambda: False

    target=args.audio
    if args.separate_vocals:
        logger.info("Separating vocals before transcription")
        separated_path = separate_vocals(args.audio)
        if separated_path:
            target = separated_path
        else:
            logger.error("Vocal separation failed, using original audio")

    out=transcribe_audio(
        target, 
        args.language, 
        args.segments,
        model=args.model,
        beam_size=args.beam_size,
        initial_prompt=args.initial_prompt,
        word_timestamps=args.word_timestamps
    )

    print("\n====== TRANSCRIPTION ======\n",out["text"])
    print("\n====== TRANSLITERATION ====\n",out["transliteration"])
    if args.segments and "segments" in out:
        print("\n====== SEGMENTS ==========\n")
        for s in out["segments"]:
            print(f"[{s['start']:7.2f}-{s['end']:7.2f}] {s['transliteration']}")

if __name__=="__main__":                # harmless when imported in your project
    main()
