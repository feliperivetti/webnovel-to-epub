import json
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from src.diagnostics import ScraperDiagnostics, create_scraper, main


FIXTURES = Path(__file__).parent / "fixtures"
SOURCES = [
    ("https://royalroad.com/fiction/123/test", "royalroad"),
    # Registry currently uses the NovelFire alias for the Panda/NovelPhoenix parser.
    ("https://novelfire.net/book/shadow-slave", "pandanovel"),
    ("https://novels-br.com/novels/escravo-das-sombras", "novelsbr"),
    ("https://centralnovel.com/series/shadow-slave-20260913/", "centralnovel"),
]


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Diagnostic unit tests must not access the network")
    monkeypatch.setattr(requests.sessions.Session, "request", forbidden)


@pytest.mark.parametrize("url,source", SOURCES)
@pytest.mark.parametrize("stage,suffix", [("chapter", "chap"), ("metadata", "toc")])
def test_offline_uses_existing_parsers(url, source, stage, suffix, tmp_path):
    code = main([
        url, "--stage", stage, "--html", str(FIXTURES / f"{source}_{suffix}.html"),
        "--output-dir", str(tmp_path),
    ])
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert code == 0
    assert report["ok"] is True
    assert report["mode"] == "offline"
    assert report["requests"][0]["offline"] is True
    if stage == "chapter":
        assert report["requests"][0]["selectors"]["chap_content"] == 1
        assert len((tmp_path / "chapter-001.txt").read_text(encoding="utf-8")) > 10


@pytest.mark.parametrize("status,body", [
    (200, "<html><title>Loading...</title></html>"),
    (200, '<div class="chapter-inner chapter-content"><p> </p></div>'),
    (403, "<html><title>Access denied</title><p>Verify you are human</p></html>"),
])
def test_failed_chapter_preserves_http_evidence(status, body, tmp_path):
    scraper = create_scraper(SOURCES[0][0], direct=True)
    response = requests.Response()
    response.status_code = status
    response.url = "https://royalroad.com/chapter/1"
    response._content = body.encode()
    response.encoding = "utf-8"
    scraper._session.request = Mock(return_value=response)
    diagnostics = ScraperDiagnostics(scraper, tmp_path, selectors=["title"])
    with diagnostics.capture():
        assert diagnostics.step("chapter", lambda: diagnostics.chapter(response.url)) is None
    assert diagnostics.save_report() is False
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["requests"][0]["status"] == status
    assert (tmp_path / "response-01.html").read_text() == body
    assert not (tmp_path / "chapter-001.txt").exists()
    if status == 403:
        assert report["steps"][0]["error_type"] == "HTTPError"
        assert "access denied" in report["requests"][0]["possible_block_markers"]
    else:
        assert report["steps"][0]["error_type"] == "ValueError"
    scraper._session.close()


def test_transport_error_is_reported_and_credentials_redacted(tmp_path, capsys):
    scraper = create_scraper(SOURCES[0][0], direct=True)
    scraper.settings = scraper.settings.model_copy(update={"API_JWT_SECRET": "test-secret-value"})
    request = Mock(side_effect=requests.exceptions.ProxyError(
        "Failed https://user:password@proxy.example:8080 test-secret-value"
    ))
    scraper._session.request = request
    diagnostics = ScraperDiagnostics(scraper, tmp_path, timeout=4)
    with diagnostics.capture():
        diagnostics.step("chapter", lambda: diagnostics.chapter("https://royalroad.com/chapter/1"), True)
    assert scraper._session.request is request
    assert diagnostics.save_report() is False
    report_text = (tmp_path / "report.json").read_text()
    assert json.loads(report_text)["requests"][0]["error_type"] == "ProxyError"
    for output in (report_text, capsys.readouterr().out):
        assert "password" not in output
        assert "test-secret-value" not in output
    assert request.call_args.kwargs["timeout"] == 4
    scraper._session.close()


def test_links_stage_does_not_claim_chapter_download_succeeded(tmp_path):
    assert main([SOURCES[1][0], "--stage", "links", "--qty", "2", "--output-dir", str(tmp_path)]) == 0
    report = json.loads((tmp_path / "report.json").read_text())
    assert report["requests"] == []  # Panda generates links without fetching the TOC.
    assert [step["name"] for step in report["steps"]] == ["links"]
    assert len(report["steps"][0]["result"]) == 2


def test_direct_mode_overrides_only_the_scraper_instance():
    from src.config import get_settings

    settings = get_settings()
    original_proxy = settings.PROXY_URL
    scraper = create_scraper(SOURCES[1][0], direct=True)
    assert scraper.settings is not settings
    assert scraper.settings.PROXY_URL is None
    assert scraper.settings.PROXY_URL_FALLBACK is None
    assert scraper._session.proxies == {}
    assert scraper._session.trust_env is False
    assert settings.PROXY_URL == original_proxy
    scraper._session.close()


def test_offline_requires_a_single_stage(tmp_path):
    with pytest.raises(SystemExit) as exc:
        main([SOURCES[1][0], "--html", str(FIXTURES / "pandanovel_chap.html"),
              "--output-dir", str(tmp_path)])
    assert exc.value.code == 2


def test_anubis_evidence_is_saved_without_claiming_layout_change(tmp_path):
    assert main([
        SOURCES[0][0], "--stage", "metadata", "--html", str(FIXTURES / "royalroad_anubis.html"),
        "--output-dir", str(tmp_path),
    ]) == 1
    report = json.loads((tmp_path / "report.json").read_text())
    assert report["steps"][0]["error_type"] == "AntiBotChallengeException"
    assert "anubis_challenge" in report["requests"][0]["possible_block_markers"]
    assert (tmp_path / "response-01.html").is_file()


@pytest.mark.parametrize("arguments", [
    ["--headed"],
    ["--pause"],
    ["--browser", "msedge", "--pause"],
    ["--browser", "msedge", "--html", str(FIXTURES / "royalroad_toc.html"), "--stage", "metadata"],
])
def test_invalid_browser_combinations_fail_before_browser_launch(arguments):
    with pytest.raises(SystemExit) as exc:
        main([SOURCES[0][0], *arguments])
    assert exc.value.code == 2
