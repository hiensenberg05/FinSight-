# Specification 01: Voice-First Assistant Home (`design/refs/01-voice-home.png`)

## 1. Grid & Spatial Layout

### Canvas Geometry
- Total Viewport Reference: 1024px width × 651px height (Aspect Ratio ~1.57 : 1).
- Outer Canvas Base: Obsidian `#070512`.
- Base Layout Structure: 2-column parent split:
  - **Left Rail (Sidebar)**: Fixed width 168px (16.4% of viewport width), 100% viewport height.
  - **Main Content Shell**: Fluid width 856px (83.6% of viewport width), 100% viewport height, internal padding 16px top/bottom, 20px left/right.

### Main Content Grid (12-Column Equivalent)
The main content area is subdivided into a 2-column asymmetric workspace:
- **Left/Center Primary Column (Voice & Ledger)**: 8 of 12 columns (~575px width, 68% of main content).
- **Right Context Column (Insights & Health)**: 4 of 12 columns (~245px width, 32% of main content).
- **Grid Gutter / Spacing**: 14px horizontal and vertical gaps.

### Row Order & Card Positioning

```
+-----------------------------------------------------------------------------------------------------------+
| Sidebar (168px) | Top Navigation Header: Search (220px) | ⌘K | Bell (32px) | User Avatar (32px)           |
|                 +--------------------------------------------------------------------+--------------------+
|                 | Hero Greeting & Sound Orb Area (575px × 260px)                     | Date Card (245×44) |
|                 | - Hey, Aarav! + Voice Engine Active + 3 Quick Action Chips         +--------------------+
|                 | - Single Dominant Element: Central Sound Orb (210px × 210px)       | Health Score Card  |
|                 |                                                                    | (245px × 170px)    |
|                 +---------------------------------+----------------------------------+--------------------+
|                 | Spending Breakdown Card         | Recent Transactions Card         | Quick Insights     |
|                 | (280px × 230px)                 | (280px × 230px)                  | Card               |
|                 | - Donut Chart + 6 Categories    | - 5 Merchant Rows                | (245px × 270px)    |
|                 +---------------------------------+----------------------------------+                    |
|                 | Voice Input Bar (Full Width of Left Column: 575px × 52px)          |                    |
+-----------------+--------------------------------------------------------------------+--------------------+
```

### Single Dominant Element
- **Component**: Central Concentric Voice Sound Orb.
- **Coordinates & Size**: Centered at `x=525px, y=210px` relative to viewport; outer diameter 210px × 210px.
- **Visual Weight**: Multi-layer chromatic radial emission with a dark center core (`#0D0B23`, 72px diameter), inner audio glyph, glowing status text `"Listening..."`, and concentric iridescent rings transitioning between Violet (`#6D4FFF`), Fuchsia (`#FF4984`), and Cyan (`#2ECB9E`).

---

## 2. Component Inventory (Top-Left to Bottom-Right)

### Column 1: Left Navigation Rail (x: 0px to 168px)
1. **Brand Capsule** (Top-Left, y: 16px):
   - Icon: Circular badge (28px × 28px) with 3 horizontal audio bars, background `#6D4FFF`.
   - Text Primary: `"FinSight"` (Font: 14px bold, `#FFFFFF`).
   - Text Secondary: `"Clarity for a Brighter You"` (Font: 9px regular, `#7B7895`).
2. **Main Navigation List** (y: 64px to 360px):
   - Items: `Home`, `AI Assistant` (Active), `Accounts`, `Transactions`, `Budgets`, `Investments`, `Goals`, `Reports`.
   - Inactive items: 12px font, `#7C7896`, 16px icon, padding 8px 12px.
   - Active item (`AI Assistant`): Pill background `#160F42`, 1px solid border `#4A35A8`, text `#FFFFFF` 12px bold, icon `#A78BFA`.
