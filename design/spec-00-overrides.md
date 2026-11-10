# spec-00-overrides.md: Architectural Overrides for FinSight

> **Precedence**: This document takes absolute precedence over `spec-01.md` and `spec-02.md`.

---

## 1. Scale & Resolution
- **Target Resolution**: Designed and implemented for a **1440px × 900px** desktop viewport.
- **Conversion Factor**: All baseline pixel values from 1024px reference are scaled by **1.4×**.
- **Typography Floor**: Every font size is floored at a minimum of **12px**:
  - Captions / Meta / Timestamps: `12px` (Regular 400).
  - Body Text / Legends: `14px` (Regular 400 / Medium 500).
  - Card Titles / Section Headers: `15px - 16px` (Bold 700 / Semibold 600).
  - KPI Numbers: `~25px - 26px` (Bold 700 with `tabular-nums`).
  - Hero Greeting: `~31px` (Bold 700).
- **Layout Units**: CSS Grid using fractional `fr` units.
  - Sidebar: Fixed **240px**.
  - Main content padding: **28px** all around.

---

## 2. Typography & Numbers
- **Font Family**: **Inter** only.
- **Rule**: No monospace font (`font-mono`) anywhere in the application.
- **Numerals**: All numeric and currency displays strictly enforce `font-variant-numeric: tabular-nums` to prevent tabular jitter.

---

## 3. Locale, Dates & Currency
- **Locale**: `en-IN` (Indian English).
- **Currency**: Indian Rupee (`₹`), formatted strictly using `Intl.NumberFormat('en-IN')` (lakh/crore grouping: `₹1,24,500`, `₹48,320`).
- **User Persona**: **Aarav Mehta**, *"Personal Plan"*. (Replaces all USD, Jamie Diaz, and April references).
- **Dynamic Dates**: All dates are computed relative to the current live runtime date. No hardcoded `"Apr 2024/2025"`.

---

## 4. Single Source of Truth: `src/data/mock.ts`
Both Screen A (Voice Assistant) and Screen B (Overview) import directly from this file. No values are hardcoded in components:
- **Income this month**: `₹65,000`.
- **Spending this month**: `₹48,320`.
- **Saved this month**: `₹16,680` (`income - spending`, computed).
- **Savings Rate**: `26%` (`saved / income`, computed).
- **Categories** (6 categories summing to 100% and exactly `₹48,320`):
  1. Housing: `32%` -> `₹15,462`
  2. Food & Dining: `18%` -> `₹8,698`
  3. Transport: `12%` -> `₹5,798`
  4. Shopping: `14%` -> `₹6,765`
  5. Subscriptions: `8%` -> `₹3,866`
  6. Others: `16%` -> `₹7,731`
  *(Sum = exactly ₹48,320)*.
- **Daily Spend Data**: 30 deterministic seeded values summing to exactly `₹48,320`, with each day under `₹6,000`. Tooltip displays that specific day's spend. Yesterday's bar is actively highlighted with luminous purple.
- **Recent Transactions** (Shared list; Screen B displays first 3, Screen A displays all 5):
  1. Zomato: `-₹628` (Food & Dining, 1 day ago)
  2. Swiggy: `-₹450` (Food & Dining, 2 days ago)
  3. Urban Company: `-₹1,200` (Home Services, 3 days ago)
  4. Spotify: `-₹119` (Subscriptions, 4 days ago)
  5. Air India: `-₹12,430` (Travel, 5 days ago)
- **Savings Goals** (`saved` / `target`):
  - Goa Trip: `₹30,000 / ₹75,000` (`40%`)
  - New Laptop: `₹27,000 / ₹90,000` (`30%`)
  - Screen A "Goal Progress": `57,000 / 1,65,000 = 34.5%` -> displayed as `35%` (computed).
- **Account Balance**: `₹1,24,500`.
- **Financial Health Score**: `78` (*"Good"*).
- **Upcoming Bills**: `₹3,200` (*"3 due"*).
- **Investments**: `₹2,34,920`.
- **Quick Insights**: Labelled *"Saved this month"* showing the computed `₹16,680`.

---

## 5. Shared Shell (Both Screens)
- **Sidebar (240px)**:
  - Brand: Logo + `"FinSight"` title.
  - Primary Nav: `Home`, `AI Assistant`, `Accounts`, `Transactions`, `Budgets`, `Investments`, `Goals`, `Reports`.
  - Screen A highlights `AI Assistant`; Screen B highlights `Home`.
  - Bottom: `Settings`, `Upgrade to Pro` card, User profile capsule (`Aarav Mehta`, `Personal Plan`).
