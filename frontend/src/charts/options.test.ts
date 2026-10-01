import { describe, expect, it } from "vitest";
import { withAlpha } from "./options";

describe("withAlpha", () => {
  it("converts a hex token to rgba with the given alpha", () => {
    expect(withAlpha("#2a78d6", 0.25)).toBe("rgba(42, 120, 214, 0.25)");
  });

  it("rejects colors that are not #rrggbb", () => {
    expect(() => withAlpha("var(--series-1)", 1)).toThrow(/expected "#rrggbb"/);
  });
});
