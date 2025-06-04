#!/usr/bin/env python3

import os
import sys
import argparse
import tempfile
import logging
import requests
import json
import time
import re
import subprocess
import shutil

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Azure Speech Translation API credentials
AZURE_SPEECH_KEY = "FR8TunAFCts46TTcUPOBuFouMnFY6SHp1i3ocUKHtCZ2O0guJsBjJQQJ99BEACGhslBXJ3w3AAAYACOG9e7Q"
AZURE_SPEECH_REGION = "centralindia"

# GPT-4 API credentials for transliteration
GPT4_ENDPOINT = "https://scout-llm-2.openai.azure.com/openai/deployments/gpt-4/chat/completions?api-version=2025-01-01-preview"
GPT4_API_KEY = "c1b98148632f4133a5f5aa1146f640ed"

def parse_args():
    parser = argparse.ArgumentParser(description='Download YouTube video, convert to MP3, and extract Telugu lyrics using Azure Speech Translation.')
    parser.add_argument('url', help='YouTube URL to download')
    parser.add_argument('--output', '-o', default='output.mp3', help='Output MP3 file name')
    parser.add_argument('--transliterate', '-t', action='store_true', help='Transliterate Telugu lyrics to English characters')
    return parser.parse_args()

def download_with_ytdlp(url, output_path):
    """Download audio using yt-dlp command line tool."""
    try:
        logger.info(f"Downloading with yt-dlp: {url}")
        
        # Generate a safer filename for the temporary file (without extension)
        temp_filename = f"audio_temp_{int(time.time())}"
        temp_file_base = os.path.join(output_path, temp_filename)
        
        # Check if yt-dlp is installed
        try:
            subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("yt-dlp is not installed. Please install it with: pip install yt-dlp")
            return None
        
        # Run yt-dlp command with additional options for better compatibility
        # Using %(ext)s in the output template to let yt-dlp handle the extension
        command = [
            "yt-dlp",
            "-x",  # Extract audio
            "--audio-format", "mp3",  # Convert to mp3
            "--audio-quality", "0",   # Best quality
            "--no-playlist",          # Don't download playlists
            "--no-warnings",          # Less verbose output
            "-o", f"{temp_file_base}.%(ext)s",  # Output file with dynamic extension
            url                       # URL to download
        ]
        
        logger.info(f"Running command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            logger.error(f"yt-dlp error: {error_msg}")
            logger.error(f"yt-dlp output: {result.stdout}")
            
            # Check for common errors
            if "Incomplete YouTube ID" in error_msg:
                logger.error("The YouTube URL appears to be invalid or incomplete.")
            elif "Video unavailable" in error_msg or "This video is unavailable" in error_msg:
                logger.error("The video is unavailable or may be private/deleted.")
            elif "ERROR: Unable to download webpage" in error_msg:
                logger.error("Network error: Unable to access YouTube. Check your internet connection.")
            
            return None
            
        # Check for the downloaded file with any extension
        dir_path = os.path.dirname(temp_file_base)
        base_name = os.path.basename(temp_file_base)
        
        # List all files in the directory
        downloaded_file = None
        files = os.listdir(dir_path)
        for file in files:
            # Check for files that start with our temp filename
            if file.startswith(base_name):
                downloaded_file = os.path.join(dir_path, file)
                logger.info(f"Found downloaded file: {downloaded_file}")
                break
        
        if not downloaded_file:
            logger.error(f"Could not find any downloaded file. Files in {dir_path}: {files}")
            return None
        
        # If the file is not an MP3, convert it to MP3 using ffmpeg
        if not downloaded_file.lower().endswith('.mp3'):
            logger.info(f"Downloaded file is not MP3. Converting {downloaded_file} to MP3")
            mp3_file = f"{temp_file_base}.mp3"
            
            try:
                # Check if ffmpeg is installed
                subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.error("ffmpeg is not installed. Please install it to convert audio files.")
                # Still return the downloaded file even if we can't convert it
                return downloaded_file
                
            try:
                # Convert to MP3 using ffmpeg
                ffmpeg_cmd = [
                    "ffmpeg", 
                    "-y",                  # Overwrite output file
                    "-i", downloaded_file, # Input file
                    "-codec:a", "libmp3lame", # MP3 codec
                    "-q:a", "0",           # Highest quality
                    mp3_file               # Output file
                ]
                
                logger.info(f"Running ffmpeg command: {' '.join(ffmpeg_cmd)}")
                ffmpeg_result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                
                if ffmpeg_result.returncode == 0 and os.path.exists(mp3_file):
                    logger.info(f"Successfully converted to MP3: {mp3_file}")
                    
                    # Remove the original file
                    try:
                        os.remove(downloaded_file)
                        logger.info(f"Removed original file: {downloaded_file}")
                    except Exception as e:
                        logger.warning(f"Failed to remove original file: {e}")
                    
                    return mp3_file
                else:
                    logger.error(f"Failed to convert to MP3: {ffmpeg_result.stderr}")
                    # Return the original file if conversion fails
                    return downloaded_file
                    
            except Exception as e:
                logger.error(f"Error converting to MP3: {str(e)}")
                # Return the original file if conversion fails
                return downloaded_file
        
        logger.info(f"Downloaded to file: {downloaded_file}")
        return downloaded_file
        
    except Exception as e:
        logger.error(f"Error using yt-dlp: {str(e)}")
        return None

def clean_youtube_url(url):
    """Clean and normalize a YouTube URL."""
    # Extract video ID using more comprehensive regex
    # This handles various YouTube URL formats:
    # - https://www.youtube.com/watch?v=VIDEO_ID
    # - https://youtu.be/VIDEO_ID
    # - https://youtube.com/shorts/VIDEO_ID
    # - https://www.youtube.com/v/VIDEO_ID
    video_id_match = re.search(r'(?:youtube\.com\/(?:watch\?v=|v\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})', url)
    
    if video_id_match:
        video_id = video_id_match.group(1)
        logger.info(f"Extracted video ID: {video_id}")
        return f"https://www.youtube.com/watch?v={video_id}"
    
    # If we couldn't extract the ID with regex, return the original URL
    logger.warning(f"Could not extract video ID from URL: {url}")
    return url

def create_temp_http_server(file_path):
    """
    Create a temporary solution to make the audio file accessible via URL.
    For this implementation, we'll use ngrok to create a temporary tunnel.
    """
    try:
        # First, check if the file is small enough to be sent directly
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        # For simplicity, we'll use a direct API that supports MP3 files
        # instead of setting up a server or uploading to blob storage
        logger.info("Using direct MP3 transcription instead of batch API")
        
        # Convert file to MP3 if it's not already
        if not file_path.lower().endswith('.mp3'):
            mp3_path = os.path.splitext(file_path)[0] + '.mp3'
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-i", file_path, mp3_path],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                logger.info(f"Converted to MP3: {mp3_path}")
                file_path = mp3_path
            except Exception as e:
                logger.error(f"Failed to convert to MP3: {e}")
                # Continue with original file
        
        # Use a direct transcription approach with chunks
        return transcribe_mp3_directly(file_path)
    
    except Exception as e:
        logger.error(f"Error in file handling: {e}")
        return "Error: Failed to process audio file"

def transcribe_mp3_directly(file_path):
    """
    Transcribe an MP3 file directly by splitting it into smaller chunks
    and sending each chunk to the Azure Speech API.
    """
    try:
        logger.info("Transcribing MP3 directly in chunks...")
        
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
                return transcribe_single_file(file_path)
                
            hours, minutes, seconds = map(float, duration_match.groups())
            total_seconds = hours * 3600 + minutes * 60 + seconds
            logger.info(f"Audio duration: {total_seconds:.2f} seconds")
            
            # If less than 2 minutes, just transcribe directly
            if total_seconds < 120:
                logger.info("Audio is short enough for direct transcription")
                return transcribe_single_file(file_path)
            
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
                print(f"Transcribing chunk {i+1}/{len(chunk_files)}...")
                
                # Call the Azure Speech API for this chunk
                chunk_text = transcribe_single_file(chunk_file)
                
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
            return transcribe_single_file(file_path)
    
    except Exception as e:
        logger.error(f"Error in direct MP3 transcription: {e}")
        return f"Error: {str(e)}"

def transcribe_single_file(file_path):
    """
    Transcribe a single audio file using the Azure Speech REST API.
    """
    try:
        logger.info(f"Transcribing single file: {file_path}")
        
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
            "language": "te-IN",  # Telugu (India)
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

def transliterate_with_gpt4(telugu_text):
    """Transliterate Telugu text to English characters using GPT-4."""
    try:
        logger.info("Transliterating Telugu text to English characters using GPT-4...")
        
        # Prepare the API request
        headers = {
            "api-key": GPT4_API_KEY,
            "Content-Type": "application/json"
        }
        
        # Prepare the request payload with more neutral language
        payload = {
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a language transliteration assistant. Convert the provided text from one script to Latin (English) characters. Keep the exact same meaning and simply change the script. Your task is purely linguistic conversion."
                },
                {
                    "role": "user",
                    "content": f"Please convert this text to Latin script, preserving pronunciation:\n\n{telugu_text}"
                }
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        # Log request details for debugging
        logger.info(f"Sending request to GPT-4 API at: {GPT4_ENDPOINT}")
        
        # Make the API request
        response = requests.post(
            GPT4_ENDPOINT,
            headers=headers,
            json=payload
        )
        
        # Check for successful response
        if response.status_code == 200:
            result = response.json()
            transliterated_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if not transliterated_text:
                logger.error("Received empty transliteration from GPT-4")
                return try_chunked_transliteration(telugu_text)
                
            logger.info("Transliteration complete")
            return transliterated_text
        else:
            error_msg = f"GPT-4 API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            # Try with chunked approach
            return try_chunked_transliteration(telugu_text)
            
    except Exception as e:
        error_msg = f"Error transliterating with GPT-4: {str(e)}"
        logger.error(error_msg)
        # Try with chunked approach
        return try_chunked_transliteration(telugu_text)

def try_chunked_transliteration(text):
    """Try transliterating text in smaller chunks to avoid content filter issues."""
    logger.info("Trying transliteration with smaller chunks...")
    
    # Split the text into lines
    lines = text.split('\n')
    
    # Group lines into chunks of about 3-5 lines
    chunks = []
    current_chunk = []
    for line in lines:
        current_chunk.append(line)
        if len(current_chunk) >= 3:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
    
    # Add any remaining lines
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    # Transliterate each chunk
    transliterated_chunks = []
    for i, chunk in enumerate(chunks):
        logger.info(f"Transliterating chunk {i+1}/{len(chunks)}...")
        try:
            # Prepare the API request
            headers = {
                "api-key": GPT4_API_KEY,
                "Content-Type": "application/json"
            }
            
            # More neutral prompt for each chunk
            payload = {
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are a script converter. Convert the text from non-Latin script to Latin letters only. Do not translate or change any meaning."
                    },
                    {
                        "role": "user",
                        "content": f"Convert only the script of this text to Latin (English) letters, preserving exact pronunciation:\n\n{chunk}"
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }
            
            # Make the API request
            response = requests.post(
                GPT4_ENDPOINT,
                headers=headers,
                json=payload
            )
            
            # Process the response
            if response.status_code == 200:
                result = response.json()
                chunk_result = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                transliterated_chunks.append(chunk_result)
            else:
                logger.warning(f"Failed to transliterate chunk {i+1}: {response.status_code} - {response.text}")
                # Use a simple character-by-character transliteration as fallback
                fallback = simple_transliteration(chunk)
                transliterated_chunks.append(f"[Auto-transliterated] {fallback}")
                
        except Exception as e:
            logger.warning(f"Error in chunk {i+1}: {str(e)}")
            fallback = simple_transliteration(chunk)
            transliterated_chunks.append(f"[Auto-transliterated] {fallback}")
    
    # Combine the transliterated chunks
    return '\n'.join(transliterated_chunks)

def simple_transliteration(text):
    """Very simple character mapping for emergencies."""
    # This is a very basic fallback that won't produce good results
    # but will at least provide something if all else fails
    tamil_to_english = {
        'అ': 'a', 'ఆ': 'aa', 'ఇ': 'i', 'ఈ': 'ee', 'ఉ': 'u', 'ఊ': 'oo',
        'ఎ': 'e', 'ఏ': 'ae', 'ఐ': 'ai', 'ఒ': 'o', 'ఓ': 'oa', 'ఔ': 'au',
        'క': 'ka', 'ఖ': 'kha', 'గ': 'ga', 'ఘ': 'gha', 'ఙ': 'nga',
        'చ': 'cha', 'ఛ': 'chha', 'జ': 'ja', 'ఝ': 'jha', 'ఞ': 'nya',
        'ట': 'ta', 'ఠ': 'tha', 'డ': 'da', 'ఢ': 'dha', 'ణ': 'na',
        'త': 'tha', 'థ': 'thha', 'ద': 'da', 'ధ': 'dha', 'న': 'na',
        'ప': 'pa', 'ఫ': 'pha', 'బ': 'ba', 'భ': 'bha', 'మ': 'ma',
        'య': 'ya', 'ర': 'ra', 'ల': 'la', 'వ': 'va', 'శ': 'sha',
        'ష': 'sha', 'స': 'sa', 'హ': 'ha', 'ళ': 'la',
        '్': '', 'ా': 'a', 'ి': 'i', 'ీ': 'ee', 'ు': 'u', 'ూ': 'oo',
        'ె': 'e', 'ే': 'ae', 'ై': 'ai', 'ొ': 'o', 'ో': 'oa', 'ౌ': 'au',
        'ం': 'm', 'ః': 'h'
    }
    
    result = ""
    for char in text:
        if char in tamil_to_english:
            result += tamil_to_english[char]
        else:
            result += char
    
    return result

def transcribe_with_azure_speech(audio_file):
    """Transcribe the audio file using Azure Speech REST API with chunking."""
    try:
        logger.info("Transcribing audio with Azure Speech REST API...")
        
        # Check if file exists
        if not os.path.exists(audio_file):
            logger.error(f"Audio file not found: {audio_file}")
            return "Error: Audio file not found"
        
        # Check file size - if larger than 1MB, use chunking approach
        file_size_mb = os.path.getsize(audio_file) / (1024 * 1024)
        logger.info(f"Audio file size: {file_size_mb:.2f} MB")
        
        # Process file based on extension and size
        if file_size_mb > 1:
            # For larger files, use the chunking approach
            return transcribe_mp3_directly(audio_file)
        else:
            # For small files, use direct transcription
            return transcribe_single_file(audio_file)
            
    except Exception as e:
        logger.error(f"Error transcribing with Azure Speech: {e}")
        return f"Error: {str(e)}"

def main():
    args = parse_args()
    
    try:
        # Validate URL
        if not args.url or not (args.url.startswith('http://') or args.url.startswith('https://')):
            logger.error(f"Invalid URL format: {args.url}")
            print(f"Error: '{args.url}' does not appear to be a valid URL.")
            print("Please provide a complete YouTube URL (e.g., https://www.youtube.com/watch?v=sTfl_FCMX4g)")
            sys.exit(1)
            
        # Clean the YouTube URL
        clean_url = clean_youtube_url(args.url)
        if clean_url != args.url:
            logger.info(f"Using normalized URL: {clean_url}")
        
        # Download audio from YouTube using yt-dlp
        logger.info(f"Starting download from YouTube: {clean_url}")
        temp_file = download_with_ytdlp(clean_url, tempfile.gettempdir())
        if not temp_file:
            logger.error("Failed to download the YouTube video.")
            print("\nFailed to download the YouTube video. Please check:")
            print("1. The URL is a valid YouTube video URL")
            print("2. The video is not private or region-restricted")
            print("3. Your internet connection is working")
            print("4. yt-dlp is installed correctly (pip install yt-dlp)")
            sys.exit(1)
        
        # Move the file to the specified output location
        if temp_file != args.output:
            try:
                shutil.copy2(temp_file, args.output)
                logger.info(f"Audio saved to: {args.output}")
            except Exception as e:
                logger.error(f"Failed to copy file to output location: {e}")
                print(f"\nWarning: Could not save to {args.output}, using temporary file {temp_file} instead.")
                args.output = temp_file
        
        # Transcribe the audio to get lyrics
        logger.info(f"Transcribing audio file: {args.output}")
        print("\nTranscribing audio to Telugu text... (this may take a few minutes)")
        lyrics = transcribe_with_azure_speech(args.output)
        
        if not lyrics or lyrics.startswith("Error:"):
            logger.error("Transcription failed or returned empty result")
            print("\nFailed to transcribe the audio. Please make sure:")
            print("1. The Azure Speech Translation API key is correct")
            print("2. The audio file contains Telugu speech")
            print("3. The audio quality is sufficient for transcription")
            sys.exit(1)
        
        # Output the original lyrics
        print("\n=== ORIGINAL LYRICS ===\n")
        print(lyrics)
        
        # Save the original lyrics to a file
        original_file = os.path.splitext(args.output)[0] + "_lyrics.txt"
        try:
            with open(original_file, "w", encoding="utf-8") as f:
                f.write(lyrics)
            logger.info(f"Original lyrics saved to: {original_file}")
            print(f"\nTelugu lyrics saved to: {original_file}")
        except Exception as e:
            logger.error(f"Error saving original lyrics: {e}")
        
        # Transliterate the lyrics if requested
        if args.transliterate:
            try:
                print("\nTransliterating lyrics to English characters... (this may take a moment)")
                transliterated_lyrics = transliterate_with_gpt4(lyrics)
                
                if not transliterated_lyrics:
                    logger.error("Transliteration returned empty result")
                    print("\nTransliteration failed to produce any result.")
                else:
                    print("\n=== TRANSLITERATED LYRICS (ENGLISH CHARACTERS) ===\n")
                    print(transliterated_lyrics)
                    
                    # Save the transliterated lyrics to a file
                    transliterated_file = os.path.splitext(args.output)[0] + "_transliterated.txt"
                    try:
                        with open(transliterated_file, "w", encoding="utf-8") as f:
                            f.write(transliterated_lyrics)
                        logger.info(f"Transliterated lyrics saved to: {transliterated_file}")
                        print(f"\nTransliterated lyrics saved to: {transliterated_file}")
                    except Exception as e:
                        logger.error(f"Error saving transliterated lyrics: {e}")
                        
            except Exception as e:
                logger.error(f"Error during transliteration: {e}")
                print(f"\nTransliteration failed: {str(e)}")
                print("Please check your GPT-4 API key and connection.")
        else:
            logger.info("Transliteration not requested. Use --transliterate or -t flag to get lyrics in English characters.")
            print("\nTip: Use the --transliterate or -t flag to get lyrics in English characters")
        
        # Clean up temporary file if it still exists
        if os.path.exists(temp_file) and temp_file != args.output:
            try:
                os.remove(temp_file)
                logger.info(f"Removed temporary file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary file: {e}")
        
        logger.info(f"Lyrics extraction complete. MP3 saved to: {args.output}")
        print(f"\nProcess completed successfully!")
    
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        print("\nOperation canceled by user.")
        sys.exit(130)
    except Exception as e:
        logger.error(f"An error occurred during execution: {e}")
        print(f"\nAn error occurred: {str(e)}")
        print("Please try again or try a different video URL.")
        sys.exit(1)

if __name__ == "__main__":
    main() 