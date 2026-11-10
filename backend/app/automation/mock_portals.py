"""
Embedded Mock Portals for FinSight Autonomous Browser Automation.
Provides realistic, zero-network-dependency portal fixtures for Swiggy, Bescom, and Croma.
Enables 100% deterministic, instant Playwright navigation, scraping, and screenshot verification.
"""

from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse

mock_portals_router = APIRouter(prefix="/mock-portal", tags=["Mock Portals"])


@mock_portals_router.get("/swiggy/order-89218", response_class=HTMLResponse)
async def get_swiggy_mock_receipt():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Swiggy Order Receipt #89218</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f111a; color: #f1f5f9; padding: 24px; margin: 0; display: flex; justify-content: center; }
    .card { background: #1e2230; border: 1px solid #334155; border-radius: 16px; width: 440px; padding: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
    .header { display: flex; align-items: center; justify-content: space-between; border-bottom: 1px dashed #475569; padding-bottom: 16px; }
    .logo { color: #fc8019; font-weight: 800; font-size: 22px; letter-spacing: -0.5px; }
    .badge { background: #065f46; color: #34d399; font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 9999px; }
    .restaurant { margin-top: 16px; font-size: 17px; font-weight: 700; color: #ffffff; }
    .subtext { font-size: 12px; color: #94a3b8; margin-top: 2px; }
    .items { margin-top: 20px; border-bottom: 1px solid #334155; padding-bottom: 14px; }
    .item-row { display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 10px; color: #e2e8f0; }
    .bill-section { margin-top: 16px; }
    .bill-row { display: flex; justify-content: space-between; font-size: 13px; color: #94a3b8; margin-bottom: 8px; }
    .surge-highlight { background: rgba(239, 68, 68, 0.15); border: 1px solid #ef4444; color: #fca5a5; padding: 6px 10px; border-radius: 8px; font-weight: 600; }
    .total-row { display: flex; justify-content: space-between; font-size: 18px; font-weight: 800; color: #38bdf8; border-top: 1px solid #475569; padding-top: 14px; margin-top: 14px; }
    .footer { text-align: center; font-size: 11px; color: #64748b; margin-top: 20px; }
    .seal { display: inline-flex; align-items: center; gap: 4px; color: #10b981; font-size: 11px; font-weight: 600; margin-top: 12px; }
  </style>
</head>
<body>
  <div class="card" id="swiggy-receipt-container">
    <div class="header">
      <span class="logo">SWIGGY</span>
      <span class="badge" id="order-status">DELIVERED</span>
    </div>

    <div class="restaurant" id="restaurant-name">Meghana Foods · Indiranagar</div>
    <div class="subtext" id="order-meta">Order #SW-89218 · Sun, 09 Feb 2025, 11:42 PM (Late-Night)</div>

    <div class="items" id="item-list">
      <div class="item-row">
        <span>Special Chicken Biryani × 1</span>
        <span>₹380.00</span>
      </div>
      <div class="item-row">
        <span>Butter Chicken Bowl (500ml) × 1</span>
        <span>₹480.00</span>
      </div>
      <div class="item-row">
        <span>Butter Garlic Naan × 3</span>
        <span>₹190.00</span>
      </div>
    </div>

    <div class="bill-section">
      <div class="bill-row">
        <span>Item Total (Subtotal)</span>
        <span id="subtotal">₹1,050.00</span>
      </div>
      <div class="bill-row">
        <span>Standard Delivery Fee</span>
        <span>₹45.00</span>
      </div>
      <div class="bill-row surge-highlight" id="surge-row">
        <span>⚠️ Late-Night Peak Surge Fee</span>
        <span id="surge-fee">₹120.00</span>
      </div>
      <div class="bill-row">
        <span>Restaurant Packaging Charges</span>
        <span id="packaging-fee">₹65.00</span>
      </div>
      <div class="bill-row">
        <span>Taxes & GST (5%)</span>
        <span>₹60.00</span>
      </div>
      <div class="bill-row">
        <span>Delivery Partner Tip</span>
        <span>₹140.00</span>
      </div>
      <div class="total-row">
        <span>Total Paid via UPI</span>
        <span id="total-amount">₹1,480.00</span>
      </div>
    </div>

    <div class="footer">
      <div>Delivered to: Aarav Mehta, 4th Cross, Indiranagar, Bengaluru</div>
      <div class="seal">✓ Verified Digital Tax Invoice · GSTIN: 29AABCU9201L1Z4</div>
    </div>
  </div>
</body>
</html>
"""
    return HTMLResponse(content=html_content)


@mock_portals_router.get("/bescom/account-102938475", response_class=HTMLResponse)
async def get_bescom_mock_portal():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>BESCOM Electricity Portal - Official Bill Verification</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0b1329; color: #f8fafc; padding: 24px; margin: 0; display: flex; justify-content: center; }
    .container { background: #131d38; border: 1px solid #1e293b; border-radius: 16px; width: 500px; padding: 26px; box-shadow: 0 12px 30px rgba(0,0,0,0.6); }
    .gov-banner { display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #3b82f6; padding-bottom: 14px; margin-bottom: 18px; }
    .brand { font-size: 18px; font-weight: 800; color: #60a5fa; letter-spacing: 0.5px; }
    .dept { font-size: 11px; color: #94a3b8; }
    .verified-stamp { background: #064e3b; border: 1px solid #10b981; color: #34d399; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 18px; }
    .cell { background: #1e293b; border-radius: 8px; padding: 10px 14px; }
    .cell-title { font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 600; }
    .cell-value { font-size: 14px; font-weight: 700; color: #ffffff; margin-top: 3px; }
    .meter-box { background: rgba(59, 130, 246, 0.1); border: 1px solid #2563eb; border-radius: 10px; padding: 14px; margin-bottom: 18px; }
    .units-val { font-size: 26px; font-weight: 800; color: #38bdf8; }
    .bill-summary { border-top: 1px solid #334155; padding-top: 14px; }
    .row { display: flex; justify-content: space-between; font-size: 13px; color: #cbd5e1; margin-bottom: 8px; }
    .grand-total { display: flex; justify-content: space-between; font-size: 20px; font-weight: 800; color: #fbbf24; border-top: 2px solid #475569; padding-top: 12px; margin-top: 12px; }
    .status-alert { margin-top: 16px; background: rgba(245, 158, 11, 0.15); border: 1px solid #d97706; color: #fde68a; padding: 10px; border-radius: 8px; font-size: 12px; display: flex; justify-content: space-between; align-items: center; }
  </style>
</head>
<body>
  <div class="container" id="bescom-verification-container">
    <div class="gov-banner">
      <div>
        <div class="brand">BESCOM · Karnataka Power</div>
        <div class="dept">Bangalore Electricity Supply Company Limited</div>
      </div>
      <div class="verified-stamp" id="portal-seal">✓ OFFICIAL BBPS PORTAL</div>
    </div>

    <div class="grid">
      <div class="cell">
        <div class="cell-title">Consumer Account ID</div>
        <div class="cell-value" id="consumer-id">102938475</div>
      </div>
      <div class="cell">
        <div class="cell-title">Consumer Name</div>
        <div class="cell-value" id="consumer-name">Aarav Mehta</div>
      </div>
      <div class="cell">
        <div class="cell-title">Sub-Division</div>
        <div class="cell-value">E4 Indiranagar, Bengaluru</div>
      </div>
      <div class="cell">
        <div class="cell-title">Tariff Category</div>
        <div class="cell-value" id="tariff-type">LT-2a (Domestic)</div>
      </div>
    </div>

    <div class="meter-box">
      <div class="cell-title">Active Consumption Cycle (Feb 2025)</div>
      <div class="units-val" id="units-consumed">184 kWh (Units)</div>
      <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">Previous: 4,120 kWh | Current: 4,304 kWh · Meter: KA-BLR-89210</div>
    </div>

    <div class="bill-summary">
      <div class="row">
        <span>Energy Charges (184 units @ tiered slab)</span>
        <span>₹1,048.80</span>
      </div>
      <div class="row">
        <span>Fixed Monthly Demand Charges</span>
        <span>₹180.00</span>
      </div>
      <div class="row">
        <span>Fuel Cost Adjustment Charge (FAC)</span>
        <span>₹92.00</span>
      </div>
      <div class="row">
        <span>State Electricity Duty</span>
        <span>₹79.20</span>
      </div>
      <div class="grand-total">
        <span>Total Payable Bill Amount</span>
        <span id="bill-amount">₹1,400.00</span>
      </div>
    </div>

    <div class="status-alert">
      <span>Payment Due Date: <strong id="due-date">28 Feb 2025</strong></span>
      <span style="font-weight: 700; color: #f59e0b;">STATUS: UNPAID</span>
    </div>
  </div>
</body>
</html>
"""
    return HTMLResponse(content=html_content)


@mock_portals_router.get("/croma/order-49102", response_class=HTMLResponse)
async def get_croma_mock_portal():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Croma Retail Invoice #49102</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #090d16; color: #f8fafc; padding: 24px; margin: 0; display: flex; justify-content: center; }
    .box { background: #141c2e; border: 1px solid #1e293b; border-radius: 16px; width: 460px; padding: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
    .top { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #06b6d4; padding-bottom: 12px; margin-bottom: 16px; }
    .brand { font-size: 20px; font-weight: 900; color: #22d3ee; }
    .invoice-tag { font-size: 11px; background: #083344; color: #67e8f9; padding: 3px 8px; border-radius: 4px; font-weight: 600; }
    .prod-box { background: #0f172a; border: 1px solid #334155; border-radius: 10px; padding: 14px; margin-bottom: 16px; }
    .prod-title { font-size: 15px; font-weight: 700; color: #ffffff; }
    .prod-sku { font-size: 12px; color: #94a3b8; margin-top: 4px; }
    .prod-specs { font-size: 12px; color: #38bdf8; margin-top: 6px; }
    .price-row { display: flex; justify-content: space-between; font-size: 18px; font-weight: 800; color: #f8fafc; border-top: 1px solid #334155; padding-top: 12px; }
    .warranty { background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; color: #6ee7b7; padding: 8px 12px; border-radius: 8px; font-size: 12px; margin-top: 16px; }
  </style>
</head>
<body>
  <div class="box" id="croma-invoice-container">
    <div class="top">
      <div class="brand">CROMA · Electronics</div>
      <div class="invoice-tag" id="invoice-no">TAX INVOICE #CR-49102</div>
    </div>
    <div style="font-size: 12px; color: #94a3b8; margin-bottom: 14px;">Store: Croma Indiranagar 100ft Rd · Purchased: 12 Feb 2025</div>

    <div class="prod-box">
      <div class="prod-title" id="product-name">Belkin Ultra High Speed HDMI 2.1 4K/8K Display Cable (2m)</div>
      <div class="prod-sku">Category: Computer & Display Hardware · SKU: BLK-HDMI-99812-IN</div>
      <div class="prod-specs">48 Gbps Bandwidth · Dolby Vision & eARC Compatible · Space Grey</div>
    </div>

    <div class="price-row">
      <span>Amount Paid via Credit Card (** 4102)</span>
      <span id="croma-total">₹2,400.00</span>
    </div>

    <div class="warranty">
      ✓ Verified Hardware Purchase · 2-Year Manufacturer Warranty Active
      <div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">Eligible for return/replacement until 26 Feb 2025</div>
    </div>
  </div>
</body>
</html>
"""
    return HTMLResponse(content=html_content)
