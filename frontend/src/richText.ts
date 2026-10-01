// Tiflux descriptions and answers arrive as HTML. They are shown as plain text (React escapes it),
// so nothing from Tiflux is ever interpreted as markup or script.
const BLOCK_END = /<\/(p|div|li|h[1-6]|tr|blockquote)\s*>|<br\s*\/?>/gi;
const TAG = /<[^>]*>/g;
const DROPPED = /<(script|style)[^>]*>[\s\S]*?<\/\1\s*>/gi;
const NAMED_ENTITIES: Record<string, string> = { nbsp: " ", amp: "&", lt: "<", gt: ">", quot: '"', apos: "'" };

function decodeEntities(text: string): string {
  return text.replace(/&(#x[0-9a-f]+|#\d+|[a-z]+);/gi, (match, code: string) => {
    if (code[0] !== "#") return NAMED_ENTITIES[code.toLowerCase()] ?? match;
    const value = code[1].toLowerCase() === "x" ? parseInt(code.slice(2), 16) : parseInt(code.slice(1), 10);
    return Number.isFinite(value) ? String.fromCodePoint(value) : match;
  });
}

/** Tiflux HTML -> readable plain text with line breaks. Example: htmlToText("<p>Oi</p><p>Tudo</p>") === "Oi\nTudo" */
export function htmlToText(html: string | null | undefined): string {
  if (!html) return "";
  const text = html.replace(DROPPED, "").replace(BLOCK_END, "\n").replace(TAG, "");
  return decodeEntities(text).replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n").trim();
}
