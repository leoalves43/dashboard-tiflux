# DESIGN — Dashboard Tiflux

Tokens live in `frontend/src/styles/tokens.css` as CSS custom properties; components and charts read only these roles (charts via `frontend/src/charts/theme.ts`). No hex, spacing or font outside the token file.
Palette = dataviz skill reference instance (validated; categorical order is the CVD-safety mechanism — never reorder).

## Surfaces & ink
| Role | Light | Dark |
|---|---|---|
| `--page` | #f9f9f7 | #0d0d0d |
| `--surface` (cards, charts) | #fcfcfb | #1a1a19 |
| `--surface-2` (hover, inputs) | #f0efec | #262624 |
| `--ink-1` primary | #0b0b0b | #ffffff |
| `--ink-2` secondary | #52514e | #c3c2b7 |
| `--ink-3` muted / axis | #898781 | #898781 |
| `--grid` hairline | #e1e0d9 | #2c2c2a |
| `--axis` baseline | #c3c2b7 | #383835 |
| `--border` | rgba(11,11,11,.10) | rgba(255,255,255,.10) |
| `--accent` (focus, selection) | #2a78d6 | #3987e5 |

## Data colors
- Categorical, fixed order: `--series-1..8` = blue, orange, aqua, yellow, magenta, green, violet, red (light #2a78d6 #eb6834 #1baf7a #eda100 #e87ba4 #008300 #4a3aa7 #e34948; dark #3987e5 #d95926 #199e70 #c98500 #d55181 #008300 #9085e9 #e66767). Max 3 series per chart (all-pairs safe).
- Series roles: abertos/criados = series-1, resolvidos/fechados = series-3, cancelados = series-2.
- Status (fixed, never a series): `--good` #0ca30c (no prazo), `--serious` #ec835a (estágio vencido), `--critical` #d03b3b (atrasado), `--neutral` = `--ink-3` (sem SLA). Always paired with a text label.
- Ordinal (atraso/idade buckets): blue ramp steps 250→650 (light) / 300→600 (dark): `--ord-1..5`.

## Type & space
- Font: `system-ui, -apple-system, "Segoe UI", sans-serif` everywhere; `tabular-nums` only in tables/axes.
- Sizes: `--fs-xs` 12px, `--fs-sm` 13px, `--fs-md` 14px, `--fs-lg` 18px, `--fs-xl` 28px (KPI value).
- Spacing scale: `--sp-1` 4px, `--sp-2` 8px, `--sp-3` 12px, `--sp-4` 16px, `--sp-6` 24px. Radius `--radius` 8px, marks 4px.

## Components
- Filter bar: one row (wraps) above all content, scopes every chart/table/export; date range first.
- KPI tile: label (sentence case) · value (semibold, compact) · optional status dot + label.
- Chart card: title, subtitle, export buttons (CSV/XLSX) top-right; hover tooltip always on; bars ≤24px, 4px rounded ends; lines 2px; grid hairline solid.
- Tables: sticky header, sortable, tabular numbers, row click drills into filters.