3. **Upgrade to Pro Card** (y: 490px):
   - Dimensions: 148px × 68px, background `#100E22`, 1px border `#262248`, radius 12px.
   - Icon: Slanted arrow badge in 24px square (`#1C173E`, icon `#8B5CF6`).
   - Title: `"Upgrade to Pro"` (11px bold, `#FFFFFF`).
   - Subtitle: `"Unlock deeper insights with advanced AI"` (9px regular, `#7B7895`).
4. **User Profile Capsule** (Bottom-Left, y: 580px):
   - Avatar: Circle 28px diameter, background `#372E68`, initial `"A"`, 11px bold `#FFFFFF`.
   - Name: `"Aarav Mehta"` (11px bold, `#FFFFFF`).
   - Plan: `"Personal Plan"` (9px regular, `#7B7895`).
   - Trailing: Chevron-right icon 12px (`#5A5675`).

### Top Header Bar (x: 188px to 1004px, y: 12px to 44px)
5. **Search Input Bar**:
   - Dimensions: 220px width × 32px height, position right-aligned at `x=680px`.
   - Background: `#0C0A1F`, border 1px solid `#1E1A3C`, radius 8px.
   - Elements: Search magnifying icon (12px, `#625E7E`), placeholder `"Search transactions, goals..."` (11px, `#625E7E`), keyboard shortcut chip `"⌘ K"` (background `#181530`, text `#8E8AA5`, 9px).
6. **Notification Bell Button**:
   - Dimensions: 32px × 32px, circular, background `#121026`, border 1px solid `#1F1B3E`.
   - Icon: Bell (13px, `#8E8AA5`).
   - Notification dot: 5px diameter circle, `#FF3B69` at top-right edge.
7. **Header User Avatar Button**:
   - Dimensions: 32px × 32px, circular, background `#2C1E66`, border 1px solid `#4935A8`.

### Main Column — Upper Hero Area (x: 188px to 763px, y: 56px to 320px)
8. **Greeting Block**:
   - Heading 1: `"Hey, Aarav!"` (Font: 22px bold, `#FFFFFF`).
   - Sub-heading / Engine status:
     - Icon: Soundwave icon in rounded pill (`#6D4FFF`).
     - Title: `"Voice Engine Active"` (Font: 14px bold, `#A78BFA`).
     - Prompt text: `"Ask anything about your money. I'm listening."` (Font: 11px regular, `#7C7896`).
9. **Status Indicators**:
   - Text: `"● Live · Secure · Private"` (Font: 10px medium, green dot `#10B981`, text `#7C7896`).
10. **Quick Action Chips Row**:
    - Chips: `[Spending Breakdown]`, `[Suggest Budget]`, `[Investment Ideas]`.
    - Styling: Rounded-full pills (height 26px), background `#14112E`, border 1px solid `#282352`, text 10.5px medium `#D2CFE8`, leading icons (trending-up, target, spark).
11. **Central Concentric Voice Sound Orb**:
    - Position: Center of hero workspace (`x=525px, y=210px`).
    - Outer glowing radius: 105px (210px diameter), diffuse shadow spread `#4428A3` at 40% opacity.
    - Concentric fluid rings: Violet `#6D4FFF`, Pink `#FF4984`, Cyan `#2ECB9E`, Indigo `#3C34C8`.
    - Inner dark hub: 72px diameter, background `#0D0B23`, border 1px solid `#342A68`.
    - Hub content: Audio pulse icon (14px, `#FFFFFF`), text `"Listening..."` (10px medium, `#FFFFFF`).

### Main Column — Middle Row Cards (y: 330px to 570px)
12. **Assistant Speech Bubble Callout**:
    - Overhang position: Spanning top-left of spending card (`x=188px, y=320px`).
    - Dimensions: 220px width × 64px height.
    - Background: `#17152A`, border 1px solid `#2B254E`, radius 10px.
    - Text: `"Here's your spending breakdown for this month, Aarav. You've spent ₹48,320 across 6 categories. That's 12% lower than last month."` (Font: 10px regular, `#C8C5DC`).
