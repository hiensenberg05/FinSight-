import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client):
    """Verify application health route."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_root(client):
    """Verify application root metadata."""
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["product"] == "FinSight"


def test_get_accounts(client):
    """Verify account listing endpoint."""
    res = client.get("/api/v1/accounts")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert any("HDFC" in a["bankName"] for a in data)


def test_get_transactions_with_anomalies(client):
    """Verify transactions endpoint and anomaly indicator presence."""
    res = client.get("/api/v1/transactions")
    assert res.status_code == 200
    txs = res.json()
    assert len(txs) > 0
    # Verify at least one flagged anomaly exists (e.g. Swiggy or Croma)
    anomalies = [t for t in txs if t.get("isAnomaly")]
    assert len(anomalies) >= 1


def test_get_budgets(client):
    """Verify budgets endpoint."""
    res = client.get("/api/v1/budgets")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert any("Food" in b["category"] for b in data)


def test_get_bills_and_autopay_toggle(client):
    """Verify bills list and autoPay toggle."""
    res = client.get("/api/v1/bills")
    assert res.status_code == 200
    bills = res.json()
    assert len(bills) >= 1

    first_bill = bills[0]
    new_autopay = not first_bill["autoPay"]

    patch_res = client.patch(
        f"/api/v1/bills/{first_bill['id']}/autopay",
        json={"autoPay": new_autopay},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["autoPay"] == new_autopay


def test_get_health_metrics(client):
    """Verify financial health metrics endpoint."""
    res = client.get("/api/v1/analytics/health")
    assert res.status_code == 200
    metrics = res.json()
    assert "score" in metrics
    assert "rating" in metrics
    assert metrics["availableBalance"] > 0


def test_get_category_breakdown(client):
    """Verify category breakdown endpoint."""
    res = client.get("/api/v1/analytics/categories")
    assert res.status_code == 200
    cats = res.json()
    assert isinstance(cats, list)
    assert all({"name", "amount"}.issubset(category) for category in cats)


def test_get_cashflow_forecast(client):
    """Verify predictive cashflow forecasting endpoint."""
    res = client.get("/api/v1/forecasts/cashflow")
    assert res.status_code == 200
    pts = res.json()
    assert isinstance(pts, list)
    assert len(pts) >= 3


def test_voice_query_flagship_journey(client):
    """
    Verify flagship user query: 'Why did I spend ₹8,000 more this month?'
    Tests intent classification, tool invocation, and visual chart payload generation.
    """
    res = client.post(
        "/api/v1/voice/query",
        json={"query": "Why did I spend ₹8,000 more this month?", "language": "en"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "text" in data
    if data["chartData"]:
        assert any(w in data["text"].lower() for w in ("increased", "decreased", "rose", "higher", "spike", "more", "jumped"))
        assert data["chartTitle"]
    else:
        assert "no transaction records" in data["text"].lower() or "couldn't compare" in data["text"].lower()


def test_statement_upload(client):
    """Verify CSV statement upload and normalization pipeline."""
    csv_content = """Date,Narration,Chq/Ref No,Value Dt,Withdrawal Amt,Deposit Amt,Closing Balance
03/02/2025,UPI/UBER/309230/RIDE,309230,03/02/2025,350.00,,98250.00
02/02/2025,UPI/SWIGGY/940294/DINNER,940294,02/02/2025,1480.00,,99249.00
31/01/2025,NEFT/TECHCORP/SALARY/JAN2025,NEFT99,31/01/2025,,85000.00,100729.00
"""
    files = {"statement": ("test_statement.csv", csv_content, "text/csv")}
    data = {"bank": "HDFC"}
    res = client.post("/api/v1/statements/upload", files=files, data=data)
    assert res.status_code == 200
    resp_data = res.json()
    assert resp_data["success"] is True
    assert resp_data["importedRows"] == 3
