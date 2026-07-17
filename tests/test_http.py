"""Tests for the shared HTTP layer (okama_macro/_http.py)."""

import ssl

import pytest
import requests

from okama_macro import _http


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            err = requests.HTTPError(f'{self.status_code} Error')
            err.response = self
            raise err

    def json(self):
        return self._payload


@pytest.fixture(autouse=True)
def _fast(monkeypatch):
    monkeypatch.setattr(_http.time, 'sleep', lambda *a: None)


def test_sends_browser_user_agent_and_merges_headers(monkeypatch):
    captured = {}

    def fake_get(url, **kwargs):
        captured.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr(_http.requests, 'get', fake_get)

    _http.get('https://example.org', headers={'X-Extra': '1'})

    assert captured['headers']['User-Agent'] == _http.USER_AGENT
    assert captured['headers']['X-Extra'] == '1'
    assert captured['proxies'] is None  # use_proxy=False by default


def test_caller_user_agent_overrides_default(monkeypatch):
    captured = {}

    def fake_get(url, **kwargs):
        captured.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr(_http.requests, 'get', fake_get)

    _http.get('https://example.org', headers={'User-Agent': 'custom-ua'})

    assert captured['headers']['User-Agent'] == 'custom-ua'


def test_retries_transient_5xx_then_succeeds(monkeypatch):
    calls = []
    responses = [FakeResponse(502), FakeResponse(200)]
    monkeypatch.setattr(_http.requests, 'get',
                        lambda url, **k: calls.append(1) or responses[len(calls) - 1])

    response = _http.get('https://example.org')

    assert len(calls) == 2
    assert response.status_code == 200


def test_persistent_5xx_raises_after_max_attempts(monkeypatch):
    calls = []
    monkeypatch.setattr(_http.requests, 'get',
                        lambda url, **k: calls.append(1) or FakeResponse(503))

    with pytest.raises(RuntimeError, match='my-source failed'):
        _http.get('https://example.org', max_attempts=3, label='my-source')

    assert len(calls) == 3


def test_client_error_4xx_fails_fast(monkeypatch):
    calls = []
    monkeypatch.setattr(_http.requests, 'get',
                        lambda url, **k: calls.append(1) or FakeResponse(404))

    with pytest.raises(RuntimeError):
        _http.get('https://example.org')

    assert len(calls) == 1


def test_redacts_secrets_in_error_message(monkeypatch):
    def fake_get(url, **kwargs):
        raise requests.ConnectionError('https://x?api_key=sekret failed')

    monkeypatch.setattr(_http.requests, 'get', fake_get)

    with pytest.raises(RuntimeError) as excinfo:
        _http.get('https://example.org', redact=('sekret',))

    assert 'sekret' not in str(excinfo.value)
    assert '***' in str(excinfo.value)


def test_proxies_from_env_builds_url(monkeypatch):
    monkeypatch.setenv('PROXY_HOST', '127.0.0.1')
    monkeypatch.setenv('PROXY_PORT', '3128')
    monkeypatch.setenv('PROXY_USER', 'u')
    monkeypatch.setenv('PROXY_PASS', 'p')

    assert _http.proxies_from_env() == {
        'http': 'http://u:p@127.0.0.1:3128',
        'https': 'http://u:p@127.0.0.1:3128',
    }


def test_proxies_from_env_none_when_unset(monkeypatch):
    monkeypatch.delenv('PROXY_HOST', raising=False)
    monkeypatch.delenv('PROXY_PORT', raising=False)

    assert _http.proxies_from_env() is None


def test_use_proxy_passes_env_proxies(monkeypatch):
    monkeypatch.setenv('PROXY_HOST', '127.0.0.1')
    monkeypatch.setenv('PROXY_PORT', '3128')
    monkeypatch.delenv('PROXY_USER', raising=False)
    monkeypatch.delenv('PROXY_PASS', raising=False)
    captured = {}

    def fake_get(url, **kwargs):
        captured.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr(_http.requests, 'get', fake_get)

    _http.get('https://example.org', use_proxy=True)

    assert captured['proxies'] == {'http': 'http://127.0.0.1:3128',
                                   'https': 'http://127.0.0.1:3128'}


def test_legacy_tls_session_sets_ua_and_no_verify(monkeypatch):
    monkeypatch.delenv('PROXY_HOST', raising=False)
    monkeypatch.delenv('PROXY_PORT', raising=False)

    session = _http.legacy_tls_session()

    assert session.headers['User-Agent'] == _http.USER_AGENT
    assert session.verify is False
    adapter = session.get_adapter('https://x')
    assert isinstance(adapter, _http._LegacyRenegotiationAdapter)


def test_legacy_adapter_injects_ssl_context_into_direct_pool():
    ctx = ssl.create_default_context()
    adapter = _http._LegacyRenegotiationAdapter(ctx)

    assert adapter.poolmanager.connection_pool_kw.get('ssl_context') is ctx


def test_legacy_adapter_injects_ssl_context_into_proxy_manager():
    # On the production server MOSPI is fetched through the local HAProxy, so
    # the legacy-renegotiation SSL context must reach the proxied pool too —
    # otherwise the tunneled TLS handshake to api.mospi.gov.in loses
    # OP_LEGACY_SERVER_CONNECT and fails with UNSAFE_LEGACY_RENEGOTIATION_DISABLED.
    ctx = ssl.create_default_context()
    adapter = _http._LegacyRenegotiationAdapter(ctx)

    proxy_manager = adapter.proxy_manager_for('http://127.0.0.1:3128')

    assert proxy_manager.connection_pool_kw.get('ssl_context') is ctx


def test_legacy_tls_session_picks_up_env_proxy(monkeypatch):
    monkeypatch.setenv('PROXY_HOST', '127.0.0.1')
    monkeypatch.setenv('PROXY_PORT', '3128')
    monkeypatch.delenv('PROXY_USER', raising=False)
    monkeypatch.delenv('PROXY_PASS', raising=False)

    session = _http.legacy_tls_session()

    assert session.proxies == {'http': 'http://127.0.0.1:3128',
                               'https': 'http://127.0.0.1:3128'}
