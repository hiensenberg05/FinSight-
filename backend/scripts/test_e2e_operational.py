import sys
import asyncio
import json
import websockets
import httpx

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BACKEND_WS = "ws://localhost:8000/ws/voice"
BACKEND_HTTP = "http://localhost:8000/api/v1"

async def test_e2e_operational_flows():
    print("--- Starting FinSight End-to-End Operational Flow Verification ---")
    
    async with websockets.connect(BACKEND_WS, max_size=16 * 1024 * 1024) as ws:
        print("[WS] Connected to", BACKEND_WS)
        
        # 1. Receive initial welcome / proactive alerts on connection
        init_msgs = []
        try:
            while True:
                msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                data = json.loads(msg)
                init_msgs.append(data)
                print(f"[WS Init Message] type={data.get('type')}")
                if data.get("type") == "proactive_alert":
                    print(f" -> Received Sentinel alert: [{data.get('severity')}] {data.get('title')}: {data.get('detail')}")
        except asyncio.TimeoutError:
            pass

        # 2. Test Provenance Flow: "Why did my spending increase in February?"
        print("\n--- Test 1: Provenance & Grounding ('Why did my spending increase in February?') ---")
        await ws.send(json.dumps({
            "type": "text_query",
            "text": "Why did my spending increase in February?"
        }))
        
        stages_received = []
        turn_complete_data = None
        
        while True:
            raw_msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
            msg = json.loads(raw_msg)
            msg_type = msg.get("type")
            
            if msg_type == "execution_stage":
                stages_received.append(msg.get("stage"))
                print(f" [Execution Stage] {msg.get('stage')}: {msg.get('label')}")
            elif msg_type == "turn_complete":
                turn_complete_data = msg
                print(" [Turn Complete] Received final turn!")
                break
        
        assert "fetching_financial_data" in stages_received, "Missing fetching_financial_data stage!"
        assert "preparing_spoken_response" in stages_received, "Missing preparing_spoken_response stage!"
        
        evidence = turn_complete_data.get("evidence", [])
        print(f" -> Attached Evidence Count: {len(evidence)}")
        assert len(evidence) > 0, "Expected transaction evidence!"
        first_ev = evidence[0]
        print(f" -> Sample Evidence Item: txn_id={first_ev.get('transaction_id')}, merchant={first_ev.get('merchant')}, amount={first_ev.get('amount_formatted')}, account={first_ev.get('account_reference')}")
        assert "XXXX" in first_ev.get("account_reference"), "Account number must be masked!"
        print("[PASS] Provenance & Execution Stages Verified!")

        # 3. Test Action Operator Flow: "Set my food budget to ₹16,000"
        print("\n--- Test 2: Action Operator Phase 1 & 2 ('Set my food budget to ₹16,000') ---")
        await ws.send(json.dumps({
            "type": "text_query",
            "text": "Set my food budget to ₹16,000"
        }))
        
        action_proposal = None
        while True:
            raw_msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
            msg = json.loads(raw_msg)
            if msg.get("type") == "turn_complete":
                action_proposal = msg.get("action_proposal")
                print(" [Turn Complete] Assistant text:", msg.get("text"))
                break
        
        assert action_proposal is not None, "Expected action_proposal in payload!"
        action_id = action_proposal.get("action_id")
        action_type = action_proposal.get("action_type")
        params = action_proposal.get("parameters")
        print(f" -> Generated Action Proposal: id={action_id}, type={action_type}, params={params}")
        assert action_type == "set_category_budget", f"Unexpected action_type: {action_type}"
        assert params.get("amount") == 16000.0, f"Expected amount 16000.0, got {params.get('amount')}"

        # Confirm the action proposal via REST
        async with httpx.AsyncClient() as client:
            confirm_res = await client.post(f"{BACKEND_HTTP}/actions/{action_id}/confirm")
            print(f" -> Confirm Action REST Response: status={confirm_res.status_code}, data={confirm_res.json()}")
            assert confirm_res.status_code == 200, "Failed to confirm action proposal"
            assert confirm_res.json().get("success") is True, "Action execution unsuccessful"

        print("[PASS] Action Operator Prepared & Executed Successfully!")

        # 4. Test Predictive Advisory Flow: "What if I reduce dining expenses by 20%?"
        print("\n--- Test 3: Predictive Advisory ('What if I reduce dining expenses by 20%?') ---")
        await ws.send(json.dumps({
            "type": "text_query",
            "text": "What if I reduce dining expenses by 20%?"
        }))
        
        sim_data = None
        while True:
            raw_msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
            msg = json.loads(raw_msg)
            if msg.get("type") == "turn_complete":
                sim_data = msg.get("simulation_data")
                print(" [Turn Complete] Assistant text:", msg.get("text"))
                break
        
        assert sim_data is not None, "Expected simulation_data in payload!"
        print(f" -> Historical spend: ₹{sim_data.get('historical_monthly_spend'):,.2f}")
        print(f" -> Monthly savings at 20%: ₹{sim_data.get('monthly_savings'):,.2f}")
        print(f" -> Annualized savings: ₹{sim_data.get('annualized_savings'):,.2f}")
        print(f" -> Vacation Fund Impact: {sim_data.get('goal_impact')}")

        # Test live interactive slider scrubbing via WS
        print("\n -> Testing live slider adjustment over WebSocket to 35% reduction...")
        await ws.send(json.dumps({
            "type": "simulate_slider",
            "category": "Food & Dining",
            "reduction_pct": 35.0,
            "goal_name": "Vacation Fund"
        }))
        
        slider_res = await asyncio.wait_for(ws.recv(), timeout=5.0)
        slider_data = json.loads(slider_res)
        assert slider_data.get("type") == "simulation_update", f"Expected simulation_update, got {slider_data.get('type')}"
        updated_sim = slider_data.get("data")
        print(f" -> Updated monthly savings at 35%: ₹{updated_sim.get('monthly_savings'):,.2f}")
        print(f" -> Updated annualized savings: ₹{updated_sim.get('annualized_savings'):,.2f}")
        assert updated_sim.get("reduction_percentage") == 35.0
        print("[PASS] Interactive Simulation Slider Verified!")

    print("\n=======================================================")
    print("ALL OPERATIONAL SYSTEM VERIFICATION TESTS PASSED (100%)")
    print("=======================================================")

if __name__ == "__main__":
    asyncio.run(test_e2e_operational_flows())
