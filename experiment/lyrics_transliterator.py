import os
import requests
from typing import Dict, List, Any, Optional
import copy

# Constants for Azure OpenAI
AZURE_OPENAI_ENDPOINT = (
    "https://scout-llm-2.openai.azure.com/"
    "openai/deployments/gpt-4o/chat/completions?api-version=2024-05-01-preview"
)
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "c1b98148632f4133a5f5aa1146f640ed")

# Supported languages
SUPPORTED_LANGUAGES = ["hi", "te"]

def validate_azure_openai_key() -> bool:
    """Validate the Azure OpenAI API key by making a small test request"""
    if not AZURE_OPENAI_KEY:
        print("Azure OpenAI API key is not set")
        return False
        
    try:
        response = requests.post(
            AZURE_OPENAI_ENDPOINT,
            headers={
                "api-key": AZURE_OPENAI_KEY,
                "Content-Type": "application/json"
            },
            json={
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello"}
                ],
                "max_tokens": 5,
                "temperature": 0.0
            },
            timeout=5
        )
        
        return response.status_code == 200
            
    except Exception as e:
        print(f"Error validating Azure OpenAI API key: {str(e)}")
        return False

def transliterate_with_function_calling(text: str, language: str, is_segmented: bool = False) -> Dict[str, Any]:
    """
    Transliterate text using Azure OpenAI with function calling.
    
    This uses a single API call to transliterate the entire text and handles
    problematic words by instructing the model to skip words it's unsure about.
    
    Args:
        text: The text to transliterate
        language: The source language code (e.g., "hi", "te")
        is_segmented: Whether the text contains multiple segments separated by special markers
        
    Returns:
        Dictionary with transliterated text
    """
    if not AZURE_OPENAI_KEY or not text or language not in SUPPORTED_LANGUAGES:
        error_msg = "Invalid input or API key"
        print(f"Transliteration error: {error_msg}")
        return {"success": False, "error": error_msg}
    
    language_names = {
        "hi": "Hindi",
        "te": "Telugu"
    }
    
    language_name = language_names.get(language, language)
    
    try:
        # Function spec for transliteration
        if is_segmented:
            # Use a function that explicitly handles segments
            functions = [
                {
                    "name": "transliterate_segments",
                    "description": f"Transliterate {language_name} text segments to Latin (English) script",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "segments": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "original": {
                                            "type": "string",
                                            "description": "The original segment text"
                                        },
                                        "transliterated": {
                                            "type": "string",
                                            "description": f"The {language_name} text transliterated to Latin script, preserving pronunciation"
                                        }
                                    }
                                },
                                "description": "Array of segments with their transliterations"
                            },
                            "skipped_words": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "Words that couldn't be transliterated reliably"
                            }
                        },
                        "required": ["segments"]
                    }
                }
            ]
            
            # Split the input text into segments
            segments = [segment.strip() for segment in text.split("###SEGMENT###") if segment.strip()]
            
            system_prompt = (
                f"You are a transliteration expert. Convert each {language_name} text segment to "
                "Latin (English) script. Each segment is separated by the marker ###SEGMENT###. "
                "For each segment, provide the transliteration that maintains pronunciation accurately. "
                "Keep the exact same number of segments in your response. "
                "If you're unsure about any words, include them in the skipped_words list."
            )
            
            function_name = "transliterate_segments"
            
        else:
            # Use the original single-text function
            functions = [
                {
                    "name": "transliterate_text",
                    "description": f"Transliterate {language_name} text to Latin (English) script",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "transliterated_text": {
                                "type": "string",
                                "description": f"The {language_name} text transliterated to Latin script, preserving pronunciation"
                            },
                            "skipped_words": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "Words that couldn't be transliterated reliably"
                            }
                        },
                        "required": ["transliterated_text"]
                    }
                }
            ]
            
            system_prompt = (
                f"You are a transliteration expert. Convert the following {language_name} text to "
                "Latin (English) script. Maintain the pronunciation accurately. "
                "If you're unsure about any words, include them in the skipped_words list."
            )
            
            function_name = "transliterate_text"
        
        # Send the request
        response = requests.post(
            AZURE_OPENAI_ENDPOINT,
            headers={
                "api-key": AZURE_OPENAI_KEY,
                "Content-Type": "application/json"
            },
            json={
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                "temperature": 0.3,
                "functions": functions,
                "function_call": {"name": function_name}
            },
            timeout=15
        )
        
        response.raise_for_status()
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            function_call = result["choices"][0]["message"].get("function_call", {})
            if function_call and "arguments" in function_call:
                import json
                args = json.loads(function_call["arguments"])
                print(f"Transliteration successful for {language_name} text")
                
                if is_segmented:
                    # Return segment-specific format
                    return {
                        "success": True,
                        "segments": args.get("segments", []),
                        "skipped_words": args.get("skipped_words", [])
                    }
                else:
                    # Return original format
                    return {
                        "success": True,
                        "transliterated_text": args.get("transliterated_text", ""),
                        "skipped_words": args.get("skipped_words", [])
                    }
        
        error_msg = "Unexpected API response format"
        print(f"Transliteration error: {error_msg}")
        return {"success": False, "error": error_msg}
                
    except Exception as e:
        error_msg = str(e)
        print(f"Transliteration exception: {error_msg}")
        return {"success": False, "error": error_msg}

def add_transliteration(transcription_result: Dict[str, Any], language: str) -> Dict[str, Any]:
    """
    Add transliteration to transcription results, processing the segments array.
    
    Args:
        transcription_result: Dict containing 'text' and 'segments' where segments is an array of
                              objects with 'id', 'text', 'start', and 'end' properties
        language: The source language code (e.g., "hi", "te")
        
    Returns:
        Dictionary with transliterated_segments that mirror the structure of segments
    """
    # Make a deep copy to avoid modifying the original
    result_with_transliteration = copy.deepcopy(transcription_result)
    
    # Validate inputs
    if (not validate_azure_openai_key() or 
        "segments" not in transcription_result or 
        not transcription_result.get("segments") or
        language not in SUPPORTED_LANGUAGES):
        return result_with_transliteration
    
    # Extract segments
    segments = transcription_result["segments"]

    # Create a segmented text with clear markers
    segmented_text = ""
    for segment in segments:
        if segment.get("text"):
            segmented_text += f"{segment['text']}###SEGMENT###"
    

    if not segmented_text.strip():
        return result_with_transliteration
    
    # Transliterate all segments in one call with the segmented flag
    transliteration_result = transliterate_with_function_calling(segmented_text, language, is_segmented=True)
    
    if transliteration_result.get("success", False) and "segments" in transliteration_result:
        # Process each segment with its transliteration
        segment_results = transliteration_result["segments"]
        
        # Create a new array for transliterated segments that matches the original structure
        transliterated_segments = []
        
        # Verify we have the same number of segments
        if len(segment_results) != len(result_with_transliteration["segments"]):
            print(f"Warning: Received {len(segment_results)} transliterated segments but expected {len(result_with_transliteration['segments'])}")
            
        # Create transliterated_segments with same structure as segments
        for i, segment in enumerate(segments):
            if i < len(segment_results):
                # Create a new segment with the same structure but transliterated text
                transliterated_segment = copy.deepcopy(segment)
                transliterated_segment["text"] = segment_results[i]["transliterated"]
                transliterated_segments.append(transliterated_segment)
        
        # Add the transliterated segments to the result
        result_with_transliteration["transliterated_segments"] = transliterated_segments
    
    return result_with_transliteration 