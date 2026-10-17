# Merchant Flow Precision --- Design System Specifications (DukaanFlow)

## 1. Visual Identity and Philosophy

DukaanFlow uses a minimal, trustworthy, high-density fintech aesthetic
for Indian merchants, kirana stores, and local wholesalers. The
interface draws inspiration from the clarity and restraint of Stripe,
Linear, and INDmoney without copying their branding.

Priorities: - Instant financial legibility: distinguish available cash,
incoming receivables, and supplier liabilities. - Low-distraction,
anti-glare surfaces suitable for shop counters. - Restrained elevation:
subtle borders and light shadows, not heavy glassmorphism or neon
gradients. - Consistent separation between actual, scheduled, estimated,
and simulated values.

## 2. Color Palette and Semantic Tokens

### Base and Surfaces

  Token              Hex         Use
  ------------------ ----------- ---------------------------------------
  `surface-canvas`   `#F7F8FA`   Global workspace background
  `surface-card`     `#FFFFFF`   Cards, dialogs, tables, inputs
  `surface-muted`    `#F0F2F5`   Secondary fills, chips, table headers
  `border-subtle`    `#E8EAED`   Dividers and outlines
  `border-focus`     `#16A36A`   Focus outline and active indicators

### Brand and Financial Semantics

  -----------------------------------------------------------------------
  Token             Hex               Tint              Use
  ----------------- ----------------- ----------------- -----------------
  Growth Emerald    `#16A36A`         `#E8F7EF`         Positive
                                                        liquidity,
                                                        inflows, primary
                                                        CTA

  Dark Forest       `#0D6843`         ---               Hover/pressed
                                                        primary actions

  Projection Blue   `#6D8FE8`         `#EDF2FD`         Forecast balances
                                                        and scheduled
                                                        values

  Warning Amber     `#E9A23B`         `#FEF6EB`         Due soon, buffer
                                                        warning

  Alert Red         `#DC5555`         `#FDF0F0`         Overdue, negative
                                                        cash, safety
                                                        breach

  Slate Black       `#17191C`         ---               Main text and
                                                        major figures

  Muted Slate       `#737780`         ---               Secondary text
                                                        and captions
  -----------------------------------------------------------------------

## 3. Typography

-   Font stack: `Inter`, `-apple-system`, `BlinkMacSystemFont`,
    `sans-serif`.
-   Use `font-variant-numeric: tabular-nums` for financial figures.
-   Format currency using Indian grouping, e.g. `₹84,500`, `₹1,48,200`,
    `₹12,000`.
-   Do not round stored amounts; round only for presentation when
    explicitly designed.

  Level                  Size   Line Height   Weight Use
  -------------------- ------ ------------- -------- -------------------------
  Display / Hero KPI     32px           1.2      700 Available cash
  Page Title             24px           1.3      600 Screen title
  Card Header            18px           1.4      600 Forecast panel
  Subheading             15px           1.4      600 Names/table sections
  Body                   14px           1.5      400 Main content
  Label / Caption        12px           1.4      500 Helper text
  Micro Badge            11px           1.2      600 OVERDUE, DUE SOON, SAFE

## 4. Layout and Spacing

-   Spacing scale: 4, 8, 12, 16, 20, 24, 32, 40px.
-   Desktop baseline: 1440×900, responsive from 1280px upward.
-   Sidebar: 240px fixed width on desktop, white background, subtle
    right border.
-   Top header: 72px.
-   Main content: 28--32px outer padding, max-width near 1280px.
-   Primary grid gap: 20--24px.
-   Mobile header: 56px.
-   Mobile bottom navigation: 64px with Overview, Khata, Cash Flow,
    Simulator, More.
-   Mobile horizontal content padding: 16px.

## 5. Radius and Elevation

-   Cards and modals: 12--16px radius.
-   Buttons and inputs: 8px radius.
-   Status pills and avatars: full radius.
-   Borders: 1px `#E8EAED`.
-   Shadow: `0 1px 3px rgba(0,0,0,0.04)` only where needed.

## 6. Components

### KPI Cards

-   Small icon in a softly tinted 32×32 area.
-   Subdued label.
-   Large tabular currency figure.
-   Contextual delta/status text.
-   Green for positive liquidity/receivables; amber for payables/due
    soon; red for overdue/critical. Never rely on color alone.

### Ledger Tables

-   Header: 12px semibold uppercase, muted slate, canvas fill.
-   Row height: approximately 56px.
-   Hover: `#F9FAFB`.
-   1px row separators.
-   Actions are text/outline buttons with clear labels.
-   Any WhatsApp or UPI action is only a UI affordance if the
    integration is not implemented; never imply a payment has been sent.

### Forecast Chart

-   Historical/actual realized values: solid emerald line, 2.5px.
-   Projected values: dashed projection blue line.
-   Simulated values: distinct dashed/dotted indigo line.
-   Safety floor: red dashed horizontal line at the configured merchant
    threshold; do not hardcode ₹15,000 as a universal default.
-   Tooltips show date, balance, inflows, outflows, and
    actual/projected/simulated status.

### Status Pills

-   `SAFE`: emerald tint.
-   `DUE SOON`: amber tint.
-   `OVERDUE` / `SHORTAGE`: red tint.
-   Always include readable text and accessible contrast.

## 7. Interaction Rules

-   Primary buttons use `#16A36A`; hover/pressed uses `#0D6843`.
-   Secondary buttons use white surface, 1px border, and canvas hover.
-   Active navigation uses emerald indicator and high-contrast label.
-   Focus state is visible for keyboard users.
-   Confirm reversals and other high-impact actions.
-   Use explicit labels and inline validation; do not rely on
    placeholder text alone.
-   Display skeletons or loading indicators for asynchronous views.
-   Empty states explain the next useful action.

## 8. Page-Level Guidance

### Overview

Cash KPI first, receivables and payables adjacent, forecast chart and
shortage alerts prominent, recent transactions and upcoming obligations
below.

### Customer Khata

Searchable customer table, outstanding balance, status, last activity,
and clear Add Customer / Record Repayment actions.

### Suppliers

Supplier table, unpaid amount, due date, overdue status, and
bill/payment actions.

### Cash Flow

14-day chart, day-by-day table, inflows/outflows, safety buffer, and
contributor details.

### Simulator

Baseline and scenario lines, editable event controls, impact summary,
and reset/save actions. Label all scenario figures as hypothetical.

## 9. Accessibility and Responsive Behavior

-   Meet WCAG AA contrast where practical.
-   Keyboard-accessible menus/dialogs/forms.
-   Visible focus ring and semantic headings.
-   At narrow widths, convert dense tables to stacked rows/cards or
    allow deliberate horizontal scrolling.
-   Charts need a textual/table equivalent.
