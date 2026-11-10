# Specification 02: Financial Overview Dashboard (`design/refs/02-overview.png`)

## 1. Grid & Spatial Layout

### Canvas Geometry
- Total Viewport Reference: 1024px width × 670px height (Aspect Ratio ~1.53 : 1).
- Outer Canvas Base: Deep Obsidian Black `#07060B`.
- Base Layout Structure: 2-column parent split:
  - **Left Rail (Sidebar)**: Fixed width 168px (16.4% of viewport width), 100% viewport height.
  - **Main Content Shell**: Fluid width 856px (83.6% of viewport width), 100% viewport height, internal padding 16px top/bottom, 20px left/right.

### Main Content Grid (12-Column Equivalent)
The main content area is structured across three distinct vertical row blocks:
- **Row 1 (KPI Metrics)**: 4 equal columns (3 of 12 columns each, ~198px width per card, 12px gap).
- **Row 2 (Trend & Category Split)**: Asymmetric 2-column split:
  - Left Card (Spending Trend Bar Chart): 7 of 12 columns (~490px width, 59% of row).
  - Right Card (Spending by Category Donut): 5 of 12 columns (~330px width, 41% of row).
- **Row 3 (Ledger & Goals Split)**: Symmetric 2-column split:
  - Left Card (Recent Transactions): 6 of 12 columns (~410px width, 50% of row).
  - Right Card (Your Goals Progress): 6 of 12 columns (~410px width, 50% of row).
- **Grid Gutter / Spacing**: 12px horizontal and vertical gaps.

### Row Order & Card Positioning

```
+---------------------------------------------------------------------------------------------------------------+
| Sidebar (168px) | Top Navigation Header: Search (280px) | ⌘K | Bell (32px) | User Capsule (130px)             |
|                 +------------------------------------------------------------------+--------------------------+
|                 | Greeting: "Good evening, Jamie"                                  | Date: "Thu, Apr 24, 2025"|
|                 | Subtitle: "Here's what's happening with your money today."       | "Small steps. A brighter"|
|                 +------------------------------------------------------------------+--------------------------+
|                 | Gliding Segmented Tabs: [Overview] [Spending] [Cash Flow] [Goals]                           |
|                 +--------------------+---------------------+--------------------+-----------------------------+
|                 | KPI Card 1         | KPI Card 2          | KPI Card 3         | KPI Card 4                  |
|                 | Total Balance      | Monthly Spending    | Monthly Income     | Savings Rate                |
|                 | $24,390.12         | $3,207.56           | $5,800.00          | 26%                         |
|                 +--------------------+---------------------+--------------------+-----------------------------+
|                 | Spending Trend Bar Chart (490px × 210px)  | Spending by Category Donut (330px × 210px)      |
|                 | - Timeframe Range: 7D | [30D] | 3M | 1Y   | - Donut Chart ($3,207.56 Total) + 6 Categories  |
|                 | - Highlighted Bar: Apr 22 ($3,207.56)     |                                                 |
|                 +-------------------------------------------+-------------------------------------------------+
|                 | Recent Transactions (410px × 170px)       | Your Goals (410px × 170px)                      |
|                 | - Spotify (-$11.99)                       | - Bali Trip ($1,200 / $3,000 | 40%)             |
|                 | - Whole Foods (-$86.42)                   | - New Laptop ($450 / $1,500 | 30%)              |
|                 | - Uber (-$24.50)                          |                                                 |
+-----------------+-------------------------------------------+-------------------------------------------------+
```

### Single Dominant Element
- **Component**: 4-Metric Primary KPI Row combined with the **Spending Trend Bar Chart Card**.
- **Visual Weight**: The Spending Trend card occupies 490px × 210px in the primary focal plane, featuring 30 sequential vertical bars with a luminous purple active bar indicator at Apr 22 (`#AB85FF`) and an anchored currency callout tag (`$3,207.56`).

---

## 2. Component Inventory (Top-Left to Bottom-Right)

### Column 1: Left Navigation Rail (x: 0px to 168px)
1. **Brand Capsule** (Top-Left, y: 16px):
   - Icon: 4-petal geometric clover symbol (24px × 24px, gradient violet `#8B5CF6` to indigo `#6366F1`).
   - Title: `"FinSight"` (Font: 15px bold, `#FFFFFF`).
