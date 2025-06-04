import requests
import uuid
import json

AZURE_TRANSLATOR_ENDPOINT = "https://api.cognitive.microsofttranslator.com"
AZURE_TRANSLATOR_LOCATION = "centralindia"
AZURE_TRANSLATOR_KEY = "B03R6qIW4PKOxz9hlYwHT7TlBqjUboLbk3tNub2UpkEg70PRB0H8JQQJ99BFACGhslBXJ3w3AAAbACOG3Uw6"

def transliterate_telugu_to_english(text_list):
    path = '/transliterate'
    params = {
        'api-version': '3.0',
        'language': 'te',
        'fromScript': 'Telu',
        'toScript': 'Latn'
    }
    constructed_url = AZURE_TRANSLATOR_ENDPOINT + path

    headers = {
        'Ocp-Apim-Subscription-Key': AZURE_TRANSLATOR_KEY,
        'Ocp-Apim-Subscription-Region': AZURE_TRANSLATOR_LOCATION,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    body = [{'Text': text} for text in text_list]

    response = requests.post(constructed_url, params=params, headers=headers, json=body)
    response.raise_for_status()
    results = response.json()

    for original, item in zip(text_list, results):
        print(f"Original: {original} → Transliteration: {item['text']}")

# Example Telugu text
telugu_texts = [
    "తెలుగు",
    "నమస్తే",
    "విజయవాడ",
    "అనుపమ"
]

transliterate_telugu_to_english(telugu_texts)
