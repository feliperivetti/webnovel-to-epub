"""Inspect real EPUBs and compare them to independently entered expectations."""

import json
import re
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

import ebooklib
import pytest
from bs4 import BeautifulSoup
from ebooklib import epub


EXPECTED_PATH = Path(__file__).parent / "fixtures" / "expected.json"


def normalize_text(value):
    return " ".join(value.split())


def inspect_epub(path, cover_bytes, *, allow_error_pages=False):
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None, "Corrupted EPUB ZIP"
        assert archive.read("mimetype") == b"application/epub+zip"
    book = epub.read_epub(str(path))
    metadata = {}
    for key, dc_name in (("book_title", "title"), ("author", "creator"), ("description", "description")):
        records = book.get_metadata("DC", dc_name)
        assert len(records) == 1 and records[0][0], f"Missing or ambiguous EPUB metadata: {key}"
        metadata[key] = records[0][0]

    def toc_links(entries):
        for entry in entries:
            if isinstance(entry, (tuple, list)):
                yield from toc_links(entry)
            elif getattr(entry, "href", None):
                yield entry

    toc = {urlsplit(link.href).path: link.title for link in toc_links(book.toc)}
    spine_ids = [entry[0] for entry in book.spine]
    chapter_items = [
        item for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT)
        if re.fullmatch(r"chap_\d+\.xhtml", item.file_name)
    ]
    assert chapter_items, "EPUB contains no chapter documents"
    assert all(item.get_id() in spine_ids for item in chapter_items), "Chapter missing from reading order"
    chapter_items.sort(key=lambda item: spine_ids.index(item.get_id()))
    chapters = []
    for item in chapter_items:
        soup = BeautifulSoup(item.get_content(), "html.parser")
        heading = soup.find("h1")
        story = soup.select_one("section > div")
        assert heading is not None and story is not None, f"Missing chapter markup: {item.file_name}"
        title = heading.get_text(" ", strip=True)
        text = normalize_text(story.get_text(" ", strip=True))
        assert title and text, f"Empty chapter: {item.file_name}"
        if not allow_error_pages:
            assert "Error Chapter" not in title
            assert "Content could not be downloaded." not in text
        assert item.file_name in toc, f"Chapter missing from table of contents: {item.file_name}"
        assert toc[item.file_name] == title, "TOC label differs from chapter heading"
        chapters.append({"file": item.file_name, "title": title, "text": text})

    nav = book.get_item_with_id("nav")
    assert nav is not None, "Missing EPUB navigation document"
    nav_soup = BeautifulSoup(nav.get_content(), "html.parser")
    nav_targets = {urlsplit(a["href"]).path for a in nav_soup.select("a[href]")}
    assert all(chapter["file"] in nav_targets for chapter in chapters)
    cover = book.get_item_with_id("cover-img")
    assert cover is not None and cover.get_content() == cover_bytes, "Cover was not embedded correctly"
    return {**metadata, "chapter_count": len(chapters), "has_cover": True, "chapters": chapters}


def pending_fields(value, path):
    if value is None or isinstance(value, str) and "__PREENCHER" in value:
        return [path]
    if isinstance(value, dict):
        return [pending for key, child in value.items() for pending in pending_fields(child, f"{path}.{key}")]
    if isinstance(value, list):
        return [pending for i, child in enumerate(value) for pending in pending_fields(child, f"{path}[{i}]")]
    return []


def load_expected(source, path=EXPECTED_PATH):
    data = json.loads(path.read_text(encoding="utf-8"))
    assert source in data and isinstance(data[source], dict), f"Missing source {source!r} in {path}"
    expected = data[source]
    required = {"book_title", "author", "description_contains", "chapter_count", "has_cover", "chapters"}
    assert required <= expected.keys(), f"Missing fields in {source}: {required - expected.keys()}"
    pending = pending_fields(expected, source)
    if pending:
        pytest.skip(f"Fill {path}: {', '.join(pending)}")
    for key in ("book_title", "author"):
        assert isinstance(expected[key], str) and expected[key].strip(), f"{source}.{key} must be a nonempty string"
    assert isinstance(expected["chapter_count"], int) and not isinstance(expected["chapter_count"], bool)
    assert expected["chapter_count"] > 0
    assert isinstance(expected["has_cover"], bool)
    assert isinstance(expected["chapters"], list) and len(expected["chapters"]) == expected["chapter_count"]
    assert isinstance(expected["description_contains"], list)
    for chapter in expected["chapters"]:
        assert {"title", "required_text", "forbidden_text"} <= chapter.keys()
        assert isinstance(chapter["title"], str) and chapter["title"].strip()
        assert isinstance(chapter["required_text"], list) and chapter["required_text"]
        assert isinstance(chapter["forbidden_text"], list)
        for snippet in chapter["required_text"] + chapter["forbidden_text"]:
            assert isinstance(snippet, str) and snippet.strip(), "Text snippets must be nonempty strings"
    assert all(isinstance(text, str) and text.strip() for text in expected["description_contains"])
    return expected


def assert_expected_epub(actual, expected):
    for key in ("book_title", "author", "chapter_count", "has_cover"):
        assert actual[key] == expected[key], f"Unexpected {key}: {actual[key]!r} != {expected[key]!r}"
    for snippet in expected["description_contains"]:
        assert normalize_text(snippet) in normalize_text(actual["description"]), f"Description missing: {snippet!r}"
    assert len(actual["chapters"]) == len(expected["chapters"])
    for chapter, wanted in zip(actual["chapters"], expected["chapters"]):
        assert chapter["title"] == wanted["title"], f"Unexpected title for {chapter['file']}"
        for snippet in wanted["required_text"]:
            assert normalize_text(snippet) in chapter["text"], f"{chapter['file']} missing: {snippet!r}"
        for snippet in wanted["forbidden_text"]:
            assert normalize_text(snippet) not in chapter["text"], f"{chapter['file']} contains: {snippet!r}"
