import { describe, expect, it } from "vitest";
import { fmtBytes } from "./format";

describe("fmtBytes", () => {
  it("scales to the largest whole unit", () => {
    expect(fmtBytes(101411)).toBe("99,0 KB");
    expect(fmtBytes(5 * 1024 * 1024)).toBe("5,0 MB");
  });

  it("keeps bytes as integers and dashes missing sizes", () => {
    expect(fmtBytes(512)).toBe("512 B");
    expect(fmtBytes(null)).toBe("–");
  });
});
