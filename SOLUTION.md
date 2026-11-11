# FinSight 🪙 — Executive Solution Pitch

> **Track**: Voice AI / Agentic Personal Finance  
> **Live Web Application**: [https://finsight-k6ud.onrender.com](https://finsight-k6ud.onrender.com)  
> **GitHub Repository**: [https://github.com/hiensenberg05/FinSight-](https://github.com/hiensenberg05/FinSight-)  
> **Technical Report (PDF)**: [FinSight_Technical_Report.pdf](FinSight_Technical_Report.pdf)  
> **API & Documentation**: [https://finsight-k6ud.onrender.com/docs](https://finsight-k6ud.onrender.com/docs)

---

### 1. Executive Summary & Problem
Personal finance applications remain broken by three critical shortcomings:
1. **Opaque Bank Statements**: Bank ledgers show uninformative strings like `UPI-SWIGGY-89218 ₹1,480` or `BESCOM-BLR ₹1,400`. Users never see the hidden late-night surge fees, packaging markups, or unit tariffs causing their budget spikes.
2. **AI Financial Hallucination**: Generative LLMs hallucinate numbers and advice when asked about money because they predict unconstrained tokens instead of executing deterministic relational math.
3. **Passive Advisory**: Traditional dashboards display static charts instead of autonomously resolving discrepancies or communicating across organizational channels.

---

### 2. The FinSight Solution
**FinSight** is an autonomous, voice-first financial intelligence co-pilot that resolves these challenges through five tightly integrated architectural pillars:

* 🎙️ **Full-Duplex Bilingual Voice Gateway**: Sub-second conversational streaming in **English, Hindi (Devanagari), and Hinglish** powered by Gnani.ai Vachana STT and Timbre Neural TTS, complete with barge-in interruption.
* 🛡️ **Zero-Hallucination SQL Grounding**: 11 deterministic relational database micro-agents compute balances, burn-rates, and category utilizations in integer paise. The LLM only narrates verified database facts—never guessing numbers.
* 🌐 **Autonomous Browser Forensics (Playwright)**: An isolated headless Chromium sandbox navigates merchant portals (Swiggy, BESCOM) on voice command to scrape itemized receipts, unmask surge surcharges, and capture verifiable visual screenshot proofs.
* 🔔 **Dynamic Slack Sentinel**: Event-driven notification engine that constructs interactive Block Kit cards and broadcasts budget overruns, bill reminders, and anomaly clearances directly to Slack channels (`#engineering-inventory-tracker`) and personal assistant DMs.
* 🔒 **Safe Reversible Actions & What-If Simulations**: Human-in-the-loop proposals with liquidity cushion checks (e.g. creating ₹50,000 Emergency Fund goals) and real-time interactive savings sliders.

---

### 3. Production Architecture & Verification

```
React 19 Dashboard (Three.js 3D Orb) ⇄ Full-Duplex WebSockets ⇄ FastAPI Core ⇄ PostgreSQL / SQLite
                                                                      ├── Gnani AI (Vachana STT + Timbre TTS)
                                                                      ├── Playwright (Headless Chromium DOM)
                                                                      ├── Slack Sentinel (Interactive Block Kit)
                                                                      └── Groq ReAct Engine (Zero-Hallucination)
```

* **Test Suite Verification**: **40 out of 40 unit and integration tests passing (100% pass rate)** covering money math, tenant isolation, voice pipelines, and action reversibility.
* **Cloud Infrastructure**: Containerized multi-stage Docker deployment live on **Render** with native WebSocket support and automatic migrations.
