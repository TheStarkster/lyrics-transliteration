import os
import tempfile
from pathlib import Path
import asyncio
import shutil
import uuid
import demucs.separate
import torch
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from typing import Dict, List
import threading

# Import local modules
from vad_filter import filter_vad
from simple_transcribe import transcribe

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

# Store active websocket connections
active_connections: Dict[str, WebSocket] = {}

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

@app.post("/upload")
async def upload_audio(file: UploadFile = File(...), client_id: str = None, language: str = "te", model: str = "large-v3", beam_size: int = 20):
    if not client_id or client_id not in active_connections:
        return JSONResponse(
            status_code=400,
            content={"error": "No active WebSocket connection. Connect to websocket first."}
        )
    
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
        args=(process_audio(str(input_path), client_id, job_id, language, model, beam_size),)
    )
    process_thread.start()
    
    return {"message": "Processing started", "job_id": job_id, "language": language, "model": model}

async def process_audio(input_path: str, client_id: str, job_id: str, language: str = "te", model_name: str = "large-v3", beam_size: int = 20):
    job_dir = TEMP_DIR / job_id
    
    try:
        # Step 1: Remove music using demucs
        await send_update(client_id, f"Step 1/4: Removing background music with Demucs...")
        
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
        
        # Step 2: Apply VAD filtering
        await send_update(client_id, "Step 2/4: Applying Voice Activity Detection (VAD)...")
        vad_output_path = filter_vad(str(vocals_path))
        await send_update(client_id, "VAD filtering complete")
        
        # Step 3: Transcribe the audio
        await send_update(client_id, f"Step 3/4: Transcribing {language} audio using {model_name} model with beam size {beam_size}...")
        transcription_result = transcribe(vad_output_path, model_name=model_name, language=language, beam_size=beam_size)
        await send_update(client_id, "Transcription complete")
        
        # Step 4: Send results
        await send_update(client_id, "Step 4/4: Preparing results...")
        
        # Format result with timestamps
        timestamp_text = ""
        for segment in transcription_result["segments"]:
            timestamp_text += f"[{segment['start']:.2f} --> {segment['end']:.2f}] {segment['text'].strip()}\n"
        
        result = {
            "status": "complete",
            "full_text": transcription_result["text"],
            "segments": transcription_result["segments"],
            "timestamp_text": timestamp_text,
            "language": language,
            "model": model_name
        }
        
        await active_connections[client_id].send_json(result)
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
    return {"message": "Audio Transcription API is running. Connect to WebSocket first, then upload your audio file."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
