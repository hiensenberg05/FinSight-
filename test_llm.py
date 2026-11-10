import os
import httpx
import asyncio
from backend.app.core.config import settings

async def main():
    key = os.getenv("GOOGLE_API_KEY") or settings.GEMINI_API_KEY
    print("API Key configured:", bool(key), "length:", len(key) if key else 0)
    if not key:
        return
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    payload = {
        "contents": [{"parts": [{"text": "Hello, give a 1-sentence financial greeting for Aarav Mehta."}]}]
    }
    async with httpx.AsyncClient(timeout=6.0) as client:
        res = await client.post(url, json=payload)
        print("Status Code:", res.status_code)
        if res.status_code == 200:
            text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
            print("Response:", text.strip())
        else:
            print("Error body:", res.text[:200])

if __name__ == "__main__":
    asyncio.run(main())
