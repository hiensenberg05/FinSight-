"""
Test WebSocket Voice Gateway: streaming tokens, tool calling, and barge-in interruption.
"""

import asyncio
import json
import sys
import websockets

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


async def test_ws_voice():
    uri = "ws://127.0.0.1:8000/ws/voice"
    print(f"Connecting to {uri}...")

    async with websockets.connect(uri, max_size=16 * 1024 * 1024) as ws:
        ready = await ws.recv()
        print(f"Received: {ready}")

        # Send test query
        query = {"type": "query", "query": "Why did my spending increase?"}
        print(f"Sending query: {query}")
        await ws.send(json.dumps(query))

        tokens_received = []
        tool_calling_received = False
        tool_result_received = False
        latencies = None

        while True:
            raw = await ws.recv()
            evt = json.loads(raw)
            evt_type = evt.get("type")

            if evt_type == "tool_calling":
                tool_calling_received = True
                print(f"  [AGENTIC EVENT] Tool Calling -> {evt['tool']} with args: {evt.get('args')}")
            elif evt_type == "tool_result":
                tool_result_received = True
                print(f"  [AGENTIC EVENT] Tool Result -> {evt['tool']} computed in {evt['duration_ms']}ms")
            elif evt_type == "text_token":
                tokens_received.append(evt["token"])
                print(evt["token"], end="", flush=True)
            elif evt_type == "turn_complete":
                latencies = evt.get("latencies")
                print(f"\n  [TURN COMPLETE] Latency Breakdown:")
                for k, v in latencies.items():
                    print(f"    - {k}: {v}ms")
                break

        assert tool_calling_received, "Failed to receive tool_calling event"
        assert tool_result_received, "Failed to receive tool_result event"
        assert len(tokens_received) > 0, "Failed to receive text tokens"
        print("\n--> Token streaming and tool-calling verified successfully!")

        # Test Interruption / Barge-in
        print("\nTesting Interruption (Barge-in)...")
        await ws.send(json.dumps({"type": "query", "query": "What bills are due this month?"}))
        # Wait for first token
        tok = await ws.recv()
        print(f"  Received event: {json.loads(tok).get('type')}")
        # Send cancel
        print("  Sending interruption turn.cancel...")
        await ws.send(json.dumps({"type": "turn.cancel"}))

        # Expect interrupted message
        int_resp = await ws.recv()
        int_data = json.loads(int_resp)
        print(f"  Interruption response: {int_data}")
        assert int_data.get("type") == "interrupted", "Expected interrupted event!"
        print("--> Interruption handling (barge-in) verified successfully!")


if __name__ == "__main__":
    asyncio.run(test_ws_voice())
