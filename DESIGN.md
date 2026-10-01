# DESIGN — Dashboard Tiflux

Tokens live in `frontend/src/styles/tokens.css` as CSS custom properties; components and charts read only these roles (charts via `frontend/src/charts/theme.ts`). No hex, spacing or font outside the token file.
Palette = dataviz skill reference instance (validated; categorical order is the CVD-safety mechanism — never reorder).

## Surfaces & ink
| Role | Light | Dark |
|---|---|---|
| `--page` | #f3f5fa | #0b0f17 |
| `--surface` (cards, charts) | #ffffff | #131a26 |
| `--surface-2` (hover, inputs) | #eef1f7 | #1c2433 |
| `--ink-1` primary | #0b0b0b | #ffffff |
| `--ink-2` secondary | #4b5163 | #c5cad6 |
| `--ink-3` muted / axis | #7f8698 | #8b93a7 |
| `--grid` hairline | #e3e7ef | #253043 |
| `--axis` baseline | #c5ccd9 | #34405a |
| `--border` | rgba(11,11,11,.10) | rgba(255,255,255,.10) |
| `--accent` (focus, selection) | #2a78d6 | #3987e5 |

## Data colors
- Categorical, fixed order: `--series-1..8` = blue, orange, aqua, yellow, magenta, green, violet, red (light #2a78d6 #eb6834 #1baf7a #eda100 #e87ba4 #008300 #4a3aa7 #e34948; dark #3987e5 #d95926 #199e70 #c98500 #d55181 #008300 #9085e9 #e66767). Max 3 series per chart (all-pairs safe).
- Series roles: abertos/criados = series-1, resolvidos/fechados = series-3, cancelados = series-2.
- Status (fixed, never a series): `--good` #0ca30c (no prazo), `--serious` #ec835a (estágio vencido), `--critical` #d03b3b (atrasado), `--neutral` = `--ink-3` (sem SLA). Always paired with a text label.
- Ordinal (atraso/idade buckets): blue ramp steps 250/350/450/550/650 (light) / 150/300/400/500/600 (dark): `--ord-1..5` (validated `--ordinal` on both surfaces).

## Color accents (chrome, not data)
- Surfaces are slightly cool-tinted; the palette was re-validated against `#ffffff` / `#131a26` (series-3 on light is 2.82:1 → relief via legend + table views).
- `--brand-gradient` = series-1 → series-7 (blue → violet): brand mark, 2px line under the top bar, card-title marker. Never on data marks.
- Tone: an element sets `--tone` to a series/status token; CSS derives its wash with `color-mix(... var(--tone) 14%, transparent)`. Text stays in ink tokens; tone only colors stripes, dots and washes.
- KPI tones: total = series-7, abertos = series-1, fechados = series-3, no prazo = `--good`, atrasados & dias de atraso = `--critical`, estágio vencido = `--serious`, tempo de resolução = series-4.
- Pills (tables): situação uses series roles (aberto 1, fechado 3, cancelado 2); SLA uses status colors; always dot + label.

## Type & space
- Font: `system-ui, -apple-system, "Segoe UI", sans-serif` everywhere; `tabular-nums` only in tables/axes.
- Sizes: `--fs-xs` 12px, `--fs-sm` 13px, `--fs-md` 14px, `--fs-lg` 18px, `--fs-xl` 28px (KPI value).
- Spacing scale: `--sp-1` 4px, `--sp-2` 8px, `--sp-3` 12px, `--sp-4` 16px, `--sp-6` 24px. Radius `--radius` 8px, marks 4px.

## Components
- Filter bar: one row (wraps) above all content, scopes every chart/table/export; date range first.
- KPI tile: 3px tone stripe on top, tone wash fading down · label (sentence case) · value (semibold, compact, ink) · optional status dot + label.
- Chart card: soft shadow (`--shadow-sm`), gradient marker before the title, subtitle, export buttons (CSV/XLSX) top-right; hover tooltip always on; bars ≤24px, 4px rounded ends; lines 2px with a vertical gradient area (tone 25% → 0); grid hairline solid.
- Tables: sticky header, sortable, tabular numbers, row click drills into filters.
- Ticket hover card: appears 400 ms after the pointer rests on a ticket row, hides on leave; fixed near the pointer, flipped to stay in the viewport; `--surface`, `--border`, `--shadow`, radius `--radius`, max 420px wide, brand-gradient 3px top stripe; non-interactive (`pointer-events: none`). Shows the 9 summary fields (label `--ink-3` `--fs-xs`, value `--ink-1`), description clamped to 6 lines.
- Ticket modal: overlay = `--ink-1` at 45% over the page; panel `--surface`, max 880px × 90vh, scrolls inside, brand-gradient top stripe; header = nº + título + situação pill + close button. Sections: Detalhes (field grid), Descrição (pre-wrap text), Anexos (file name link · type · size), Follow-ups (timeline). Closes on Esc, backdrop click, close button; focus returns to the row.
- Follow-up item: 3px left border in its tone + pill — resposta = series-1, interna = series-4; author `--ink-1` semibold, date `--ink-3`, text pre-wrap, files listed below.
