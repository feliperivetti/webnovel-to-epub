"""Check connectivity diagnostics without exposing proxy credentials."""

from unittest.mock import Mock

import pytest
import requests

from src.main import debug_proxy, settings


@pytest.fixture
def proxy_url(monkeypatch):
    url = "http://private-user:private-password@proxy.example:8080"
    monkeypatch.setattr(settings, "PROXY_URL", url)
    return url


def test_proxy_check_uses_configured_endpoint(mocker, proxy_url):
    response = Mock()
    response.json.return_value = {"ip": "192.0.2.10"}
    get = mocker.patch("src.main.requests.get", return_value=response)
    result = debug_proxy()
    assert result["proxy_configured"] is True
    assert result["server_ip_check"] == "192.0.2.10"
    assert result["error"] is None
    assert "private-user" not in str(result)
    assert "private-password" not in str(result)
    assert get.call_args.kwargs["proxies"] == {"http": proxy_url, "https": proxy_url}
    response.raise_for_status.assert_called_once()


def test_proxy_errors_do_not_disclose_credentials(mocker, proxy_url, caplog):
    mocker.patch("src.main.requests.get", side_effect=requests.exceptions.ProxyError(proxy_url))
    result = debug_proxy()
    assert result["server_ip_check"] == "Failed"
    assert result["error"] == "ProxyError"
    for output in (str(result), caplog.text):
        assert "private-user" not in output
        assert "private-password" not in output


def test_proxy_check_rejects_http_error(mocker, proxy_url):
    response = Mock()
    response.raise_for_status.side_effect = requests.exceptions.HTTPError(proxy_url)
    mocker.patch("src.main.requests.get", return_value=response)
    result = debug_proxy()
    assert result["server_ip_check"] == "Failed"
    assert result["error"] == "HTTPError"
    response.json.assert_not_called()


def test_proxy_check_without_configured_proxy(mocker, monkeypatch):
    monkeypatch.setattr(settings, "PROXY_URL", "")
    response = Mock()
    response.json.return_value = {"ip": "192.0.2.20"}
    get = mocker.patch("src.main.requests.get", return_value=response)
    result = debug_proxy()
    assert result["proxy_configured"] is False
    assert result["proxy_url_masked"] is None
    assert get.call_args.kwargs["proxies"] is None
