import os
import tempfile
from pathlib import Path
import asyncio
import shutil
import uuid
import demucs.separate
import torch
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from typing import Dict, List, Optional, Tuple, Any
import threading
import jiwer
from pydantic import BaseModel
import re
import difflib

# Import local modules
from vad_filter import filter_vad
from simple_transcribe import transcribe
from lyrics_transliterator import add_transliteration as add_trans, validate_azure_openai_key

app = FastAPI(title="Audio Transcription API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a directory for temporary files
TEMP_DIR = Path("./temp")
TEMP_DIR.mkdir(exist_ok=True)

# Create directory for phonetic correction resources
RESOURCES_DIR = Path("./resources")
RESOURCES_DIR.mkdir(exist_ok=True)

# Store active websocket connections
active_connections: Dict[str, WebSocket] = {}

# Check if Azure OpenAI API is available
AZURE_API_AVAILABLE = validate_azure_openai_key()
if not AZURE_API_AVAILABLE:
    print("Warning: Azure OpenAI API is not available. Transliteration feature will be disabled.")

# Define request model for WER calculation
class WERRequest(BaseModel):
    reference: str
    hypothesis: str

async def send_update(client_id: str, message: str):
    """Send status update to client via websocket"""
    if client_id in active_connections:
        await active_connections[client_id].send_text(message)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    active_connections[client_id] = websocket
    try:
        await websocket.send_text(f"Connected with client_id: {client_id}")
        # Keep connection open until client disconnects
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        if client_id in active_connections:
            del active_connections[client_id]

def align_sequences(reference_words: List[str], hypothesis_words: List[str]) -> List[Dict[str, Any]]:
    """
    Aligns reference and hypothesis word sequences and identifies substitutions, deletions, and insertions.
    Uses python's difflib instead of jiwer internals.
    Returns a detailed comparison with word-level classification.
    """
    # Use difflib's SequenceMatcher for alignment
    matcher = difflib.SequenceMatcher(None, reference_words, hypothesis_words)
    
    # Process the operations to create a list of classified words
    result = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':  # Words match
            for k in range(i1, i2):
                word = reference_words[k]
                result.append({
                    "word": word,
                    "type": "correct",
                    "reference_index": k,
                    "hypothesis_index": j1 + (k - i1)
                })
                
        elif tag == 'replace':  # Substitution
            # Handle case where number of words don't match
            min_len = min(i2 - i1, j2 - j1)
            
            # Process substitutions (matched pairs)
            for k in range(min_len):
                ref_word = reference_words[i1 + k]
                hyp_word = hypothesis_words[j1 + k]
                result.append({
                    "reference_word": ref_word,
                    "hypothesis_word": hyp_word,
                    "type": "substitution",
                    "reference_index": i1 + k,
                    "hypothesis_index": j1 + k
                })
            
            # Handle extra reference words as deletions
            for k in range(min_len, i2 - i1):
                ref_word = reference_words[i1 + k]
                result.append({
                    "word": ref_word,
                    "type": "deletion",
                    "reference_index": i1 + k
                })
            
            # Handle extra hypothesis words as insertions
            for k in range(min_len, j2 - j1):
                hyp_word = hypothesis_words[j1 + k]
                result.append({
                    "word": hyp_word,
                    "type": "insertion",
                    "hypothesis_index": j1 + k
                })
                
        elif tag == 'insert':  # Insertion (in hypothesis but not reference)
            for k in range(j1, j2):
                hyp_word = hypothesis_words[k]
                result.append({
                    "word": hyp_word,
                    "type": "insertion",
                    "hypothesis_index": k
                })
                
        elif tag == 'delete':  # Deletion (in reference but not hypothesis)
            for k in range(i1, i2):
                ref_word = reference_words[k]
                result.append({
                    "word": ref_word,
                    "type": "deletion",
                    "reference_index": k
                })
    
    return result

@app.post("/calculate-wer")
async def calculate_wer(request: WERRequest):
    """Calculate Word Error Rate between reference and hypothesis texts with detailed word-level comparison"""
    try:
        # Preprocess inputs
        reference_clean = request.reference.strip()
        hypothesis_clean = request.hypothesis.strip()
        
        # Calculate WER using jiwer
        wer = jiwer.wer(reference_clean, hypothesis_clean)
        
        # Calculate additional metrics
        mer = jiwer.mer(reference_clean, hypothesis_clean)
        wil = jiwer.wil(reference_clean, hypothesis_clean)
        
        # Split text into words for alignment
        reference_words = re.findall(r'\S+', reference_clean)
        hypothesis_words = re.findall(r'\S+', hypothesis_clean)
        
        # Get detailed word-by-word alignment
        word_alignments = align_sequences(reference_words, hypothesis_words)
        
        # Count error types
        substitutions = sum(1 for item in word_alignments if item["type"] == "substitution")
        deletions = sum(1 for item in word_alignments if item["type"] == "deletion")
        insertions = sum(1 for item in word_alignments if item["type"] == "insertion")
        
        # Generate HTML representations with color-coded spans
        reference_html = []
        hypothesis_html = []
        
        for item in word_alignments:
            if item["type"] == "correct":
                reference_html.append(f'<span class="correct">{item["word"]}</span>')
                hypothesis_html.append(f'<span class="correct">{item["word"]}</span>')
            elif item["type"] == "substitution":
                reference_html.append(f'<span class="substitution">{item["reference_word"]}</span>')
                hypothesis_html.append(f'<span class="substitution">{item["hypothesis_word"]}</span>')
            elif item["type"] == "deletion":
                reference_html.append(f'<span class="deletion">{item["word"]}</span>')
            elif item["type"] == "insertion":
                hypothesis_html.append(f'<span class="insertion">{item["word"]}</span>')
        
        return {
            "wer": wer,
            "mer": mer,
            "wil": wil,
            "substitutions": substitutions,
            "deletions": deletions,
            "insertions": insertions,
            "total_words": len(reference_words),
            "reference_html": " ".join(reference_html),
            "hypothesis_html": " ".join(hypothesis_html),
            "word_alignments": word_alignments,
            "success": True
        }
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }

@app.post("/upload")
async def upload_audio(
    file: UploadFile = File(...), 
    client_id: str = None, 
    language: str = "te", 
    model: str = "large-v3", 
    beam_size: int = 20,
    enable_transliteration: bool = True
):
    if not client_id or client_id not in active_connections:
        return JSONResponse(
            status_code=400,
            content={"error": "No active WebSocket connection. Connect to websocket first."}
        )
    
    # Check if transliteration is available
    if enable_transliteration and not AZURE_API_AVAILABLE:
        await send_update(client_id, "Warning: Azure OpenAI API is not available. Transliteration will be disabled.")
    
    # Create a unique job ID
    job_id = str(uuid.uuid4())
    
    # Create a job directory
    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(exist_ok=True)
    
    # Save the uploaded file
    input_path = job_dir / f"input.mp3"
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Start processing in a separate thread
    process_thread = threading.Thread(
        target=asyncio.run,
        args=(process_audio(
            str(input_path), 
            client_id, 
            job_id, 
            language, 
            model, 
            beam_size,
            enable_transliteration and AZURE_API_AVAILABLE
        ),)
    )
    process_thread.start()
    
    return {
        "message": "Processing started", 
        "job_id": job_id, 
        "language": language, 
        "model": model,
        "options": {
            "enable_transliteration": enable_transliteration and AZURE_API_AVAILABLE
        },
        "azure_api_available": AZURE_API_AVAILABLE
    }

async def process_audio(
    input_path: str, 
    client_id: str, 
    job_id: str, 
    language: str = "te", 
    model_name: str = "large-v3", 
    beam_size: int = 20,
    enable_transliteration: bool = True
):
    job_dir = TEMP_DIR / job_id
    
    try:
        # Step 1: Remove music using demucs
        await send_update(client_id, f"Step 1/3: Removing background music with Demucs...")
        
        # Set up demucs parameters
        demucs_output = job_dir / "demucs_output"
        demucs_output.mkdir(exist_ok=True)
        
        # Run demucs to separate vocals
        demucs.separate.main([
            "--two-stems=vocals", 
            "-o", str(demucs_output),
            input_path
        ])
        
        # Find the vocals track
        vocals_path = None
        for path in demucs_output.glob("**/*vocals.wav"):
            vocals_path = path
            break
        
        if not vocals_path:
            await send_update(client_id, "Error: Failed to extract vocals from audio")
            return
        
        await send_update(client_id, "Music removal complete")
        
        # Step 2: Transcribe the audio (skipping VAD filtering)
        await send_update(client_id, f"Step 2/3: Transcribing {language} audio using {model_name} model with beam size {beam_size}...")
        transcription_result = transcribe(str(vocals_path), model_name=model_name, language=language, beam_size=beam_size)
        await send_update(client_id, "Transcription complete")

        # Step 3: Add transliteration if requested
        transliterated_segments = None
        if enable_transliteration:
            await send_update(client_id, "Step 3/3: Adding transliteration...")
            
            # Use the simplified transliteration function that does everything in one call
            transliteration_result = add_trans(transcription_result, language)
            if "transliterated_segments" in transliteration_result:
                transliterated_segments = transliteration_result["transliterated_segments"]
            
            await send_update(client_id, "Transliteration complete")

        final_result = {
            "status": "complete",
            "segments": transcription_result["segments"]
        }
        
        # Add transliteration to final result if available
        if transliterated_segments:
            final_result["transliterated_segments"] = transliterated_segments
        
        await active_connections[client_id].send_json(final_result)
        await send_update(client_id, "Processing complete!")
        
    except Exception as e:
        error_message = f"Error during processing: {str(e)}"
        await send_update(client_id, error_message)
    finally:
        # Clean up temporary files (optional)
        # shutil.rmtree(job_dir, ignore_errors=True)
        pass

@app.get("/")
async def root():
    return {
        "message": "Audio Transcription API is running. Connect to WebSocket first, then upload your audio file.",
        "azure_api_available": AZURE_API_AVAILABLE,
        "supported_languages": ["hi", "te"]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
