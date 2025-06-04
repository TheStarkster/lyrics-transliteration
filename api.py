#!/usr/bin/env python3

import os
import tempfile
import logging
import requests
import json
import time
import re
import subprocess
import shutil
import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Form, File, UploadFile, Depends
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Azure Speech Translation API credentials
AZURE_SPEECH_KEY = "FR8TunAFCts46TTcUPOBuFouMnFY6SHp1i3ocUKHtCZ2O0guJsBjJQQJ99BEACGhslBXJ3w3AAAYACOG9e7Q"
AZURE_SPEECH_REGION = "centralindia"

# Azure Translator API credentials
AZURE_TRANSLATOR_ENDPOINT = "https://api.cognitive.microsofttranslator.com"
AZURE_TRANSLATOR_LOCATION = "centralindia"
AZURE_TRANSLATOR_KEY = "B03R6qIW4PKOxz9hlYwHT7TlBqjUboLbk3tNub2UpkEg70PRB0H8JQQJ99BFACGhslBXJ3w3AAAbACOG3Uw6"

# Language configurations
LANGUAGE_CONFIGS = {
    "telugu": {
        "name": "Telugu",
        "speech_code": "te-IN", 
        "translator_code": "te",
        "script": "Telu"
    },
    "hindi": {
        "name": "Hindi",
        "speech_code": "hi-IN",
        "translator_code": "hi",
        "script": "Deva"
    }
}

# Create FastAPI app
app = FastAPI(
    title="Audio Transcription API",
    description="API to transcribe Telugu and Hindi audio files and transliterate to English characters",
    version="1.0.0"
)

# Set up templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create directories if they don't exist
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

# Request and response models
class AudioFileRequest(BaseModel):
    filename: str
    language: str
    output_filename: Optional[str] = None

class TranscriptionResponse(BaseModel):
    original_lyrics: str
    transliterated_lyrics: str
    audio_filename: str
    language: str
    status: str

class ProcessingStatus(BaseModel):
    task_id: str
    status: str
    message: str

# In-memory task storage
tasks = {}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/submit")
async def submit_form(
    request: Request, 
    audio_file: UploadFile = File(...),
    language: str = Form(...), 
    background_tasks: BackgroundTasks = None
):
    # Validate language
    if language not in LANGUAGE_CONFIGS:
        return templates.TemplateResponse(
            "error.html", 
            {
                "request": request,
                "error_message": f"Unsupported language: {language}. Supported languages are: {', '.join(LANGUAGE_CONFIGS.keys())}"
            }
        )
    
    # Generate a task ID
    task_id = str(uuid.uuid4())
    
    # Create initial task status
    tasks[task_id] = {
        "status": "processing",
        "message": "Task has been queued for processing",
        "result": None,
        "language": language
    }
    
    # Save the uploaded file
    file_location = os.path.join("uploads", f"{task_id}_{audio_file.filename}")
    with open(file_location, "wb+") as file_object:
        file_object.write(await audio_file.read())
    
    # Queue the background task
    background_tasks.add_task(
        process_audio_task, 
        task_id=task_id, 
        file_path=file_location,
        language=language
    )
    
    # Check if the request prefers JSON response (AJAX request)
    accept_header = request.headers.get("accept", "")
    if "application/json" in accept_header:
        return ProcessingStatus(
            task_id=task_id, 
            status="processing", 
            message=f"Processing {LANGUAGE_CONFIGS[language]['name']} audio started"
        )
    else:
        # Return the template with task ID (for traditional form submission)
        return templates.TemplateResponse(
            "processing.html", 
            {
                "request": request,
                "task_id": task_id,
                "message": f"Processing {LANGUAGE_CONFIGS[language]['name']} audio started"
            }
        )

@app.get("/result-page/{task_id}", response_class=HTMLResponse)
async def result_page(request: Request, task_id: str):
    if task_id not in tasks:
        return templates.TemplateResponse(
            "error.html", 
            {
                "request": request,
                "error_message": "Task not found"
            }
        )
    
    task = tasks[task_id]
    
    if task["status"] != "completed":
        return templates.TemplateResponse(
            "processing.html", 
            {
                "request": request,
                "task_id": task_id,
                "status": task["status"],
                "message": task["message"]
            }
        )
    
    return templates.TemplateResponse(
        "result.html", 
        {
            "request": request,
            "task_id": task_id,
            "original_lyrics": task["result"]["original_lyrics"],
            "transliterated_lyrics": task["result"]["transliterated_lyrics"],
            "audio_filename": task["result"]["audio_filename"],
            "language": LANGUAGE_CONFIGS[task["language"]]["name"]
        }
    )

