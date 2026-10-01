import pytest

from app.ticket_activity import load_activity, load_description, map_file
from app.tiflux.client import TifluxNotFound
from tests.fakes import FakeActivitySource

# Shapes copied from a real Tiflux response (2026-10-01): ids and sizes arrive as strings.
FILE = {"id": "14381332", "content_type": "image/png", "file_name": "erro.png", "size": "101411", "url": "https://s3/x"}
ANSWER_WITH_FILE = {"id": "31826996", "answer_time": "2026-10-01T13:05:47Z", "author": "Cliente",
                    "files_count": "1", "name": "<div>Deu certo</div>"}
ANSWER = {"id": "31827101", "answer_time": "2026-10-01T13:08:04Z", "author": "Técnica", "files_count": "0",
          "name": "<div>Imagina!!</div>"}
INTERNAL = {"id": "9", "created_at": "2026-10-01T13:06:00Z", "files_count": 0, "text": "ver com infra",
            "user": {"id": 1, "name": "Coordenador"}}


def _source(**kwargs: bool) -> FakeActivitySource:
    return FakeActivitySource(
        lists={"/tickets/7/files": [FILE], "/tickets/7/answers": [ANSWER, ANSWER_WITH_FILE],
               "/tickets/7/internal_communications": [INTERNAL]},
        details={"/tickets/7/answers/31826996": {**ANSWER_WITH_FILE, "files": [FILE]}},
        **kwargs,
    )


def test_map_file_converts_string_numbers() -> None:
    assert map_file(FILE) == {"id": 14381332, "file_name": "erro.png", "content_type": "image/png",
                              "size": 101411, "url": "https://s3/x"}


def test_load_activity_merges_followups_in_chronological_order() -> None:
    activity = load_activity(_source(), 7)
    kinds = [(f["kind"], f["author"]) for f in activity["followups"]]
    assert kinds == [("answer", "Cliente"), ("internal", "Coordenador"), ("answer", "Técnica")]
    assert activity["followups"][1]["text"] == "ver com infra"
    assert activity["files"][0]["file_name"] == "erro.png"


def test_load_activity_fetches_detail_only_for_followups_with_files() -> None:
    source = _source()
    activity = load_activity(source, 7)
    assert [c for c in source.calls if c.count("/") == 4] == ["/tickets/7/answers/31826996"]
    assert activity["followups"][0]["files"][0]["id"] == 14381332
    assert activity["followups"][2]["files"] == []


def test_load_activity_of_ticket_without_history_is_empty() -> None:
    assert load_activity(FakeActivitySource(lists={}), 8) == {"files": [], "followups": []}


def test_load_activity_propagates_missing_ticket() -> None:
    with pytest.raises(TifluxNotFound):
        load_activity(_source(missing=True), 7)


def test_load_description_reads_ticket_detail() -> None:
    source = FakeActivitySource(lists={}, details={"/tickets/7": {"description": "<p>Sem acesso</p>"}})
    assert load_description(source, 7) == "<p>Sem acesso</p>"


def test_load_description_raises_when_ticket_is_gone() -> None:
    with pytest.raises(TifluxNotFound):
        load_description(FakeActivitySource(lists={}), 7)
