#!/usr/bin/env python3
"""
Whisper large-v3 - high-accuracy, CPU-friendly, project-compatible
"""

# ─── Imports & helpers (identical to previous) ─────────────────────────────
import os, random, subprocess, json, argparse, textwrap
from pathlib import Path
import numpy as np, torch, whisper, requests

def set_seed(seed:int=42):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    if torch.backends.cudnn.is_available():
        torch.backends.cudnn.deterministic=True; torch.backends.cudnn.benchmark=False
set_seed(42)

DEVICE="cpu"                       # change to "cuda" if you have a GPU
model = whisper.load_model("large-v3", device=DEVICE)

AZURE_OPENAI_ENDPOINT = (
    "https://scout-llm-2.openai.azure.com/"
    "openai/deployments/gpt-4o/chat/completions?api-version=2025-01-01-preview"
)
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "REPLACE_ME")

def separate_vocals(input_path:str, output_dir:str="demucs_out")->str:
    cmd=["demucs","--two-stems","vocals","--device","cpu","-o",output_dir,input_path]
    subprocess.run(cmd,check=True)
    song=Path(input_path).stem
    return os.path.join(output_dir,"htdemucs",song,"vocals.wav")

def get_english_transliteration(text:str, lang:str)->str:
    headers={"Content-Type":"application/json","api-key":AZURE_OPENAI_KEY}
    prompt=(f"Transliterate the following {lang} text to English "
            f"(use Latin characters only):\n\n{text}")
    payload={
        "messages":[
            {"role":"system","content":"You are a transliteration expert."},
            {"role":"user","content":prompt}
        ],
        "temperature":0,"top_p":0,"max_tokens":5000
    }
    try:
        r=requests.post(AZURE_OPENAI_ENDPOINT,headers=headers,data=json.dumps(payload))
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"❌ Transliteration error: {e}")
        return f"Transliteration failed: {e}"

def transcribe_audio(
    audio_path: str,
    language: str = "Telugu",
    return_segments: bool = False,   # ← keeps your old positional layout
    *,                               # anything after this is keyword-only
    initial_prompt: str | None = None
) -> dict:
    """
    High-accuracy, deterministic transcription + transliteration.
    Signature is identical to your original codebase.
    """
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

    result = model.transcribe(audio_path, **decode_opts)

    transliteration = get_english_transliteration(result["text"], language)

    if not return_segments:
        return {"text": result["text"], "transliteration": transliteration}

    segments_out = []
    for seg in result["segments"]:
        segments_out.append(
            {
                "id": seg["id"],
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
                "transliteration": get_english_transliteration(seg["text"], language),
            }
        )

    return {
        "text": result["text"],
        "transliteration": transliteration,
        "segments": segments_out,
    }

# ─── Optional CLI driver for quick testing (unchanged) ─────────────────────
def main():
    p=argparse.ArgumentParser(description="High-accuracy Whisper transcription")
    p.add_argument("audio"); p.add_argument("--language",default="Telugu")
    p.add_argument("--prompt",dest="initial_prompt"); p.add_argument("--segments",action="store_true")
    p.add_argument("--separate-vocals",action="store_true")
    args=p.parse_args()

    target=args.audio
    if args.separate_vocals:
        target=separate_vocals(args.audio)

    out=transcribe_audio(target,args.language,args.segments,initial_prompt=args.initial_prompt)

    print("\n====== TRANSCRIPTION ======\n",out["text"])
    print("\n====== TRANSLITERATION ====\n",out["transliteration"])
    if args.segments:
        print("\n====== SEGMENTS ==========\n")
        for s in out["segments"]:
            print(f"[{s['start']:7.2f}-{s['end']:7.2f}] {s['transliteration']}")

if __name__=="__main__":                # harmless when imported in your project
    main()