2. **Main Navigation Items** (y: 60px to 270px):
   - Items: `Home` (Active), `Accounts`, `Transactions`, `Budgets`, `Goals`, `Insights`.
   - Inactive item style: 12px medium, `#7C7896`, 16px icon, horizontal padding 12px, vertical padding 8px.
   - Active item (`Home`): Rounded rectangle pill (height 34px), background `#1E1740`, 1px solid border `#4A35A8`, text `#FFFFFF` 12px bold, icon `#A78BFA`.
3. **Lower Navigation Items** (y: 470px to 630px):
   - `Settings` link: Gear icon (16px), text `"Settings"` (12px, `#7C7896`).
   - `Upgrade to Pro` Card:
     - Dimensions: 148px width × 74px height, background `#0F0E1E`, border 1px solid `#242044`, radius 12px, padding 10px.
     - Top row: Crown icon (14px, `#A78BFA`).
     - Title: `"Upgrade to Pro"` (11px bold, `#FFFFFF`).
     - Subtitle: `"Unlock deeper insights and smarter tools."` (9px regular, `#7C7896`).
     - Trailing: Chevron-right icon (12px, `#5A5675`).

### Top Header Bar (x: 188px to 1004px, y: 12px to 44px)
4. **Search Input Bar** (x: 188px, y: 12px):
   - Dimensions: 320px width × 32px height.
   - Background: `#0F1017`, border 1px solid `#212330`, radius 8px, padding 0 10px.
   - Icon: Search magnifying glass (12px, `#625E7E`).
   - Placeholder: `"Search transactions, merchants, or goals..."` (11px, `#625E7E`).
   - Shortcut Chip: `"⌘ K"` (background `#181A24`, border `#2A2D3D`, text `#8E8AA5`, 9px).
5. **Notification Bell Button** (x: 770px):
   - Dimensions: 32px × 32px, circular, background `#121026`, border 1px solid `#1F1B3E`.
   - Icon: Bell (13px, `#8E8AA5`).
   - Badge: Pink dot (5px, `#FF3B69`).
6. **User Profile Capsule** (x: 815px to 995px):
   - Container: Rounded-full capsule (height 32px), background `#121026`, border 1px solid `#1F1B3E`, padding 0 8px.
   - Avatar: 24px circle, background `#7052B2`, initial `"JD"`, text 10px bold `#FFFFFF`.
   - Name & Role: `"Jamie Diaz"` (11px bold, `#FFFFFF`), `"Personal Plan"` (9px regular, `#7C7896`).
   - Trailing: Chevron-down icon (10px, `#5A5675`).

### Greeting & Horizon Row (y: 54px to 100px)
7. **Greeting Text**:
   - Heading 1: `"Good evening, Jamie"` (Font: 22px bold, `#FFFFFF`).
   - Subtitle: `"Here's what's happening with your money today."` (Font: 11px regular, `#7C7896`).
8. **Date & Motto Block** (Top-Right, aligned at `x=815px`):
   - Date: `"Thu, Apr 24, 2025"` (Font: 10px bold, `#FFFFFF`).
   - Motto: `"Small steps. A brighter tomorrow."` (Font: 9px regular, `#5C5877`).

### Segmented Tab Controls (y: 110px to 142px)
9. **Gliding Segmented Tabs**:
   - Container: Height 32px, inline-flex, background `#0F0E1E`, border 1px solid `#221E3E`, radius 10px, padding 2px.
   - 4 Tabs:
     - `[Overview]` (Active): Background `#7052B2`, border 1px solid `#8B5CF6`, text 11px bold `#FFFFFF`, icon (layout grid 12px).
     - `[Spending]`: Text 11px medium `#7C7896`, icon (wallet 12px).
     - `[Cash Flow]`: Text 11px medium `#7C7896`, icon (refresh-cw 12px).
     - `[Goals]`: Text 11px medium `#7C7896`, icon (heart 12px).

### Row 1: Four Primary KPI Cards (y: 154px to 238px)
10. **Card 1: Total Balance**:
    - Dimensions: 198px width × 84px height, background `#0D0B16`, border 1px solid `#1A182A`, radius 12px, padding 12px.
    - Icon Box: 26px × 26px, radius 8px, background `#152238`, icon wallet (14px, `#3F83FF`).
    - Label: `"Total Balance"` (10px medium, `#7C7896`).
    - Value: `"$24,390.12"` (18px bold font-mono tabular-nums, `#FFFFFF`).
    - Trend: `"↑ 2.4%  vs. last month"` (Font: 9.5px semibold, arrow `#10B981`, text `#10B981` / `#7C7896`).
