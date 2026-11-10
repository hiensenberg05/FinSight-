import httpx
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GNANI_API_KEY")
headers = {
    "X-API-Key-ID": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
}

tests = [
    {"text": "Hello Aarav, your finances look solid today.", "language": "en", "voice": "Nalini"},
    {"text": "Hello Aarav, your finances look solid today.", "language": "en", "voice": "Deepak"},
    {"text": "नमस्ते आरव, आपका खर्च इस महीने नियंत्रण में है।", "language": "hi", "voice": "Nalini"},
    {"text": "नमस्ते आरव, आपका खर्च इस महीने नियंत्रण में है।", "language": "hi", "voice": "Deepak"},
    {"text": "Namaste Aarav, aapka kharcha control me hai.", "language": "hi", "voice": "Nalini"},
]

with httpx.Client(timeout=10.0) as client:
    for t in tests:
        payload = {
            "model": "timbre-v2.5",
            "text": t["text"],
            "language": t["language"],
            "voice": t["voice"],
            "audio_format": "wav",
        }
        try:
            r = client.post("https://api.vachana.ai/api/v1/tts/inference", headers=headers, json=payload)
            print(f"Voice={t['voice']} Lang={t['language']} Text='{t['text'][:30]}...' -> Status={r.status_code} Bytes={len(r.content)}")
        except Exception as e:
            print(f"Error for {t['voice']} ({t['language']}): {e}")
