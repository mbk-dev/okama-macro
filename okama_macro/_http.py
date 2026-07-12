"""Shared HTTP plumbing for all okama-macro source clients.

``get()`` is a plain GET with a browser-like User-Agent (several statistical
agencies reject the default python-requests UA), an optional outbound proxy
taken from the ``PROXY_*`` environment variables, and linear-back-off retries
on transient upstream 5xx responses. 4xx responses and hard connection errors
fail fast. On failure it raises ``RuntimeError`` with the ``redact`` strings
masked so API keys never leak into logs. ``legacy_tls_session()`` (Task 3)
serves endpoints that need OpenSSL legacy server renegotiation.
"""

import logging
import os
import ssl
import time

import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3 import PoolManager

info_logger = logging.getLogger('okama_macro.http')

DEFAULT_TIMEOUT = 60  # seconds
USER_AGENT = 'Mozilla/5.0 (okama-data pipeline)'


def proxies_from_env() -> dict[str, str] | None:
    """Build the requests proxies dict from PROXY_* env vars, or None if unset.

    Foreign sources go through the local HAProxy on the production server;
    without the env vars (e.g. in tests) requests go direct.
    """
    host, port = os.getenv('PROXY_HOST'), os.getenv('PROXY_PORT')
    if not (host and port):
        return None
    user, password = os.getenv('PROXY_USER'), os.getenv('PROXY_PASS')
    auth = f'{user}:{password}@' if user and password else ''
    url = f'http://{auth}{host}:{port}'
    return {'http': url, 'https': url}


class _LegacyRenegotiationAdapter(HTTPAdapter):
    """HTTPAdapter enabling OpenSSL legacy server connect (api.mospi.gov.in)."""

    def __init__(self, ssl_context: ssl.SSLContext, **kwargs):
        self._ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        pool_kwargs['ssl_context'] = self._ssl_context
        self.poolmanager = PoolManager(
            num_pools=connections, maxsize=maxsize, block=block, **pool_kwargs,
        )


def get(url: str,
        *,
        params: dict | None = None,
        headers: dict | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_attempts: int = 3,
        backoff: float = 1.0,
        use_proxy: bool = False,
        redact: tuple[str, ...] = (),
        label: str = 'request') -> requests.Response:
    """GET ``url`` with UA/proxy defaults and linear-back-off retries on 5xx.

    Caller-supplied ``headers`` are merged over the defaults, so an explicit
    ``User-Agent`` from the caller wins.
    """
    merged_headers = {'User-Agent': USER_AGENT} | (headers or {})
    proxies = proxies_from_env() if use_proxy else None
    for attempt in range(max_attempts):
        try:
            response = requests.get(url, params=params, headers=merged_headers,
                                    timeout=timeout, proxies=proxies)
            response.raise_for_status()
            return response
        except requests.RequestException as error:
            resp = getattr(error, 'response', None)
            transient = resp is not None and resp.status_code >= 500
            if transient and attempt < max_attempts - 1:
                info_logger.warning(
                    f'{label}: HTTP {resp.status_code}; '
                    f'retry {attempt + 1}/{max_attempts - 1}'
                )
                time.sleep(backoff * (attempt + 1))
                continue
            message = str(error)
            for secret in redact:
                message = message.replace(secret, '***')
            raise RuntimeError(f'{label} failed: {message}') from None
    msg = f'{label} failed after {max_attempts} attempts'
    raise RuntimeError(msg)  # pragma: no cover


def legacy_tls_session() -> requests.Session:
    """A Session for endpoints needing legacy TLS renegotiation (MOSPI).

    Verification is disabled (the endpoint presents a chain OpenSSL rejects) —
    the same workaround as MOSPI's own reference client. UA and env proxies
    are preset.
    """
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    ssl_context = ssl.create_default_context()
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_context.options |= getattr(ssl, 'OP_LEGACY_SERVER_CONNECT', 0x4)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})
    session.verify = False
    session.mount('https://', _LegacyRenegotiationAdapter(ssl_context))
    proxies = proxies_from_env()
    if proxies:
        session.proxies = proxies
    return session