11. **Card 2: Monthly Spending**:
    - Dimensions: 198px width × 84px height, background `#0D0B16`, border 1px solid `#1A182A`, radius 12px, padding 12px.
    - Icon Box: 26px × 26px, radius 8px, background `#2C1428`, icon receipt (14px, `#E065A6`).
    - Label: `"Monthly Spending"` (10px medium, `#7C7896`).
    - Value: `"$3,207.56"` (18px bold font-mono tabular-nums, `#FFFFFF`).
    - Trend: `"↓ 12.1%  vs. last month"` (Font: 9.5px semibold, arrow `#10B981`, text `#10B981` / `#7C7896`).
12. **Card 3: Monthly Income**:
    - Dimensions: 198px width × 84px height, background `#0D0B16`, border 1px solid `#1A182A`, radius 12px, padding 12px.
    - Icon Box: 26px × 26px, radius 8px, background `#10281E`, icon banknote (14px, `#45D598`).
    - Label: `"Monthly Income"` (10px medium, `#7C7896`).
    - Value: `"$5,800.00"` (18px bold font-mono tabular-nums, `#FFFFFF`).
    - Trend: `"↑ 6.3%  vs. last month"` (Font: 9.5px semibold, arrow `#10B981`, text `#10B981` / `#7C7896`).
13. **Card 4: Savings Rate**:
    - Dimensions: 198px width × 84px height, background `#0D0B16`, border 1px solid `#1A182A`, radius 12px, padding 12px.
    - Icon Box: 26px × 26px, radius 8px, background `#201438`, icon target (14px, `#8B5CF6`).
    - Label: `"Savings Rate"` (10px medium, `#7C7896`).
    - Value: `"26%"` (18px bold font-mono tabular-nums, `#FFFFFF`).
    - Trend: `"↑ 4 pp  vs. last month"` (Font: 9.5px semibold, arrow `#10B981`, text `#10B981` / `#7C7896`).

### Row 2: Analytics & Category Distribution (y: 250px to 465px)
14. **Spending Trend Card** (Left, x: 188px, width: 490px, height: 215px):
    - Background: `#0D0B16`, border 1px solid `#1A182A`, radius 14px, padding 14px.
    - Header:
      - Icon & Title: Bar chart icon (13px `#A78BFA`), `"Spending Trend"` (12px bold `#FFFFFF`).
      - Timeframe Filter: Inline pill segmented button (`7D`, `[30D]`, `3M`, `1Y`). Active `30D` pill background `#7052B2`, border `#8B5CF6`, text 10px bold `#FFFFFF`. Inactive text 10px `#7C7896`.
    - Bar Chart Graphic:
      - 30 vertical daily bars, width 6px, radius [2px, 2px, 0, 0].
      - Baseline bar color: `#201E3E` (inactive/resting days).
      - Active highlight bar (Apr 22): Height 110px, color `#AB85FF`, glowing drop shadow.
      - Callout Tooltip: Anchored above Apr 22 bar: Box background `#1E1838`, border `#3B2E68`, text `"Apr 22"` (8px `#7C7896`), `"$3,207.56"` (10px bold font-mono `#FFFFFF`).
      - X-Axis Labels: `"Mar 25"`, `"Apr 1"`, `"Apr 8"`, `"Apr 15"`, `"Apr 22"` (9px font-mono `#5A5675`).
      - Y-Axis Labels: `"$0"`, `"$2K"`, `"$4K"`, `"$6K"` (8.5px font-mono `#5A5675`).
