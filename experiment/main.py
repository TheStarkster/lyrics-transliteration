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
import re
from pydantic import BaseModel

class WERRequest(BaseModel):
    reference: str
    hypothesis: str

# Import local modules
from vad_filter import filter_vad
from simple_transcribe import transcribe
from lyrics_transliterator import add_transliteration as add_trans, validate_azure_openai_key
from ai_wer import calculate_wer

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

@app.post("/calculate-wer")
async def calculate_wer_endpoint(payload: WERRequest):
    try:
        wer_result = calculate_wer(payload.reference, payload.hypothesis)
        return wer_result
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
        
        demucs_output = job_dir / "demucs_output"
        demucs_output.mkdir(exist_ok=True)
        
        demucs.separate.main([
            "--two-stems=vocals", 
            "-o", str(demucs_output),
            input_path
        ])
        
        vocals_path = next(demucs_output.glob("**/*vocals.wav"), None)
        
        if not vocals_path:
            await send_update(client_id, "Error: Failed to extract vocals from audio")
            return
        
        await send_update(client_id, "Music removal complete")
        
        # Step 2: Transcribe the audio
        await send_update(client_id, f"Step 2/3: Transcribing {language} audio using {model_name} model with beam size {beam_size}...")
        transcription_result = transcribe(str(vocals_path), model_name=model_name, language=language, beam_size=beam_size)
        await send_update(client_id, "Transcription complete")

        # Step 3: Transliteration with retry mechanism
        transliterated_segments = None
        if enable_transliteration:
            await send_update(client_id, "Step 3/3: Adding transliteration...")
            max_retries = 3
            for attempt in range(1, max_retries + 1):
                try:
                    transliteration_result = add_trans(transcription_result, language)
                    if "transliterated_segments" in transliteration_result:
                        transliterated_segments = transliteration_result["transliterated_segments"]
                    await send_update(client_id, "Transliteration complete")
                    break  # Success
                except Exception as te:
                    await send_update(client_id, f"Transliteration attempt {attempt} failed: {str(te)}")
                    if attempt == max_retries:
                        await send_update(client_id, "Transliteration failed after multiple attempts. Proceeding without it.")
                        transliterated_segments = None

        final_result = {
            "status": "complete",
            "segments": transcription_result["segments"]
        }

        if transliterated_segments:
            final_result["transliterated_segments"] = transliterated_segments
        
        await active_connections[client_id].send_json(final_result)
        await send_update(client_id, "Processing complete!")

    except Exception as e:
        error_message = f"Error during processing: {str(e)}"
        await send_update(client_id, error_message)
    finally:
        # Optional cleanup
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