13. **Spending Breakdown Card**:
    - Dimensions: 280px width × 230px height, background `#0D0B16`, border 1px solid `#1A182A`, radius 14px, padding 14px.
    - Header: `"Spending Breakdown"` (12px bold, `#FFFFFF`), Month label `"Apr 2024"` (10px regular, `#6B6785`).
    - Donut Chart:
      - Outer radius: 52px, inner radius: 36px, stroke width: 16px.
      - Center text: `"₹48,320"` (14px bold, `#FFFFFF`), `"Total Spend"` (8px regular, `#7C7896`).
      - 6 Slices: Housing 32% (`#6D4FFF`), Food & Dining 18% (`#2ECB9E`), Transport 12% (`#FF4984`), Shopping 14% (`#F59E0B`), Subscriptions 8% (`#D946EF`), Others 16% (`#3B82F6`).
    - Category Legend List (2 columns of 3 rows): Dot (6px circle), Name (9.5px, `#A3A0B8`), Percentage (9.5px bold, `#FFFFFF`).
    - Footer Badge: `"↓ 12% lower than last month"` (Font: 10px semibold, `#10B981`).
14. **Recent Transactions Card**:
    - Dimensions: 280px width × 230px height, background `#0D0B16`, border 1px solid `#1A182A`, radius 14px, padding 14px.
    - Header: `"Recent Transactions"` (12px bold, `#FFFFFF`), Link `"View All →"` (10px medium, `#7C7896`).
    - 5 Transaction Rows (height 32px each, vertical gap 6px):
      - Row 1: Icon box red (`#E23744`, 22px square, initial `"Z"`), Merchant `"Zomato"`, Subtitle `"Food & Dining · Apr 23"`, Amount `"- ₹628"` (Font: 11px bold, `#FFFFFF`).
      - Row 2: Icon box orange (`#FC8019`, 22px square, initial `"S"`), Merchant `"Swiggy"`, Subtitle `"Food & Dining · Apr 22"`, Amount `"- ₹450"`.
      - Row 3: Icon box dark gray (`#24242E`, 22px square, initial `"UC"`), Merchant `"Urban Company"`, Subtitle `"Home Services · Apr 21"`, Amount `"- ₹1,200"`.
      - Row 4: Icon box green (`#1DB954`, 22px square, Spotify wave), Merchant `"Spotify"`, Subtitle `"Subscriptions · Apr 20"`, Amount `"- ₹119"`.
      - Row 5: Icon box red (`#D9383A`, 22px square, initial `"A"`), Merchant `"Air India"`, Subtitle `"Travel · Apr 19"`, Amount `"- ₹12,430"`.

### Main Column — Bottom Row (y: 585px to 635px)
15. **Docked Voice Input Bar**:
    - Dimensions: 575px width × 48px height, centered horizontally under middle row cards.
    - Background: `#0A0818`, border 1px solid `#261E52`, radius 24px (pill), inner shadow.
    - Left Action: Circular mic button (34px diameter, background `#4A32BA`, border 1px solid `#6D4FFF`, glowing purple ring, mic icon 15px `#FFFFFF`).
    - Center-Left Waveform: Animated audio frequency bars (24 bars, width 2px, height 4px to 22px, color `#A78BFA` / `#8B5CF6`).
    - Center-Right Prompt:
      - Primary: `"Speak naturally..."` (11px medium, `#FFFFFF`).
      - Caption: `"Try: 'Show my investment performance' or 'Set a savings goal'"` (9px regular, `#6B6785`).
    - Right Action: Stop/Submit square icon in rounded square button (24px × 24px, border `#261E52`, icon 10px `#7C7896`).

### Right Context Column (x: 777px to 1004px, y: 56px to 635px)
16. **Date & Motto Card** (y: 56px to 102px):
    - Dimensions: 227px width × 46px height, background `#0D0B16`, border 1px solid `#1A182A`, radius 12px, padding 10px 12px.
    - Icon: Sun outline icon (14px, `#8E8AA5`).
    - Primary Text: `"Tue, Apr 23, 2024"` (11px bold, `#FFFFFF`).
    - Subtitle: `"A calmer, wealthier tomorrow."` (9px regular, `#7C7896`).
