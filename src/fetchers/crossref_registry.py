"""Look up DOIs already registered at Crossref, straight from Crossref itself.

EXCLUDED_CODES in publications.py is a hand-maintained list and it WILL go
stale the moment someone submits a batch to Crossref without updating it
(this happened 2026-05-29: batches 005/006 were submitted but never added to
the list, and two more manual batches -003, -004- were submitted in between
without ever being recorded in this repo at all). This module fetches the
real, current list directly from Crossref's public API so that mistake can't
silently repeat -- it's used as a second, always-current filter on top of
EXCLUDED_CODES, not a replacement for it.
"""

import re
import logging
from typing import Set

import requests

logger = logging.getLogger(__name__)

_CODE_PATTERN = re.compile(r'^10\.\d+/pi-(.+)$', re.IGNORECASE)


def fetch_registered_codes(prefix: str, timeout: int = 30) -> Set[str]:
    """Return normalized codes (e.g. {"VL102", "EC10001", ...}) already
    registered at Crossref under `prefix` (both publication and section DOIs).

    Returns an empty set if Crossref can't be reached. Callers should treat
    an empty result as "unknown" and fall back to EXCLUDED_CODES alone rather
    than assuming nothing is registered.
    """
    codes = set()
    cursor = "*"
    url = f"https://api.crossref.org/prefixes/{prefix}/works"
    headers = {"User-Agent": "PI-DOI-generator/1.0 (mailto:services@psychcampus.com)"}

    try:
        while True:
            resp = requests.get(
                url,
                params={"rows": 1000, "cursor": cursor},
                headers=headers,
                timeout=timeout,
            )
            resp.raise_for_status()
            message = resp.json()["message"]
            items = message["items"]
            if not items:
                break
            for item in items:
                m = _CODE_PATTERN.match(item["DOI"])
                if m:
                    codes.add(m.group(1).upper())
            cursor = message.get("next-cursor")
            if not cursor or len(items) < 1000:
                break
    except Exception as e:
        logger.warning(
            f"Could not reach Crossref to check already-registered DOIs "
            f"(falling back to EXCLUDED_CODES only): {e}"
        )
        return set()

    logger.info(f"Fetched {len(codes)} already-registered DOI codes from Crossref")
    return codes
