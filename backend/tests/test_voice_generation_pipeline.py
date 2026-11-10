import json
import base64
import io
import wave
from types import SimpleNamespace
from pathlib import Path

import httpx
import pytest

from backend.app.voice_agent.generation.contracts import GeneratedAnswer, GenerationInput
from backend.app.voice_agent.generation.fallback import GroundedFallback
from backend.app.voice_agent.generation.providers.gemini import GeminiResponseProvider
from backend.app.voice_agent.generation.providers.groq import GroqResponseProvider
from backend.app.voice_agent.generation.validator import model_safe_data, validate_answer
from backend.app.voice_agent.operations import VoiceOperations
from backend.app.voice_agent.adapters.gnani_tts import GnaniTimbreTTS
from backend.app.voice_agent.adapters.gnani_tts_stream import _voice_for
from backend.app.voice_agent.intent_router import IntentCategory, IntentRouter
from backend.app.voice_agent.react_agent import ReactAgent


def test_response_prompt_sets_grounding_and_untrusted_data_rules():
    prompt = (Path(__file__).parents[1] / "app/voice_agent/generation/prompts/response_synthesis_v1.txt").read_text(encoding="utf-8")
    assert "untrusted data" in prompt
    assert "Do not invent" in prompt
    assert "fact_refs" in prompt


def test_validator_requires_existing_fact_paths_and_numbers():
    facts = {"total_expense": 250.0}
    valid = GeneratedAnswer(answer="Spending was ₹250.00.", fact_refs=["$.total_expense"])
    invented = GeneratedAnswer(answer="Spending was ₹999.00.", fact_refs=["$.total_expense"])
    missing_path = GeneratedAnswer(answer="Spending was ₹250.00.", fact_refs=["$.balance"])
    assert validate_answer(valid, facts)
    assert not validate_answer(invented, facts)
    assert not validate_answer(missing_path, facts)


def test_model_payload_removes_private_evidence_fields():
    safe = model_safe_data({
        "amount": 250,
        "transaction_id": "private-id",
        "evidence": [{"account_reference": "private-account", "merchant": "Cafe"}],
        "items": [{"source_import_id": "private-import", "name": "Food"}],
    })
    assert safe == {"amount": 250, "items": [{"name": "Food"}]}


def test_fallback_reports_empty_period_without_a_zero_spend_claim():
    answer = GroundedFallback.compose(GenerationInput(
        query="How much did I spend?",
        tool_name="get_category_breakdown",
        tool_data={"status": "no_activity", "period": "Nov 2026"},
    ))
    assert "no matching financial activity" in answer.answer.lower()
    assert "₹0" not in answer.answer


def test_listen_to_me_is_routed_to_conversation_fast_path():
    result = IntentRouter.classify("Listen to me.")
    assert result.category == IntentCategory.GREETING_AND_META


@pytest.mark.asyncio
async def test_gemini_sse_adapter_parses_json_and_records_first_text_latency():
    chunks = [
        {"candidates": [{"content": {"parts": [{"text": '{"answer":"Spending was ₹250.00.",'}]}}]},
        {"candidates": [{"content": {"parts": [{"text": '"fact_refs":["$.total_expense"]}'}]}}]},
    ]
    body = "".join(f"data: {json.dumps(chunk)}\n\n" for chunk in chunks)
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text=body, headers={"content-type": "text/event-stream"}))
    provider = GeminiResponseProvider("test-key", "test-model", transport=transport)
    result = await provider.generate(GenerationInput(
        query="How much did I spend?",
        tool_name="get_category_breakdown",
        tool_data={"total_expense": 250.0},
    ))
    assert result is not None
    assert result.answer == "Spending was ₹250.00."
    assert result.fact_refs == ["$.total_expense"]
    assert result.provider_ttft_ms is not None


@pytest.mark.asyncio
async def test_groq_sse_adapter_uses_schema_stream_and_parses_grounded_answer():
    chunks = [
        {"choices": [{"delta": {"content": '{"answer":"Spending was ₹250.00.",'}}]},
        {"choices": [{"delta": {"content": '"fact_refs":["$.total_expense"]}'}}]},
    ]
    body = "".join(f"data: {json.dumps(chunk)}\n\n" for chunk in chunks) + "data: [DONE]\n\n"
    captured = {}

    def respond(request):
        captured["authorization"] = request.headers.get("authorization")
        captured["payload"] = json.loads(request.content)
        return httpx.Response(200, text=body, headers={"content-type": "text/event-stream"})

    provider = GroqResponseProvider("test-key", "openai/gpt-oss-120b", transport=httpx.MockTransport(respond))
    result = await provider.generate(GenerationInput(
        query="How much did I spend?",
        tool_name="get_category_breakdown",
        tool_data={"total_expense": 250.0},
    ))
    assert result is not None
    assert result.provider == "groq"
    assert result.model == "openai/gpt-oss-120b"
    assert result.fact_refs == ["$.total_expense"]
    assert result.provider_ttft_ms is not None
    assert captured["authorization"] == "Bearer test-key"
    assert captured["payload"]["stream"] is True
    assert captured["payload"]["response_format"]["json_schema"]["strict"] is True


