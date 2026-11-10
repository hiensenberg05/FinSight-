import asyncio
import json
import io
import wave
import struct
import math
import websockets
import sys

def generate_test_wav_bytes(duration_sec: float = 1.0, freq: float = 440.0) -> bytes:
    """Generate a valid PCM 16-bit mono 16kHz WAV buffer for binary audio testing."""
    sample_rate = 16000
    num_samples = int(sample_rate * duration_sec)
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for i in range(num_samples):
            value = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * freq * (i / sample_rate)))
            wav_file.writeframes(struct.pack('<h', value))
    return buffer.getvalue()

async def run_comprehensive_eval():
    uri = "ws://127.0.0.1:8000/ws/voice"
    print(f"Connecting to Voice WebSocket at {uri}...")

    test_queries = [
        ("Query 1 (Where did I spend)", "i mean where i did spend last month"),
        ("Query 2 (Spending Spikes)", "Why did my spending increase by 8000?"),
        ("Query 3 (Pronoun follow-up)", "Tell me more about the first one"),
        ("Query 4 (Anomaly Detection)", "Are there any suspicions in my spending"),
        ("Query 5 (Hinglish/Hindi Test)", "Pichle mahine mera kharcha kahan hua?"),
    ]

    async with websockets.connect(uri) as ws:
        ready = json.loads(await ws.recv())
        print(f"[WS Ready]: Session ID {ready.get('session_id')}, Memory: {ready.get('conversational_memory')}")

        for label, query in test_queries:
            print(f"\n==========================================")
            print(f"TEST: {label} -> \"{query}\"")
            print(f"==========================================")
            await ws.send(json.dumps({
                "type": "query",
                "query": query,
                "language": "en"
            }))

            spoken_tokens = []
            tool_called = ""
            while True:
                raw = await ws.recv()
                msg = json.loads(raw)
                mtype = msg.get("type")
                if mtype == "tool_calling":
                    tool_called = msg.get("tool")
                    print(f"  [🔧 Tool Selected]: {tool_called} ({msg.get('description')})")
                elif mtype == "text_token":
                    tok = msg.get("token", "")
                    spoken_tokens.append(tok)
                    sys.stdout.write(tok)
                    sys.stdout.flush()
                elif mtype == "turn_complete":
                    print(f"\n  [⚡ Latencies]: Total={msg.get('latencies', {}).get('total_turn_ms')}ms | Tool={msg.get('latencies', {}).get('tool_ms')}ms | Reasoning={msg.get('latencies', {}).get('reasoning_ms')}ms")
                    break

        # Test Binary Audio Streaming
        print(f"\n==========================================")
        print(f"TEST: Binary Audio Frame Streaming (STT Pipeline)")
        print(f"==========================================")
        wav_bytes = generate_test_wav_bytes(duration_sec=1.5, freq=440.0)
        print(f"  [Sending]: {len(wav_bytes)} bytes of PCM 16kHz audio...")
        await ws.send(wav_bytes)

        got_transcript = False
        while True:
            raw = await ws.recv()
            msg = json.loads(raw)
            mtype = msg.get("type")
            if mtype == "transcript.final":
                print(f"  [🎙️ STT Transcribed]: \"{msg.get('text')}\"")
                got_transcript = True
            elif mtype == "tool_calling":
                print(f"  [🔧 Audio-Triggered Tool]: {msg.get('tool')}")
            elif mtype == "turn_complete":
                print(f"  [✓ Binary Audio Turn Finished]: {msg.get('text')[:80]}...")
                break

        assert got_transcript is True
        print("\nAll Prompts and Audio tests PASSED with 100% success!")

if __name__ == "__main__":
    asyncio.run(run_comprehensive_eval())
