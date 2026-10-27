"""The manual contract must reject mismatches and never accept placeholders."""

import json
from copy import deepcopy

import pytest

from src.tests.epub_checks import EXPECTED_PATH, assert_expected_epub, load_expected


def example_contract():
    # Synthetic values test the checker; no real source expectations are generated here.
    return {
        "book_title": "Livro sintético",
        "author": "Autor de teste",
        "description_contains": ["descrição com acentuação"],
        "chapter_count": 1,
        "has_cover": True,
        "chapters": [{"title": "Capítulo sintético", "required_text": ["texto obrigatório"],
                      "forbidden_text": ["texto proibido"]}],
    }


def example_actual():
    return {
        "book_title": "Livro sintético",
        "author": "Autor de teste",
        "description": "Uma descrição com acentuação.",
        "chapter_count": 1,
        "has_cover": True,
        "chapters": [{"file": "chap_1.xhtml", "title": "Capítulo sintético", "text": "Um texto obrigatório."}],
    }


def test_populated_contract_is_loaded_and_compared(tmp_path):
    path = tmp_path / "expected.json"
    path.write_text(json.dumps({"example": example_contract()}), encoding="utf-8")
    assert_expected_epub(example_actual(), load_expected("example", path))


def test_placeholder_contract_is_pending(tmp_path):
    contract = example_contract()
    contract["book_title"] = "__PREENCHER__"
    path = tmp_path / "expected.json"
    path.write_text(json.dumps({"example": contract}), encoding="utf-8")
    with pytest.raises(pytest.skip.Exception, match="example.book_title"):
        load_expected("example", path)


@pytest.mark.parametrize("field,value", [
    ("book_title", "Outro livro"),
    ("author", "Outro autor"),
    ("chapter_count", 2),
    ("has_cover", False),
    ("description_contains", ["Descrição inexistente"]),
])
def test_contract_rejects_metadata_mismatches(field, value):
    expected = example_contract()
    expected[field] = value
    with pytest.raises(AssertionError):
        assert_expected_epub(example_actual(), expected)


@pytest.mark.parametrize("field,value", [
    ("title", "Outro capítulo"),
    ("required_text", ["Trecho inexistente"]),
    ("forbidden_text", ["texto obrigatório"]),
])
def test_contract_rejects_chapter_mismatches(field, value):
    expected = deepcopy(example_contract())
    expected["chapters"][0][field] = value
    with pytest.raises(AssertionError):
        assert_expected_epub(example_actual(), expected)


def test_manual_contract_file_has_all_three_sources():
    assert set(json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))) == {"panda", "centralnovel", "novelsbr"}