17. **Financial Health Score Card** (y: 116px to 290px):
    - Dimensions: 227px width × 174px height, background `#0D0B16`, border 1px solid `#1A182A`, radius 14px, padding 14px.
    - Header: `"Financial Health Score"` (11.5px bold, `#FFFFFF`), Pill `"+6 this month"` (9px bold, `#10B981`, background `#0E291E`, border `#164E33`).
    - Gauge Meter:
      - Half-circle arc meter: 120px width × 65px height.
      - Background track: `#17152B`, stroke width 8px.
      - Active arc: Gradient cyan-to-violet (`#38BDF8` to `#8B5CF6`), stroke width 8px, 78% sweep.
      - Metric Center: `"78"` (24px bold font-mono, `#FFFFFF`), `"Good"` (10px bold, `#10B981`).
      - Bounds: `"0"` at left, `"100"` at right (8px font-mono, `#5A5675`).
    - Footer Text: `"You're on track! Keep your spending in check to reach 80+."` (9px regular, `#7C7896`, center-aligned).
18. **Quick Insights Card** (y: 304px to 635px):
    - Dimensions: 227px width × 330px height, background `#0D0B16`, border 1px solid `#1A182A`, radius 14px, padding 14px.
    - Header: Sparkle/gauge icon, `"Quick Insights"` (12px bold, `#FFFFFF`).
    - 4 Insight Rows (height 48px each, border-bottom 1px solid `#151324`):
      - Row 1: Green arrow-up box (`#12241C`, arrow `#10B981`), Value `"₹12,480"` (12px bold), Label `"Total Savings"` (9.5px `#7C7896`), Badge `"+18%"` (9px `#10B981`).
      - Row 2: Purple trend-up box (`#1E163B`, icon `#8B5CF6`), Value `"₹2,34,920"` (12px bold), Label `"Investments"` (9.5px `#7C7896`), Badge `"+12%"` (9px `#10B981`).
      - Row 3: Violet card box (`#1E163B`, icon `#8B5CF6`), Value `"₹3,200"` (12px bold), Label `"Upcoming Bills"` (9.5px `#7C7896`), Badge `"3 due"` (9px `#D946EF`, background `#291236`).
      - Row 4: Target box (`#1E163B`, icon `#8B5CF6`), Value `"67%"` (12px bold), Label `"Goal Progress"` (9.5px `#7C7896`), Badge `"On track"` (9px `#10B981`, background `#0E291E`).
    - Footer Text: `"\"Small steps today, bigger tomorrows.\""` (9.5px italic, `#5C5877`, center-aligned).

---

## 3. Sampled Design Tokens

### Color Palette (Hex)
| Token Category | Hex Value | Target Elements |
| :--- | :--- | :--- |
| **Canvas Base** | `#070512` | Root viewport body background |
| **Sidebar Base** | `#0A0917` | Left navigation rail surface |
| **Card Surface** | `#0D0B16` | All metric cards, speech bubble, right column panels |
| **Card Surface Raised** | `#141128` | Inner interactive pills, speech bubble base |
| **Card Border Normal** | `#1A182A` | Structural 1px micro-borders on panels |
| **Card Border Accent** | `#342A68` | Active cards, speech bubble edge, input bar focus |
| **Primary Text** | `#FFFFFF` | Headings, active KPI numbers, active navigation items |
| **Secondary Text** | `#C8C5DC` | Sub-headings, assistant text, transaction amounts |
| **Muted Text** | `#7C7896` | Labels, captions, dates, inactive navigation items |
| **Subtle Text** | `#5A5675` | Scale markers (0, 100), keyboard shortcut chips |
| **Accent Violet (Brand)** | `#6D4FFF` | Sound orb, mic button, active pills, logo badge |
| **Accent Violet Luminous**| `#A78BFA` | Waveform bars, voice engine badge, arc meter end |
| **Accent Pink / Magenta** | `#FF4984` | Sound orb outer ring, donut chart slice |
| **Accent Cyan / Teal** | `#2ECB9E` | Sound orb ring, donut chart slice, health gauge start |
| **Status Green (Success)**| `#10B981` | Live indicator dot, positive trends (+18%, +6), "Good" |
| **Status Red / Warning** | `#E23744` | Zomato badge, Air India badge, notification dot |
| **Status Orange** | `#FC8019` | Swiggy merchant badge, shopping category slice |