15. **Spending by Category Card** (Right, x: 690px, width: 314px, height: 215px):
    - Background: `#0D0B16`, border 1px solid `#1A182A`, radius 14px, padding 14px.
    - Header:
      - Icon & Title: Pie chart icon (13px `#A78BFA`), `"Spending by Category"` (12px bold `#FFFFFF`).
      - Link: `"View all"` (10px medium `#7C7896`).
    - Donut Chart & Legend Layout (Side-by-side inside card):
      - Left: Donut Chart (diameter 100px, stroke width 16px). Center label `"$3,207.56"` (11px bold `#FFFFFF`), `"Total"` (8px regular `#7C7896`).
      - Right: Vertical legend list (6 items, font 9.5px):
        - Housing: Dot `#8B5CF6`, `"Housing"`, `"32%"`, `"$1,026.42"`.
        - Food & Dining: Dot `#06B6D4`, `"Food & Dining"`, `"18%"`, `"$577.36"`.
        - Transport: Dot `#EC4899`, `"Transport"`, `"12%"`, `"$384.91"`.
        - Shopping: Dot `#F59E0B`, `"Shopping"`, `"11%"`, `"$352.83"`.
        - Entertainment: Dot `#10B981`, `"Entertainment"`, `"8%"`, `"$256.60"`.
        - Other: Dot `#3B82F6`, `"Other"`, `"19%"`, `"$609.44"`.

### Row 3: Activity Ledger & Goal Progress (y: 477px to 645px)
16. **Recent Transactions Card** (Left, x: 188px, width: 398px, height: 168px):
    - Background: `#0D0B16`, border 1px solid `#1A182A`, radius 14px, padding 14px.
    - Header: List icon (13px `#A78BFA`), `"Recent Transactions"` (12px bold `#FFFFFF`), link `"View all"` (10px medium `#7C7896`).
    - 3 Rows (height 34px each):
      - Row 1: Spotify green circle badge (22px), Title `"Spotify"`, Meta `"Apr 24, 2025 · Subscriptions"`, Amount `"-$11.99"` (11px bold `#FFFFFF`).
      - Row 2: Whole Foods dark green circle badge (22px), Title `"Whole Foods"`, Meta `"Apr 23, 2025 · Groceries"`, Amount `"-$86.42"`.
      - Row 3: Uber black circle badge (22px), Title `"Uber"`, Meta `"Apr 22, 2025 · Transport"`, Amount `"-$24.50"`.
17. **Your Goals Card** (Right, x: 598px, width: 406px, height: 168px):
    - Background: `#0D0B16`, border 1px solid `#1A182A`, radius 14px, padding 14px.
    - Header: Target icon (13px `#A78BFA`), `"Your Goals"` (12px bold `#FFFFFF`), link `"View all"` (10px medium `#7C7896`).
    - 2 Goal Milestone Rows (height 52px each):
      - Goal 1:
        - Thumbnail: 32px × 32px rounded square image (beach palm trees, radius 8px).
        - Title: `"Bali Trip"` (11px bold `#FFFFFF`).
        - Subtitle: `"$1,200 / $3,000"` (9.5px font-mono `#7C7896`).
        - Percentage: `"40%"` (10px bold `#7C7896`).
        - Progress Bar: Width 100%, height 4px, background track `#1C1832`, fill purple `#8B5CF6` at 40% width.
      - Goal 2:
        - Thumbnail: 32px × 32px rounded square image (modern house, radius 8px).
        - Title: `"New Laptop"` (11px bold `#FFFFFF`).
        - Subtitle: `"$450 / $1,500"` (9.5px font-mono `#7C7896`).
        - Percentage: `"30%"` (10px bold `#7C7896`).
        - Progress Bar: Width 100%, height 4px, background track `#1C1832`, fill purple `#8B5CF6` at 30% width.

---

## 3. Sampled Design Tokens

### Color Palette (Hex)
| Token Category | Hex Value | Target Elements |
| :--- | :--- | :--- |
| **Canvas Base** | `#07060B` | Root application canvas background |
| **Sidebar Base** | `#0A0A14` | Left navigation rail surface |
| **Card Surface** | `#0D0B16` | KPI cards, Spending trend panel, Donut card, Goals card |
| **Active Pill Surface** | `#7052B2` | Active tab `Overview`, active timeframe `30D`, user avatar |
| **Card Border Normal** | `#1A182A` | Structural 1px micro-borders on panels |
| **Card Border Accent** | `#8B5CF6` | Active segmented tab border, active bar outline |
| **Primary Text** | `#FFFFFF` | Headings, active KPI amounts, active tab labels |
| **Secondary Text** | `#C8C5DC` | Card titles, transaction amounts, legend amounts |
| **Muted Text** | `#7C7896` | Labels, subtitles, inactive tabs, dates, meta |
| **Subtle Axis Text** | `#5A5675` | Chart axis labels ($0, $2K, Mar 25), shortcut chip text |
| **Accent Violet (Brand)** | `#8B5CF6` | Goal progress bar fill, active chart bar, logo petal |
| **Accent Purple Luminous**| `#AB85FF` | Highlighted Apr 22 bar in spending trend chart |
| **Blue Icon Surface** | `#152238` | Total balance icon container (icon: `#3F83FF`) |
| **Pink Icon Surface** | `#2C1428` | Monthly spending icon container (icon: `#E065A6`) |
| **Green Icon Surface** | `#10281E` | Monthly income icon container (icon: `#45D598`) |
| **Purple Icon Surface** | `#201438` | Savings rate icon container (icon: `#8B5CF6`) |
| **Status Green (Success)**| `#10B981` | Positive trend percentages (`+2.4%`, `+6.3%`, `+4 pp`) |
| **Status Pink / Red** | `#FF3B69` | Notification alert dot on bell |

