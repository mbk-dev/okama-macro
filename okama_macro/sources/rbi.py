"""RBI (Reserve Bank of India) current-rates crawler.

Scrapes the "Current Rates" block served in plain server-side HTML on
https://www.rbi.org.in/ — the Policy Repo Rate row of the Policy Rates table.
An HTML scrape is used because RBI exposes no machine-readable feed for the
current policy rate: the DBIE portal (data.rbi.org.in) is an SPA over the CIMS
gateway with no documented public API, and the MOSPI RBI dataset carries annual
publication aggregates behind a registration token. Precedent: the CBR top-10
deposit rate is scraped for the same reason.

Used as the same-day tail on top of the BIS policy-rate history (which publishes
with ~a year's lag) — see ``rates.get_ind_rbi_rate``.
"""

import logging
import re

from lxml import html

from okama_macro import _http

info_logger = logging.getLogger('okama_macro.rbi')

RBI_URL = 'https://www.rbi.org.in/'
API_TIMEOUT = 60  # seconds

_RATE_RE = re.compile(r'(\d+(?:\.\d+)?)\s*%')


def get_current_repo_rate() -> float:
    """Return today's RBI Policy Repo Rate in percent (e.g. ``5.25``).

    Parses the Current Rates table: the ``<td>`` following the ``<th>`` labelled
    "Policy Repo Rate". Raises ``ValueError`` when the row or a percent value is
    missing (site redesign) so the rates update marks the symbol failed instead
    of silently writing nothing.
    """
    info_logger.info('Scraping the current Policy Repo Rate from rbi.org.in')
    response = _http.get(RBI_URL, timeout=API_TIMEOUT, use_proxy=True,
                         label='rbi.org.in current-rates request')
    tree = html.fromstring(response.text)
    for th in tree.xpath('//th'):
        label = ' '.join(th.text_content().split())
        if label == 'Policy Repo Rate':
            cell = th.getnext()
            match = _RATE_RE.search(cell.text_content()) if cell is not None else None
            if match:
                return float(match.group(1))
    raise ValueError('Policy Repo Rate not found on rbi.org.in (page layout changed?)')
