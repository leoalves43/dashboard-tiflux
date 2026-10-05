/** Which ticket-table columns are shown, and in what order (spec 004). Pure functions + storage I/O. */
export interface ColumnSlot {
  key: string;
  visible: boolean;
}
export type ColumnLayout = ColumnSlot[];
export type LayoutStorage = Pick<Storage, "getItem" | "setItem">;

// Bump the suffix only if the stored shape changes; added/removed columns are reconciled instead.
export const LAYOUT_STORAGE_KEY = "ticketColumns.v1";

function isSlot(value: unknown): value is ColumnSlot {
  if (typeof value !== "object" || value === null) return false;
  const slot = value as Record<string, unknown>;
  return typeof slot.key === "string" && typeof slot.visible === "boolean";
}

/**
 * Saved layout adapted to the current columns: unknown keys dropped, new ones appended with their
 * default visibility, anything malformed (or nothing visible) falls back to the defaults.
 * Example: reconcileLayout(JSON.parse(raw), DEFAULT_LAYOUT)
 */
export function reconcileLayout(saved: unknown, defaults: ColumnLayout): ColumnLayout {
  if (!Array.isArray(saved) || !saved.every(isSlot)) return defaults;
  const known = new Map(defaults.map((slot) => [slot.key, slot]));
  const seen = new Set<string>();
  const kept = saved.filter((slot) => known.has(slot.key) && !seen.has(slot.key) && seen.add(slot.key));
  const added = defaults.filter((slot) => !seen.has(slot.key));
  const layout = [...kept.map(({ key, visible }) => ({ key, visible })), ...added];
  return layout.some((slot) => slot.visible) ? layout : defaults;
}

/** Moves the slot at `from` to index `to`. Example: moveColumn(layout, 3, 0) */
export function moveColumn(layout: ColumnLayout, from: number, to: number): ColumnLayout {
  if (from === to || to < 0 || to >= layout.length) return layout;
  const next = [...layout];
  const [moved] = next.splice(from, 1);
  next.splice(to, 0, moved);
  return next;
}

/** Shows/hides one column; the last visible column cannot be hidden. Example: toggleColumn(layout, "title") */
export function toggleColumn(layout: ColumnLayout, key: string): ColumnLayout {
  if (isLastVisible(layout, key)) return layout;
  return layout.map((slot) => (slot.key === key ? { ...slot, visible: !slot.visible } : slot));
}

export function isLastVisible(layout: ColumnLayout, key: string): boolean {
  const visible = layout.filter((slot) => slot.visible);
  return visible.length === 1 && visible[0].key === key;
}

export function visibleKeys(layout: ColumnLayout): string[] {
  return layout.filter((slot) => slot.visible).map((slot) => slot.key);
}

/** Stored layout or the defaults; storage may be missing or throw (private mode, quota). */
export function loadLayout(storage: LayoutStorage | undefined, defaults: ColumnLayout): ColumnLayout {
  try {
    const raw = storage?.getItem(LAYOUT_STORAGE_KEY);
    return raw ? reconcileLayout(JSON.parse(raw), defaults) : defaults;
  } catch {
    return defaults;
  }
}

export function saveLayout(storage: LayoutStorage | undefined, layout: ColumnLayout): void {
  try {
    storage?.setItem(LAYOUT_STORAGE_KEY, JSON.stringify(layout));
  } catch {
    // Preference only lasts for this page view; the table keeps working.
  }
}
