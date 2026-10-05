import { describe, expect, it } from "vitest";
import {
  type ColumnLayout, LAYOUT_STORAGE_KEY, type LayoutStorage, loadLayout, moveColumn, reconcileLayout, saveLayout,
  toggleColumn, visibleKeys,
} from "./columnLayout";

const DEFAULTS: ColumnLayout = [
  { key: "a", visible: true },
  { key: "b", visible: true },
  { key: "c", visible: false },
];

/** In-memory Storage double; `failing` makes every call throw like a blocked localStorage. */
class FakeStorage implements LayoutStorage {
  readonly items = new Map<string, string>();
  constructor(private readonly failing = false) {}
  getItem(key: string): string | null {
    if (this.failing) throw new Error("storage blocked");
    return this.items.get(key) ?? null;
  }
  setItem(key: string, value: string): void {
    if (this.failing) throw new Error("storage blocked");
    this.items.set(key, value);
  }
}

describe("reconcileLayout", () => {
  it("keeps saved order, drops unknown keys and appends new ones with default visibility", () => {
    const saved = [{ key: "b", visible: false }, { key: "gone", visible: true }, { key: "a", visible: true }];
    expect(reconcileLayout(saved, DEFAULTS)).toEqual([
      { key: "b", visible: false }, { key: "a", visible: true }, { key: "c", visible: false },
    ]);
  });

  it.each([null, "x", [{ key: 1 }], [{ key: "a", visible: false }, { key: "b", visible: false }]])(
    "falls back to defaults for %j", (saved) => {
      expect(reconcileLayout(saved, DEFAULTS)).toBe(DEFAULTS);
    });
});

describe("layout edits", () => {
  it("moves a column and ignores out-of-range targets", () => {
    expect(moveColumn(DEFAULTS, 2, 0).map((s) => s.key)).toEqual(["c", "a", "b"]);
    expect(moveColumn(DEFAULTS, 0, 5)).toBe(DEFAULTS);
  });

  it("toggles visibility but never hides the last visible column", () => {
    const onlyA = toggleColumn(DEFAULTS, "b");
    expect(visibleKeys(onlyA)).toEqual(["a"]);
    expect(toggleColumn(onlyA, "a")).toBe(onlyA);
    expect(visibleKeys(toggleColumn(onlyA, "c"))).toEqual(["a", "c"]);
  });
});

describe("layout storage", () => {
  it("round-trips through storage", () => {
    const storage = new FakeStorage();
    const layout = moveColumn(DEFAULTS, 1, 0);
    saveLayout(storage, layout);
    expect(loadLayout(storage, DEFAULTS)).toEqual(layout);
  });

  it("returns defaults on corrupt JSON, missing or throwing storage", () => {
    const corrupt = new FakeStorage();
    corrupt.items.set(LAYOUT_STORAGE_KEY, "{not json");
    expect(loadLayout(corrupt, DEFAULTS)).toBe(DEFAULTS);
    expect(loadLayout(undefined, DEFAULTS)).toBe(DEFAULTS);
    expect(loadLayout(new FakeStorage(true), DEFAULTS)).toBe(DEFAULTS);
    expect(() => saveLayout(new FakeStorage(true), DEFAULTS)).not.toThrow();
  });
});
