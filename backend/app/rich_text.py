"""Tiflux HTML -> plain text for exports; same rules as frontend/src/richText.ts."""

from html.parser import HTMLParser

_BLOCK_TAGS = frozenset({"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "blockquote"})
_DROPPED_TAGS = frozenset({"script", "style"})


class _TextCollector(HTMLParser):
    """Keeps text, turns block ends and <br> into line breaks, skips script/style content."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._dropping = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _DROPPED_TAGS:
            self._dropping += 1
        elif tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _DROPPED_TAGS:
            self._dropping = max(0, self._dropping - 1)
        elif tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._dropping:
            self.parts.append(data.replace("\xa0", " "))


def _tidy(text: str) -> str:
    lines = [line.rstrip() for line in text.split("\n")]
    tidy = "\n".join(lines)
    while "\n\n\n" in tidy:
        tidy = tidy.replace("\n\n\n", "\n\n")
    return tidy.strip()


def html_to_text(html: str | None) -> str:
    """Example: html_to_text("<p>Oi</p><p>Tudo</p>") == "Oi\\nTudo" """
    if not html:
        return ""
    collector = _TextCollector()
    collector.feed(html)
    collector.close()
    return _tidy("".join(collector.parts))
