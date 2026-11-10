# FinSight: Hallmark Modular UI & Executive FinTech Redesign

> Built with **Hallmark** (`nutlope/hallmark` Theme 01: Executive FinTech Precision) and **Antislop** craft standards.
> Preserves all backend FastAPI APIs, Playwright scrapers, and WebSocket voice gateway connections.

---

## Architecture Overview: The Split Cockpit

FinSight's UI is restructured from a traditional single-column modal flow into an institutional **2-Column Split Cockpit**:

1. **Left Primary Stream (60% Desktop)**:
   - Real-time ReAct co-pilot conversation feed.
   - High-contrast typography and formatted monospace financial tables.
   - **Permanently Accessible Sticky Composer**: Text input is never blocked or hidden; users can type queries or edit figures while the voice assistant is speaking.

2. **Right Pluggable Evidence Inspector (40% Desktop)**:
   - Dedicated inspection surface for rich forensic evidence.
   - Slots dynamically for:
     - **Playwright DOM Receipts**: Swiggy Order #4089, BESCOM Meter Bills with line-item breakdown.
     - **Interactive Spending Donut & Cashflow Simulation**.
     - **Slack Webhook Delivery Receipts & Payload Proof**.
     - **Default Financial Health Score & Voice Latency Monitor**.

3. **Persistent Floating Voice Dock (Bottom Capsule)**:
   - Height: 52px, anchored at the bottom edge (`fixed bottom-4 left-1/2 -translate-x-1/2 z-40`).
   - Replaces the 460px blocking centered modal.
   - Features a 5-bar dynamic equalizer, single-line streaming transcript preview, and tactile micro-controls (Mute Mic, Mute Audio, Stop Speaking, Close).
   - Zero content obstruction: 100% of receipts, chats, and buttons remain visible and interactive.

---

## Palette & Design System

* **Canvas Base**: `#0B0F17` (Deep Obsidian Slate)
* **Surface Panels**: `#111622` (Rich Slate Panel)
* **Hairline Borders**: `rgba(255, 255, 255, 0.08)` / `#1E293B`
* **Accents**:
  * Emerald Green (`#10B981`): Inflows, confirmed transfers, Playwright pass
  * Crimson Red (`#F43F5E`): Spend anomalies, surges, budget breaches
  * Amber Yellow (`#F59E0B`): Upcoming bill deadlines, warning thresholds
  * Electric Indigo (`#6366F1`): Primary brand interaction
* **Typography**: Clean `Inter` for interfaces, tabular monospace `font-mono` for currencies, timestamps, and engine latencies.