# API endpoints for programmatic access
@app.post("/api/process", response_model=ProcessingStatus)
async def process_audio_api(
    audio_file: UploadFile = File(...), 
    language: str = Form(...),
    background_tasks: BackgroundTasks = None
):
    # Validate language
    if language not in LANGUAGE_CONFIGS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported language: {language}. Supported languages are: {', '.join(LANGUAGE_CONFIGS.keys())}"
        )
    
    # Generate a task ID
    task_id = str(uuid.uuid4())
    
    # Create initial task status
    tasks[task_id] = {
        "status": "processing",
        "message": "Task has been queued for processing",
        "result": None,
        "language": language
    }
    
    # Save the uploaded file
    file_location = os.path.join("uploads", f"{task_id}_{audio_file.filename}")
    with open(file_location, "wb+") as file_object:
        file_object.write(await audio_file.read())
    
    # Queue the background task
    background_tasks.add_task(
        process_audio_task, 
        task_id=task_id, 
        file_path=file_location,
        language=language
    )
    
    return ProcessingStatus(task_id=task_id, status="processing", message="Task has been queued")

@app.get("/api/status/{task_id}", response_model=ProcessingStatus)
async def get_task_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    return ProcessingStatus(
        task_id=task_id,
        status=task["status"],
        message=task["message"]
    )

