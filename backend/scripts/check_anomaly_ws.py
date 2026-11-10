import asyncio
import json
import websockets

async def check():
    async with websockets.connect("ws://localhost:8000/ws/voice", max_size=16*1024*1024) as ws:
        await ws.recv() # session.ready
        await ws.send(json.dumps({
            "type": "text_query",
            "text": "Are there any unusual or suspicious transactions in my account?"
        }))
        while True:
            raw = await ws.recv()
            data = json.loads(raw)
            if data.get("type") == "turn_complete":
                ev = data.get("evidence", [])
                print(f"EVIDENCE_COUNT={len(ev)}")
                if ev:
                    print(f"FIRST_EV={ev[0].get('merchant')} | {ev[0].get('amount_formatted')} | {ev[0].get('account_reference')}")
                break

if __name__ == "__main__":
    asyncio.run(check())
