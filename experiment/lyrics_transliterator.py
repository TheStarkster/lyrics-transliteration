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
        if is_segmented:
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
            timeout=30
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
                    return {
                        "success": True,
                        "segments": args.get("segments", []),
                        "skipped_words": args.get("skipped_words", [])
                    }
                else:
                    return {
                        "success": True,
                        "transliterated_text": args.get("transliterated_text", ""),
                        "skipped_words": args.get("skipped_words", [])
                    }
        
        print("Transliteration error: Unexpected API response format")
        return {"success": False, "error": "Unexpected API response format"}
                
    except Exception as e:
        print(f"Transliteration exception: {str(e)}")
        return {"success": False, "error": str(e)}

def chunk_segments(segments: List[Dict[str, Any]], chunk_size: int = 5) -> List[List[Dict[str, Any]]]:
    for i in range(0, len(segments), chunk_size):
        yield segments[i:i + chunk_size]

def add_transliteration(transcription_result: Dict[str, Any], language: str) -> Dict[str, Any]:
    result_with_transliteration = copy.deepcopy(transcription_result)

    if (not validate_azure_openai_key() or 
        "segments" not in transcription_result or 
        not transcription_result.get("segments") or
        language not in SUPPORTED_LANGUAGES):
        return result_with_transliteration
    
    original_segments = transcription_result["segments"]
    transliterated_segments = []

    for segment_chunk in chunk_segments(original_segments, chunk_size=5):
        chunk_text = "###SEGMENT###".join([seg["text"] for seg in segment_chunk if seg.get("text")])
        if not chunk_text.strip():
            continue

        result = transliterate_with_function_calling(chunk_text, language, is_segmented=True)
        if result.get("success") and "segments" in result:
            for i, segment in enumerate(segment_chunk):
                if i < len(result["segments"]):
                    translit_segment = copy.deepcopy(segment)
                    translit_segment["text"] = result["segments"][i]["transliterated"]
                    transliterated_segments.append(translit_segment)
        else:
            # If transliteration fails, just add original segments to maintain consistency
            transliterated_segments.extend(segment_chunk)

        result_with_transliteration["transliterated_segments"] = transliterated_segments
        result_with_transliteration["transliterated_segments"] = transliterated_segments
    
    result_with_transliteration["transliterated_segments"] = transliterated_segments
    
    return result_with_transliteration

