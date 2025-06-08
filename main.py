from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import shutil, os, uuid, asyncio
from processing import separate_vocals, transcribe_audio
from fastapi.responses import JSONResponse
import json
import threading
import time

app = FastAPI()

# Add CORS middleware to allow requests from any source
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

sockets = {}

# Create temp directory if it doesn't exist
os.makedirs("temp", exist_ok=True)
os.makedirs("temp/output", exist_ok=True)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    sockets[client_id] = websocket
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        sockets.pop(client_id, None)

# Create a background task that properly awaits the websocket send
async def _send_websocket_message(websocket, message):
    try:
        await websocket.send_text(message)
    except Exception as e:
        print(f"Error sending WebSocket message: {e}")

def send_progress(client_id, message):
    print(f"Sending progress to {client_id}: {message}")
    
    async def _send_async():
        if client_id in sockets:
            try:
                await _send_websocket_message(sockets[client_id], message)
            except Exception as e:
                print(f"Error sending WebSocket message: {e}")
    
    # Create a new event loop for this thread
    asyncio.run(_send_async())

# This function runs in a separate thread and handles the CPU-intensive work
def process_in_thread(tmp_input, tmp_output_dir, client_id, language, model, beam_size, return_segments):
    try:
        # Send an initial message
        send_progress(client_id, "✅ File uploaded. Starting vocal separation...")
        
        # Small delay to ensure message ordering
        time.sleep(1)
        
        # Run the CPU-intensive vocal separation
        vocals_path = separate_vocals(tmp_input, tmp_output_dir)
        send_progress(client_id, "🎙️ Vocal separation done. Starting transcription...")
        
        # Small delay to ensure message ordering
        time.sleep(1)
        
        # Run the CPU-intensive transcription
        result = transcribe_audio(vocals_path, language, return_segments, model=model, beam_size=beam_size)
        send_progress(client_id, f"📜 Transcription complete in {language} using {model} model.")
        
        # Small delay to ensure message ordering
        time.sleep(1)
        
        # Send message about transliteration
        send_progress(client_id, f"🔤 Generating English transliteration...")
        
        # Small delay to ensure message ordering
        time.sleep(1)
        
        # Send the final result (now includes transliteration)
        result_json = json.dumps(result)
        send_progress(client_id, f"RESULT:{result_json}")
            
    except Exception as e:
        print(f"Error in thread processing: {str(e)}")
        send_progress(client_id, f"❌ Error: {str(e)}")

@app.post("/upload/")
async def upload_file(
    file: UploadFile = File(...), 
    client_id: str = "", 
    language: str = "te", 
    model: str = "large-v3",
    beam_size: int = 20,
    return_segments: bool = False
):
    try:
        print(f"Received upload request from client_id: {client_id}, language: {language}, model: {model}, beam_size: {beam_size}")
        # Validate language input
        if language not in ["te", "hi", "Telugu", "Hindi"]:  # Support both ISO codes and full names for backward compatibility
            return JSONResponse(status_code=400, content={"error": "Language must be either 'te' (Telugu) or 'hi' (Hindi)"})
        
        # Validate model input
        valid_models = ["large-v3", "large", "medium", "small", "base"]
        if model not in valid_models:
            return JSONResponse(status_code=400, content={"error": f"Model must be one of: {', '.join(valid_models)}"})
        
        # Validate beam size
        if beam_size < 1 or beam_size > 20:
            return JSONResponse(status_code=400, content={"error": "Beam size must be between 1 and 20"})
            
        tmp_id = str(uuid.uuid4())
        tmp_input = f"temp/{tmp_id}_{file.filename}"
        tmp_output_dir = "temp/output"

        os.makedirs(tmp_output_dir, exist_ok=True)

        with open(tmp_input, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Start processing in a separate thread
        thread = threading.Thread(
            target=process_in_thread,
            args=(tmp_input, tmp_output_dir, client_id, language, model, beam_size, return_segments)
        )
        thread.daemon = True
        thread.start()
        
        return JSONResponse({"status": "processing", "message": "File uploaded, processing started"})
    
    except Exception as e:
        print(f"Error processing upload: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})
