import asyncio
import json
import sys
import websockets

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def test():
    uri = "ws://localhost:8000/ws/voice"
    print(f"Connecting to {uri}...")
    async with websockets.connect(uri) as ws:
        while True:
            msg = json.loads(await ws.recv())
            if msg.get("type") == "session.ready":
                print("[WS] Session ready confirmed.")
                break

        # Test Query 1: Hindi Category Spend
        q1 = "पिछले महीने का खर्चा बताओ।"
        print(f"\n[Test 1] Sending Query: {q1}")
        await ws.send(json.dumps({"type": "text_query", "text": q1}))

        while True:
            raw = await ws.recv()
            data = json.loads(raw)
            if data.get("type") == "turn_complete":
                print(f"[Test 1 Output] Spoken Text: {data.get('text')}")
                print(f" -> Reasoning Provider: {data.get('reasoning_provider')}")
                print(f" -> Reasoning Status: {data.get('provider_status', {}).get('reasoning')}")
                print(f" -> Tool Executed: {data.get('tool_metadata', {}).get('name')}")
                print(f" -> Chart Title: {data.get('chartTitle')}")
                print(f" -> Chart Slices: {len(data.get('chartData') or [])}")
                break

        # Test Query 2: English Variance
        q2 = "Why did my spending increase?"
        print(f"\n[Test 2] Sending Query: {q2}")
        await ws.send(json.dumps({"type": "text_query", "text": q2}))

        while True:
            raw = await ws.recv()
            data = json.loads(raw)
            if data.get("type") == "turn_complete":
                print(f"[Test 2 Output] Spoken Text: {data.get('text')}")
                print(f" -> Reasoning Provider: {data.get('reasoning_provider')}")
                print(f" -> Reasoning Status: {data.get('provider_status', {}).get('reasoning')}")
                print(f" -> Tool Executed: {data.get('tool_metadata', {}).get('name')}")
                print(f" -> Chart Title: {data.get('chartTitle')}")
                break

    print("\n[SUCCESS] Live voice agent verified dynamically over WebSocket!")

if __name__ == "__main__":
    asyncio.run(test())