@pytest.mark.asyncio
async def test_financial_voice_turn_streams_without_asyncio_scope_error():
    agent = ReactAgent()

    async def fake_dispatch(_db, _user_id, _classification, _query, _language):
        return {
            "tool_name": "get_category_breakdown",
            "tool_data": {"total_expense": 250.0, "categories": []},
            "quick_actions": [],
        }

    async def fake_compose(**_kwargs):
        return GeneratedAnswer(
            answer="Your spending was ₹250.",
            fact_refs=["$.total_expense"],
            provider="groq",
            model="openai/gpt-oss-120b",
            provider_ttft_ms=5,
            configured_provider="groq",
            provider_status="connected",
        )

    async def fake_audio_events(_text, _language, _voice):
        yield {"type": "audio.stream.start", "sample_rate": 48000}
        yield {
            "type": "audio.stream.end",
            "success": True,
            "chunks": 1,
            "first_audio_ms": 10,
            "total_ms": 20,
        }

    agent._dispatch_agent = fake_dispatch
    agent.response_composer = SimpleNamespace(compose=fake_compose)
    agent._stream_tts_events = fake_audio_events

    events = [event async for event in agent.execute_turn(
        db=None,
        user_id="test-user",
        query="Show my spending breakdown for this month",
        language="en",
        stream_audio=True,
    )]

    turn = next(event for event in events if event["type"] == "turn_complete")
    assert turn["text"] == "Your spending was ₹250."
    assert turn["metadata"]["generation_model"] == "openai/gpt-oss-120b"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("language", "voice", "expected_language", "expected_voice"),
    [
        ("en", "Nalini", "en-IN", "Kaveri"),
        ("hi", "Deepak", "hi-IN", "Deepak"),
        ("hinglish", "Deepak", "hi-en", "Poorvi"),
    ],
)
async def test_gnani_tts_uses_language_matched_voices_and_48khz_audio_config(
    language, voice, expected_language, expected_voice
):
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as generated:
        generated.setnchannels(1)
        generated.setsampwidth(2)
        generated.setframerate(48000)
        generated.writeframes(b"\x01\x00" * 512)
    expected_audio = wav_buffer.getvalue()
    captured = {}

    def respond(request):
        captured["payload"] = json.loads(request.content)
        captured["api_key_header"] = request.headers.get("X-API-Key-ID")
        return httpx.Response(200, content=expected_audio, headers={"content-type": "audio/wav"})

    adapter = GnaniTimbreTTS(
        api_key="test-key",
        transport=httpx.MockTransport(respond),
    )
    audio_base64 = await adapter.synthesize_speech("A short synthetic test sentence.", language, voice)
    payload = captured["payload"]
    assert captured["api_key_header"] == "test-key"
    assert payload["language"] == expected_language
    assert payload["voice"] == expected_voice
    assert payload["speed"] == 1.0
    assert payload["audio_config"] == {
        "sample_rate": 48000,
        "num_channels": 1,
        "sample_width": 2,
        "encoding": "linear_pcm",
        "container": "wav",
    }
    decoded = base64.b64decode(audio_base64)
    with wave.open(io.BytesIO(decoded), "rb") as returned:
        assert returned.getframerate() == 48000
        assert returned.getnchannels() == 1
        assert returned.getsampwidth() == 2


def test_voice_operations_records_real_trace_updates_and_scopes_users():
    operations = VoiceOperations(max_traces=10)
    operations.record({
        "trace_id": "trace-a",
        "user_id": "user-a",
        "latencies": {"tool_ms": 34},
        "provider_status": {"tts_status": "connected"},
        "playback_started": False,
        "end_to_first_audible_ms": None,
    })
    operations.mark_playback_started("trace-a", 612, "gnani_tts")
    operations.mark_interruption("trace-a", True)
    rows = operations.recent(10, "user-a")
    assert len(rows) == 1
    assert rows[0]["end_to_first_audible_ms"] == 612
    assert rows[0]["provider_status"]["playback"] == "gnani_tts"
    assert rows[0]["interruption_success"] is True
    assert operations.recent(10, "user-b") == []
    assert "query" not in rows[0]


def test_gnani_timbre_stream_maps_voice_and_language_together():
    assert _voice_for("en", "female") == ("en-IN", "Kaveri")
    assert _voice_for("hi", "male") == ("hi-IN", "Deepak")
    assert _voice_for("hinglish", "female") == ("hi-en", "Poorvi")


@pytest.mark.asyncio
async def test_voice_gateway_stream_events_forward_audio_chunks_and_measure_first_audio():
    agent = ReactAgent()

    async def fake_chunks(text, language, voice):
        assert text == "Synthetic reply"
        assert language == "en"
        assert voice == "female"
        yield b"\x01\x00" * 256
        yield b"\x02\x00" * 256

    agent.tts_stream.synthesize_chunks = fake_chunks
    events = [event async for event in agent._stream_tts_events("Synthetic reply", "en", "female")]
    assert events[0]["type"] == "audio.stream.start"
    chunks = [event for event in events if event["type"] == "audio.stream.chunk"]
    assert len(chunks) == 2
    assert [chunk["index"] for chunk in chunks] == [1, 2]
    assert all(base64.b64decode(chunk["audio"]) for chunk in chunks)
    ended = events[-1]
    assert ended["type"] == "audio.stream.end"
    assert ended["success"] is True
    assert ended["chunks"] == 2
    assert ended["first_audio_ms"] is not None