- **Header**:
  - Global Search with `⌘ K` chip.
  - Notification Bell with pink alert dot.
  - User Capsule (spec-02 style with initials `"AM"` and dropdown).
  - Status Badge: `● Gnani AI Connected` indicator.

---

## 6. Fidelity Fixes
### Screen A (Voice Assistant Home)
- **Chips Row**: Positioned on a single horizontal row aligned with the Orb's vertical center:
  - Left of Orb: `[Spending Breakdown]` and `[Suggest Budget]`.
  - Right of Orb: `[Investment Ideas]`.
- **Status Indicator**: `"● Live · Secure · Private"` positioned at top-right of the hero area.
- **Right Column Width**: Scaled proportionally (`227px × 1.4 ≈ 318px`), Health card height `~244px`, Insights height `~462px`.
- **Speech Bubble**: First sentence brighter (`#FFFFFF`) and larger (`14px`), details smaller (`12px`, `#C8C5DC`), party emoji 🎉 at the end, small directional tail pointing towards the central sound orb.

### Screen B (Financial Overview)
- **Shared Column Template for Rows 2 & 3**: Unified grid template (`7fr 5fr`) ensuring outer card edges align precisely.
- **Row 1**: `grid-cols-4` with equal gaps.
- **Spending Trend Bars**:
  - Resting bars: Accent violet at `35% - 45%` opacity (`rgba(139, 92, 246, 0.4)`).
  - Active bar (yesterday): Full accent violet with soft specular glow and callout box.
- **Header Date**: Rendered in violet (`#A78BFA`).
- **Goal Thumbnails**: Gradient tile + Lucide icons (Palm tree for Goa Trip, Laptop for New Laptop). Zero hotlinked stock images.
- **Merchant Badges**: Clean colored circular plate + bold white initial glyph.

---

## 7. Sound Orb Specification (Screen A)
- **Material Construction**:
  - Three absolutely positioned, heavily blurred (`blur-2xl`, 24px - 32px) radial gradient layers (Violet `#8B5CF6`, Pink `#EC4899`, Cyan `#06B6D4`) with `mix-blend-mode: screen`.
  - Slow rotation and morphing keyframes simulating fluid sound pressure.
  - Dark center hub: Scaled diameter `100px` (`72px × 1.4`), background `#0D0B23`, border `1px solid rgba(139, 92, 246, 0.3)`.
  - Center hub contents: Soundwave glyph + dynamic status label.
- **Orb States & Text**:
  - `idle`: `"Tap to speak"` (Waveform flat).
  - `listening`: `"Listening..."` (Waveform reactive to microphone input).
  - `processing`: `"Thinking..."` (Waveform breathing pulse).
  - `speaking`: `"Speaking..."` (Waveform synchronized to assistant audio output).

---

## 8. Response Flow
1. User clicks any Action Chip or completes voice query:
2. System transitions to `processing` state.
3. Assistant speech bubble displays an animated activity/typing indicator.
4. Assistant speech bubble and the two central cards (Spending Breakdown / Recent Transactions) dynamically update with contextual financial intelligence.
5. Default starting content matches the exact reference state from `01-voice-home.png`.

---

## 9. Voice Pipeline Architecture & Implementation
- **Speech-to-Text (STT)**:
  - Real: Browser Web Speech API (`webkitSpeechRecognition` / `SpeechRecognition`) capturing real spoken microphone audio.
  - Real: Web Audio API (`AudioContext`, `AnalyserNode`, `navigator.mediaDevices.getUserMedia`) computing real-time `audioLevel` (0.0 to 1.0) to drive live waveform bars during speech.
  - Mocked Fallback: If microphone access is unavailable or speech recognition is not supported in the user agent, simulation fallback handles contextual voice queries.
  - *Code Tag*: Marked with `// TODO: Connect live Gnani.ai ASR WebSocket streaming endpoint for low-latency Indic speech recognition`.
- **Text-to-Speech (TTS)**:
  - Real: Browser Web Speech API (`window.speechSynthesis`) synthesizing spoken answers with synchronized visualizer feedback.
  - *Code Tag*: Marked with `// TODO: Connect live Gnani.ai TTS REST API for natural Indic voices (en-IN, hi-IN)`.
- **"Gnani AI Connected" Indicator**:
  - Located in the global top header next to the search bar and date, as well as reinforced in the Voice Assistant hero status bar:
  - Visual: `● Gnani AI Connected` pill badge with an emerald pulsing live dot and violet border.