### Radii Hierarchy
- Outer Cards & Panels: `14px` (`rounded-2xl` in Tailwind 3.4 approx).
- Inner Sub-Cards / Speech Bubble: `10px` - `12px` (`rounded-xl`).
- Inputs & Search Box: `8px` (`rounded-lg`).
- Interactive Chips, Badges & Voice Input Bar: `9999px` (`rounded-full`).

### Spacing Scale (4px Base)
- Micro padding: `4px` (within badges, chips).
- Element gap: `6px` - `8px` (between list items, labels).
- Card internal padding: `14px` - `16px`.
- Grid column gap: `14px`.
- Root viewport padding: `16px` vertical, `20px` horizontal.

### Exact Typography Hierarchy
| Role | Font Size | Weight | Line Height | Letter Spacing | Font Family |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Main Hero Title** | 22px | Bold (700) | 28px | -0.02em | Sans-serif (Inter / System) |
| **Card / Section Header** | 12px - 14px | Bold (700) | 18px | -0.01em | Sans-serif |
| **Large KPI Value** | 24px | Bold (700) | 28px | -0.02em | Monospace / Tabular-nums |
| **Standard KPI Value** | 12px - 14px | Bold (700) | 16px | 0em | Monospace / Tabular-nums |
| **Body / Assistant Text** | 10px - 11px | Regular (400) | 15px | 0em | Sans-serif |
| **Category & Legend Labels** | 9.5px - 10px | Medium (500) | 14px | 0em | Sans-serif |
| **Caption / Timestamp / Meta** | 8px - 9px | Regular (400) | 12px | +0.01em | Sans-serif |

---

## 4. Animation & Interactivity States

### Animated Components
1. **Central Concentric Voice Sound Orb**:
   - Continuous state: Multi-layer rotation of fluid chromatic waves (violet `#6D4FFF`, magenta `#FF4984`, cyan `#2ECB9E`).
   - Reaction state: Breathing pulsation of outer luminous aura (scale oscillation between 0.96 and 1.04).
   - Audio pulse icon: Continuous 3-bar sinusoidal height modulation inside dark center hub.
2. **Docked Voice Input Waveform Bars**:
   - 24 vertical pill bars driven by sinusoidal audio level formula (`Math.sin(phase + i * 0.45)`).
   - Dynamic height transitions from 4px resting to 22px speaking amplitude.
3. **Financial Health Arc Gauge**:
   - Initial entry: Radial stroke-dashoffset transition from 0 to 78% over 800ms.
4. **Donut Chart Segments**:
   - Initial entry: Sweep transition from 0° to 360°.

### Interactive Controls
1. **Microphone Button (`Voice Input Bar`)**:
   - Click event: Toggles voice recording state (`idle` ⇄ `listening` ⇄ `processing`).
2. **Action Chips (`Spending Breakdown`, `Suggest Budget`, `Investment Ideas`)**:
   - Click event: Submits predefined text query into conversational intelligence engine.
3. **Sidebar Navigation Items**:
   - Hover: Background transitions to `rgba(255, 255, 255, 0.04)`.
   - Click: Switches active workspace view.
4. **Top Search Bar (`⌘ K`)**:
   - Focus: Border highlights to `#4A35A8`, opens transaction and goal quick-switcher modal.
5. **Recent Transactions (`View All →`)**:
   - Click: Navigates to full ledger view.

### Static Components
- Card containers, background canvas, structural border dividers, category legend text, date header, quotation footer.