### Radii Hierarchy
- Outer Cards & Panels: `14px` (`rounded-2xl`).
- Small KPI Cards & Thumbnails: `12px` (`rounded-xl`).
- Segmented Tabs Container & Inner Icon Boxes: `8px` - `10px` (`rounded-lg`).
- Search Bar: `8px` (`rounded-lg`).
- Active Segmented Pill & Timeframe Toggle: `8px` (`rounded-lg`).
- User Profile Pill: `9999px` (`rounded-full`).

### Spacing Scale (4px Base)
- Micro padding: `4px` (within tabs, chips).
- Element gap: `6px` - `8px` (between list items, labels).
- Card internal padding: `12px` - `14px`.
- Grid column gap: `12px`.
- Root viewport padding: `16px` vertical, `20px` horizontal.

### Exact Typography Hierarchy
| Role | Font Size | Weight | Line Height | Letter Spacing | Font Family |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Greeting Title** | 22px | Bold (700) | 28px | -0.02em | Sans-serif (Inter / System) |
| **Card Header / Section** | 12px | Bold (700) | 16px | -0.01em | Sans-serif |
| **KPI Amount Value** | 18px | Bold (700) | 22px | -0.02em | Monospace / Tabular-nums |
| **Standard Amount Value** | 11px | Bold (700) | 15px | 0em | Monospace / Tabular-nums |
| **Label / Subtitle** | 10px - 11px | Regular (400) | 14px | 0em | Sans-serif |
| **Trend / Percentage Badge**| 9.5px | Semibold (600)| 13px | 0em | Monospace / Tabular-nums |
| **Axis / Caption / Meta** | 8.5px - 9px | Regular (400) | 12px | +0.01em | Monospace / Sans-serif |

---

## 4. Animation & Interactivity States

### Animated Components
1. **Spending Trend Bar Chart**:
   - Initial entry: Bars scale up vertically from `scaleY(0)` to full height with staggered 20ms delay.
   - Active bar pulse: Highlighted Apr 22 bar features subtle specular luminance on load.
2. **Category Donut Chart**:
   - Initial entry: Circumference dashoffset animation from 0° to 360° over 600ms.
3. **Goal Progress Bars**:
   - Initial entry: Fill width transitions from 0% to target percentage (40% for Bali, 30% for Laptop) over 700ms with cubic-bezier ease.

### Interactive Controls
1. **Timeframe Range Toggle (`7D | 30D | 3M | 1Y`)**:
   - Click event: Shifts sliding active background pill between timeframe options.
   - Data reaction: Updates the Spending Trend bar chart dataset and x-axis intervals.
2. **Segmented Gliding Tabs (`[Overview] | [Spending] | [Cash Flow] | [Goals]`)**:
   - Click event: Slides the `#7052B2` indicator pill to selected tab and updates the lower workspace.
3. **Bar Hover Callout**:
   - Mouse hover over any daily bar: Displays tooltip with exact date and transaction total.
4. **Navigation Links (`View all` on Category, Transactions, and Goals)**:
   - Click event: Routes user to corresponding detailed ledger or settings view.
5. **Sidebar Navigation Items**:
   - Hover: Background highlights to `rgba(255, 255, 255, 0.04)`.
   - Click: Switches active workspace view.

### Static Components
- Card containers, background canvas, structural border dividers, category legend text, date header, goal thumbnails.
