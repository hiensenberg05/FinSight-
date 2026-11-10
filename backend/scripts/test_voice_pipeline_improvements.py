import sys
import os
import asyncio
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.stdout.reconfigure(encoding='utf-8')

from backend.app.voice_agent.voice_prompts import split_sentences_for_tts, VoiceSpeechPrompter
from backend.app.voice_agent.generation.stream_guardrail import StreamGuardrail
from backend.app.voice_agent.operations import voice_operations

def test_sentence_splitting():
    print("--- 1. Testing Sentence Splitting for Low-Latency TTS Pipelining ---")
    en_text = (
        "Your verified balance is 102756 rupees across SBI and HDFC. "
        "This covers 4.9 months of fixed commitments. "
        "Would you like to review your upcoming bills?"
    )
    en_sentences = split_sentences_for_tts(en_text)
    print("EN Sentences Count:", len(en_sentences))
    for idx, s in enumerate(en_sentences, 1):
        print(f"  Sentence {idx}: {s}")
    assert len(en_sentences) == 3, f"Expected 3 sentences, got {len(en_sentences)}"
    assert "4.9" in en_sentences[1], "Decimal 4.9 must not be split"

    hi_text = (
        "आपका कुल बैलेंस 102756 रुपये है। "
        "यह आपके 21149 रुपये के खर्चों को 4.9 महीनों तक कवर करता है। "
        "क्या आप पिछले महीने का खर्च देखना चाहते हैं?"
    )
    hi_sentences = split_sentences_for_tts(hi_text)
    print("HI Sentences Count:", len(hi_sentences))
    for idx, s in enumerate(hi_sentences, 1):
        print(f"  Sentence {idx}: {s}")
    assert len(hi_sentences) == 3, f"Expected 3 sentences, got {len(hi_sentences)}"
    assert "4.9" in hi_sentences[1], "Decimal 4.9 must not be split in Hindi"
    print("Sentence splitting: [PASS]")

def test_phonetic_normalization():
    print("\n--- 2. Testing Phonetic Normalization (Anti-Stutter & Code-Switch) ---")
    raw_en = "Your balance is ₹1,02,756 across SBI. Rent is ₹18,000, and dining increased by 56%."
    cleaned_en = StreamGuardrail.clean_text_for_tts(raw_en, language="en")
    print("Raw EN:    ", raw_en)
    print("Cleaned EN:", cleaned_en)
    assert "102756 rupees" in cleaned_en, "Expected '102756 rupees' without internal commas"
    assert "18000 rupees" in cleaned_en, "Expected '18000 rupees'"
    assert "56 percent" in cleaned_en, "Expected '56 percent'"
    assert "covers" not in cleaned_en  # Check that "rs" in other words isn't falsely created

    raw_hi = "आपका बैलेंस ₹1,02,756 है और फूड पर ₹30,563 खर्च हुआ, जो बजट से 91% ज्यादा है।"
    cleaned_hi = StreamGuardrail.clean_text_for_tts(raw_hi, language="hi")
    print("Raw HI:    ", raw_hi)
    print("Cleaned HI:", cleaned_hi)
    assert "102756 रुपये" in cleaned_hi, "Expected '102756 रुपये'"
    assert "30563 रुपये" in cleaned_hi, "Expected '30563 रुपये'"
    assert "91 प्रतिशत" in cleaned_hi, "Expected '91 प्रतिशत'"
    print("Phonetic normalization: [PASS]")

def test_voice_operations_interruption():
    print("\n--- 3. Testing Voice Operations Barge-In Telemetry ---")
    trace_id = "test-trace-bargein-001"
    voice_operations.record({
        "trace_id": trace_id,
        "user_id": "test_user_aarav",
        "session_id": "test_session",
        "latencies": {"generation_ttft_ms": 280, "tts_first_audio_ms": 320},
        "provider_status": {"tts_status": "connected"},
    })
    # Mark barge-in with 42ms cutoff latency
    voice_operations.mark_interruption(trace_id, succeeded=True, latency_ms=42)
    recent = voice_operations.recent(limit=5)
    matched = [t for t in recent if t["trace_id"] == trace_id]
    assert len(matched) == 1, "Trace should be recorded"
    trace = matched[0]
    print("Recorded Trace Interruption:", trace.get("interruption_success"))
    print("Recorded Barge-in Latency:  ", trace.get("barge_in_latency_ms"), "ms")
    assert trace.get("interruption_success") is True
    assert trace.get("barge_in_latency_ms") == 42
    print("Voice operations telemetry: [PASS]")

if __name__ == "__main__":
    test_sentence_splitting()
    test_phonetic_normalization()
    test_voice_operations_interruption()
    print("\n=======================================================")
    print("ALL VOICE PIPELINE IMPROVEMENT TESTS PASSED (100%)")
    print("=======================================================")
