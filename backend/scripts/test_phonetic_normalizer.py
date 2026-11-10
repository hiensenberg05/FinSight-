import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

def clean_for_voice(text: str, language: str = "en") -> str:
    if not text:
        return ""
    # Strip markdown table rows
    cleaned = re.sub(r"\|[^\n]+\|", " ", text)
    cleaned = re.sub(r"\|", " ", cleaned)
    # Strip markdown formatting
    cleaned = re.sub(r"[*#_`~\[\]]", "", cleaned)
    cleaned = re.sub(r"\((?:https?://|file://)[^\)]*\)", "", cleaned)
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    cleaned = re.sub(r"[-=]{3,}", " ", cleaned)

    # Phonetic normalizations for TTS with strict word boundaries
    if language in ("hi", "hinglish"):
        # Convert ₹ or Rs to रुपये
        cleaned = re.sub(r"(?:₹|(?:\b(?:rs\.?|inr)\b))\s*(\d[\d,]*(?:\.\d+)?)", lambda m: f"{m.group(1).replace(',', '')} रुपये", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"(\d+)%", r"\1 प्रतिशत", cleaned)
    else:
        # Convert ₹ or Rs to rupees
        cleaned = re.sub(r"(?:₹|(?:\b(?:rs\.?|inr)\b))\s*(\d[\d,]*(?:\.\d+)?)", lambda m: f"{m.group(1).replace(',', '')} rupees", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"(\d+)%", r"\1 percent", cleaned)

    # Remove lingering commas within digit sequences to avoid "one comma zero two"
    cleaned = re.sub(r"(?<=\d),(?=\d)", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

def split_sentences_for_tts(text: str) -> list[str]:
    if not text:
        return []
    raw_sentences = re.split(r"(?<=[.!?।])\s+(?=[A-Za-z0-9\u0900-\u097F])|\n+", text)
    return [s.strip() for s in raw_sentences if s.strip()]

t_en = "Your verified balance is ₹1,02,756 across SBI and HDFC. This covers 4.9 months of fixed commitments of ₹21,149."
c_en = clean_for_voice(t_en, "en")
s_en = split_sentences_for_tts(c_en)
print("EN Cleaned:", c_en)
print("EN Sentences:", s_en)

t_hi = "आपका कुल बैलेंस ₹1,02,756 है। यह आपके ₹21,149 के बिलों को 4.9 महीनों तक कवर करता है।"
c_hi = clean_for_voice(t_hi, "hi")
s_hi = split_sentences_for_tts(c_hi)
print("HI Cleaned:", c_hi)
print("HI Sentences:", s_hi)
