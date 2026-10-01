from app.rich_text import html_to_text


def test_block_tags_become_line_breaks() -> None:
    html = '<div class="x"><div>Bom dia,</div><div><b>segue</b> anexo<br>ok</div></div>'
    assert html_to_text(html) == "Bom dia,\nsegue anexo\nok"


def test_script_and_style_are_dropped_with_content() -> None:
    assert html_to_text("<p>a</p><script>alert(1)</script><style>p{}</style><p>b</p>") == "a\nb"


def test_entities_are_decoded() -> None:
    assert html_to_text("R&amp;D &lt;3 &#233; &#x41;&nbsp;ok") == "R&D <3 é A ok"


def test_empty_input_gives_empty_text() -> None:
    assert html_to_text(None) == ""
    assert html_to_text("") == ""


def test_plain_text_passes_through() -> None:
    assert html_to_text("ticket encerrado conforme chat.") == "ticket encerrado conforme chat."