@app.get("/api/result/{task_id}")
async def get_task_result(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    
    if task["status"] != "completed":
        return ProcessingStatus(
            task_id=task_id,
            status=task["status"],
            message=task["message"]
        )
    
    return task["result"]

# The function to process audio files in the background
async def process_audio_task(task_id: str, file_path: str, language: str):
    try:
        # Update task status
        tasks[task_id]["message"] = "Processing audio file"
        tasks[task_id]["status"] = "processing"
        
        # Ensure the file exists and is an audio file
        if not os.path.exists(file_path):
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["message"] = "Audio file not found"
            return
            
        # Update task status
        lang_name = LANGUAGE_CONFIGS[language]["name"]
        tasks[task_id]["message"] = f"Transcribing audio to {lang_name} text"
        tasks[task_id]["status"] = "transcribing"
        
        # Transcribe the audio
        lyrics = transcribe_with_azure_speech(file_path, language)
        
        if not lyrics or lyrics.startswith("Error:"):
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["message"] = "Failed to transcribe the audio"
            return
            
        # Update task status
        tasks[task_id]["message"] = f"Transliterating {lang_name} text to English characters"
        tasks[task_id]["status"] = "transliterating"
        
        # Transliterate the lyrics
        transliterated_lyrics = transliterate_to_english(lyrics, language)
        
        if not transliterated_lyrics:
            tasks[task_id]["status"] = "completed_partial"
            tasks[task_id]["message"] = "Transcription successful, but transliteration failed"
            tasks[task_id]["result"] = {
                "original_lyrics": lyrics,
                "transliterated_lyrics": "",
                "audio_filename": os.path.basename(file_path),
                "language": language,
                "status": "completed_partial"
            }
            return
        
        # Update task status to completed
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["message"] = "Processing completed successfully"
        
        # Store the result
        tasks[task_id]["result"] = {
            "original_lyrics": lyrics,
            "transliterated_lyrics": transliterated_lyrics,
            "audio_filename": os.path.basename(file_path),
            "language": language,
            "status": "completed"
        }
                
    except Exception as e:
        logger.error(f"Error processing task: {e}")
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["message"] = f"An error occurred: {str(e)}"

def transcribe_with_azure_speech(audio_file, language):
    """Transcribe the audio file using Azure Speech REST API with chunking."""
    try:
        logger.info(f"Transcribing {language} audio with Azure Speech REST API...")
        
        # Check if file exists
        if not os.path.exists(audio_file):
            logger.error(f"Audio file not found: {audio_file}")
            return "Error: Audio file not found"
        
        # Check file size - if larger than 1MB, use chunking approach
        file_size_mb = os.path.getsize(audio_file) / (1024 * 1024)
        logger.info(f"Audio file size: {file_size_mb:.2f} MB")
        
        # For larger files, use the chunking approach
        if file_size_mb > 1:
            return transcribe_mp3_directly(audio_file, language)
        else:
            # For small files, use direct transcription
            return transcribe_single_file(audio_file, language)
            
    except Exception as e:
        logger.error(f"Error transcribing with Azure Speech: {e}")
        return f"Error: {str(e)}"

def transcribe_mp3_directly(file_path, language):
    """
    Transcribe an MP3 file directly by splitting it into smaller chunks
    and sending each chunk to the Azure Speech API.
    """
    try:
        logger.info(f"Transcribing {language} MP3 directly in chunks...")
        
        # Create a temporary directory for chunks
        temp_dir = tempfile.mkdtemp()
        chunk_duration = 60  # Split into 60-second chunks
        
        # Split the MP3 file into chunks using ffmpeg
        try:
            # Get the duration of the audio file
            result = subprocess.run(
                ["ffmpeg", "-i", file_path],
                capture_output=True,
                text=True
            )
            duration_match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d+)", result.stderr)
            
            if not duration_match:
                logger.warning("Could not determine audio duration, using single-pass transcription")
                return transcribe_single_file(file_path, language)
                
            hours, minutes, seconds = map(float, duration_match.groups())
            total_seconds = hours * 3600 + minutes * 60 + seconds
            logger.info(f"Audio duration: {total_seconds:.2f} seconds")
            
            # If less than 2 minutes, just transcribe directly
            if total_seconds < 120:
                logger.info("Audio is short enough for direct transcription")
                return transcribe_single_file(file_path, language)
            
            # Split the file into chunks
            chunk_count = int(total_seconds / chunk_duration) + 1
            logger.info(f"Splitting audio into {chunk_count} chunks of {chunk_duration} seconds...")
            
            chunk_files = []
            for i in range(chunk_count):
                start_time = i * chunk_duration
                chunk_file = os.path.join(temp_dir, f"chunk_{i:03d}.wav")
                
                # Use ffmpeg to extract a chunk
                subprocess.run(
                    [
                        "ffmpeg", "-y", 
                        "-ss", str(start_time), 
                        "-t", str(chunk_duration),
                        "-i", file_path,
                        "-acodec", "pcm_s16le",
                        "-ar", "16000",
                        "-ac", "1",
                        chunk_file
                    ],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                if os.path.exists(chunk_file) and os.path.getsize(chunk_file) > 1000:
                    chunk_files.append(chunk_file)
                    logger.info(f"Created chunk {i+1}/{chunk_count}: {chunk_file}")
            
            # Transcribe each chunk
            transcriptions = []
            for i, chunk_file in enumerate(chunk_files):
                logger.info(f"Transcribing chunk {i+1}/{len(chunk_files)}...")
                
                # Call the Azure Speech API for this chunk
                chunk_text = transcribe_single_file(chunk_file, language)
                
                if chunk_text and not chunk_text.startswith("Error:"):
                    transcriptions.append(chunk_text)
                    logger.info(f"Successfully transcribed chunk {i+1}")
                else:
                    logger.warning(f"Failed to transcribe chunk {i+1}: {chunk_text}")
            
            # Combine all transcriptions
            full_transcription = " ".join(transcriptions)
            
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Removed temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary directory: {e}")
            
            if not full_transcription:
                logger.error("All chunks failed to transcribe")
                return "Error: Failed to transcribe audio"
                
            return full_transcription
            
        except Exception as e:
            logger.error(f"Error splitting audio file: {e}")
            # Try transcribing the whole file as a fallback
            logger.info("Falling back to single-file transcription")
            return transcribe_single_file(file_path, language)
    
    except Exception as e:
        logger.error(f"Error in direct MP3 transcription: {e}")
        return f"Error: {str(e)}"

def transcribe_single_file(file_path, language):
    """
    Transcribe a single audio file using the Azure Speech REST API.
    """
    try:
        logger.info(f"Transcribing single {language} file: {file_path}")
        
        # Get language code from config
        language_code = LANGUAGE_CONFIGS[language]["speech_code"]
        
        # Convert to WAV if it's an MP3
        if file_path.lower().endswith('.mp3'):
            wav_path = os.path.splitext(file_path)[0] + '.wav'
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-i", file_path, "-acodec", "pcm_s16le", "-ac", "1", "-ar", "16000", wav_path],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                logger.info(f"Converted to WAV: {wav_path}")
                file_path = wav_path
            except Exception as e:
                logger.error(f"Failed to convert to WAV: {e}")
                # Continue with the original file
        
        # Azure Speech REST API endpoint
        endpoint = f"https://{AZURE_SPEECH_REGION}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
        
        # Query parameters
        params = {
            "language": language_code,  # Use the language-specific code
            "format": "detailed"   # Get detailed output
        }
        
        # Prepare the headers
        headers = {
            "Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY,
            "Content-Type": "audio/wav",  # We're using WAV format
            "Accept": "application/json"
        }
        
        # Read the audio file
        with open(file_path, "rb") as audio_data:
            # Make the API request
            response = requests.post(
                endpoint,
                params=params,
                headers=headers,
                data=audio_data
            )
        
        # Process the response
        if response.status_code == 200:
            result = response.json()
            
            # Extract the recognized text
            recognized_text = result.get("DisplayText", "")
            if not recognized_text and "NBest" in result:
                # Try to get from NBest results if available
                nbest = result.get("NBest", [])
                if nbest and len(nbest) > 0:
                    recognized_text = nbest[0].get("Display", "")
            
            if not recognized_text:
                logger.warning("Received empty transcription for chunk")
                return ""
            
            return recognized_text
        else:
            error_msg = f"API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return f"Error: {response.status_code}"
            
    except Exception as e:
        logger.error(f"Error in single file transcription: {e}")
        return f"Error: {str(e)}"

def transliterate_to_english(text, language):
    """Transliterate text to English characters using Azure Translator API."""
    try:
        lang_name = LANGUAGE_CONFIGS[language]["name"]
        lang_code = LANGUAGE_CONFIGS[language]["translator_code"]
        script = LANGUAGE_CONFIGS[language]["script"]
        
        logger.info(f"Transliterating {lang_name} text to English characters...")
        
        # Break text into manageable chunks if it's too large
        # Azure Translator has limits on request size
        chunks = []
        if len(text) > 5000:
            # Split by spaces to avoid cutting words
            words = text.split()
            current_chunk = ""
            
            for word in words:
                if len(current_chunk) + len(word) + 1 <= 5000:
                    if current_chunk:
                        current_chunk += " " + word
                    else:
                        current_chunk = word
                else:
                    chunks.append(current_chunk)
                    current_chunk = word
            
            if current_chunk:
                chunks.append(current_chunk)
        else:
            chunks = [text]
        
        # Process each chunk
        transliterated_chunks = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Transliterating chunk {i+1}/{len(chunks)}...")
            
            # Set up the API call
            path = '/transliterate'
            params = {
                'api-version': '3.0',
                'language': lang_code,
                'fromScript': script,
                'toScript': 'Latn'
            }
            constructed_url = AZURE_TRANSLATOR_ENDPOINT + path
            
            headers = {
                'Ocp-Apim-Subscription-Key': AZURE_TRANSLATOR_KEY,
                'Ocp-Apim-Subscription-Region': AZURE_TRANSLATOR_LOCATION,
                'Content-type': 'application/json',
                'X-ClientTraceId': str(uuid.uuid4())
            }
            
            body = [{'Text': chunk}]
            
            # Make the API request
            response = requests.post(constructed_url, params=params, headers=headers, json=body)
            
            if response.status_code == 200:
                results = response.json()
                if results and len(results) > 0:
                    transliterated_text = results[0].get('text', '')
                    transliterated_chunks.append(transliterated_text)
                    logger.info(f"Successfully transliterated chunk {i+1}")
                else:
                    logger.warning(f"Empty response for chunk {i+1}")
                    transliterated_chunks.append(chunk)  # Fall back to original text
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                transliterated_chunks.append(chunk)  # Fall back to original text
        
        # Combine all transliterated chunks
        full_transliteration = " ".join(transliterated_chunks)
        
        return full_transliteration
        
    except Exception as e:
        logger.error(f"Error transliterating text: {e}")
        return ""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 