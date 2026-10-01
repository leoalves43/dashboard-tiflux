import { describe, expect, it } from "vitest";
import { htmlToText } from "./richText";

describe("htmlToText", () => {
  it("turns block tags into line breaks and strips the rest", () => {
    expect(htmlToText('<div class="x"><div>Bom dia,</div><div><b>segue</b> anexo<br>ok</div></div>')).toBe("Bom dia,\nsegue anexo\nok");
  });

  it("drops scripts and styles with their content", () => {
    expect(htmlToText("<p>a</p><script>alert(1)</script><style>p{}</style><p>b</p>")).toBe("a\nb");
  });

  it("decodes named and numeric entities", () => {
    expect(htmlToText("R&amp;D &lt;3 &#233; &#x41;&nbsp;ok")).toBe("R&D <3 é A ok");
  });

  it("returns empty text for null", () => {
    expect(htmlToText(null)).toBe("");
  });
});
