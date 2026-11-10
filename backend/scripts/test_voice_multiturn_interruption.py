import asyncio
import json
import sys
import websockets

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

async def test_websocket_multiturn_and_interruption():
    uri = "ws://127.0.0.1:8000/ws/voice"
    print(f"Connecting to {uri}...")

    async with websockets.connect(uri, max_size=16 * 1024 * 1024) as ws:
        # Step 1: Wait for session.ready
        ready_msg = json.loads(await ws.recv())
        print(f"[WS Init] {ready_msg}")
        assert ready_msg["type"] == "session.ready"
        assert ready_msg["conversational_memory"] == "active"

        # Step 2: Turn 1 - Initial query
        print("\n--- TURN 1: 'Why did my spending increase by 8000?' ---")
        await ws.send(json.dumps({
            "type": "query",
            "query": "Why did my spending increase by 8000?",
            "language": "en"
        }))

        turn1_text = ""
        turn1_tool = ""
        while True:
            msg = json.loads(await ws.recv())
            mtype = msg.get("type")
            if mtype == "tool_calling":
                turn1_tool = msg.get("tool")
                print(f"  [Tool Calling]: {turn1_tool} - {msg.get('description')}")
            elif mtype == "text_token":
                sys.stdout.write(msg.get("token", ""))
                sys.stdout.flush()
            elif mtype == "turn_complete":
                turn1_text = msg.get("text", "")
                print(f"\n  [Turn 1 Complete Latencies]: {msg.get('latencies')}")
                break

        assert turn1_tool == "compare_periods"
        assert "8,200" in turn1_text

        # Step 3: Turn 2 - Contextual Follow-up with Pronoun: "Tell me more about the first one"
        print("\n--- TURN 2: 'Tell me more about the first one' (Pronoun Resolution) ---")
        await ws.send(json.dumps({
            "type": "query",
            "query": "Tell me more about the first one",
            "language": "en"
        }))

        turn2_text = ""
        turn2_tool = ""
        while True:
            msg = json.loads(await ws.recv())
            mtype = msg.get("type")
            if mtype == "tool_calling":
                turn2_tool = msg.get("tool")
                print(f"  [Tool Calling]: {turn2_tool} - {msg.get('description')}")
            elif mtype == "text_token":
                sys.stdout.write(msg.get("token", ""))
                sys.stdout.flush()
            elif mtype == "turn_complete":
                turn2_text = msg.get("text", "")
                print(f"\n  [Turn 2 Complete Latencies]: {msg.get('latencies')}")
                break

        print(f"\nTurn 2 Spoken Text: {turn2_text}")
        assert "Food & Dining" in turn2_text or "Swiggy" in turn2_text

        # Step 4: Turn 3 - Anomaly query: "Are there any suspicions in my spending"
        print("\n--- TURN 3: 'Are there any suspicions in my spending' ---")
        await ws.send(json.dumps({
            "type": "query",
            "query": "Are there any suspicions in my spending",
            "language": "en"
        }))

        turn3_text = ""
        turn3_tool = ""
        while True:
            msg = json.loads(await ws.recv())
            mtype = msg.get("type")
            if mtype == "tool_calling":
                turn3_tool = msg.get("tool")
                print(f"  [Tool Calling]: {turn3_tool} - {msg.get('description')}")
            elif mtype == "text_token":
                sys.stdout.write(msg.get("token", ""))
                sys.stdout.flush()
            elif mtype == "turn_complete":
                turn3_text = msg.get("text", "")
                print(f"\n  [Turn 3 Complete Latencies]: {msg.get('latencies')}")
                break

        assert turn3_tool == "find_unusual_transactions"
        assert any(w in turn3_text.lower() for w in ("anomal", "suspicio", "unusual", "croma"))
        print(f"\nTurn 3 Spoken Text: {turn3_text}")

        # Step 5: Turn 4 - Interruption handling (Barge-in cancellation)
        print("\n--- TURN 4: Barge-In Interruption Test ---")
        await ws.send(json.dumps({
            "type": "query",
            "query": "Give me a full breakdown of all my monthly expenses across categories",
            "language": "en"
        }))

        # Wait until first token is streamed
        first_tok = False
        while not first_tok:
            msg = json.loads(await ws.recv())
            if msg.get("type") == "text_token":
                print(f"\n  [Token received]: '{msg.get('token')}'. User interrupts now!")
                first_tok = True

        # Send barge-in cancel event
        await ws.send(json.dumps({"type": "turn.cancel"}))
        print("  [Sent]: turn.cancel")

        # Verify cancelled event received
        cancelled_ack = False
        while True:
            msg = json.loads(await ws.recv())
            mtype = msg.get("type")
            print(f"  [Post-cancel event]: {mtype}")
            if mtype == "interrupted":
                cancelled_ack = True
                print("  ✓ Barge-in interruption successfully acknowledged by backend!")
                break

        assert cancelled_ack is True
        print("\nAll Multi-Turn Memory & Barge-In tests PASSED successfully!")

if __name__ == "__main__":
    asyncio.run(test_websocket_multiturn_and_interruption())
