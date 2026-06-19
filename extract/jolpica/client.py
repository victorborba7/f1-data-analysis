"""
A small, polite client for the Jolpica-F1 (Ergast-compatible) API.

Design goals:
- **Polite**: throttle to stay under the 4 req/sec rate limit and back off on 429.
- **Resumable / cheap re-runs**: every page response is cached to disk keyed by
  its full request path, so a re-run (or a run interrupted mid-backfill) replays
  from cache instead of re-hitting the API.
- **Pagination-aware**: Ergast paginates with ``limit``/``offset`` and reports a
  ``total`` in every envelope; :meth:`paginate` walks all pages transparently.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Iterator

import requests

from ..config import Settings, get_settings


class JolpicaClient:
    def __init__(self, settings: Settings | None = None, session: requests.Session | None = None):
        self.settings = settings or get_settings()
        self.base_url = self.settings.base_url.rstrip("/")
        self.cache_dir = self.settings.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._session = session or requests.Session()
        self._session.headers.update({"User-Agent": "f1-elt-portfolio/1.0 (+github)"})
        self._last_request_ts = 0.0

    # -- caching ------------------------------------------------------------
    def _cache_path(self, path: str, params: dict[str, Any]) -> Path:
        key = path + "?" + "&".join(f"{k}={params[k]}" for k in sorted(params))
        digest = hashlib.sha1(key.encode()).hexdigest()[:16]
        safe = path.strip("/").replace("/", "_") or "root"
        return self.cache_dir / f"{safe}__{digest}.json"

    def clear_cache(self, *prefixes: str) -> int:
        """
        Delete cached pages whose filename starts with any of ``prefixes``
        (the path with ``/`` replaced by ``_``). Used by the weekly refresh to
        force the in-progress season and reference dimensions to refetch. With no
        prefixes, clears the entire cache. Returns the number of files removed.
        """
        removed = 0
        for f in self.cache_dir.glob("*.json"):
            if not prefixes or any(f.name.startswith(p) for p in prefixes):
                f.unlink()
                removed += 1
        return removed

    # -- throttling ---------------------------------------------------------
    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_ts
        wait = self.settings.min_interval_s - elapsed
        if wait > 0:
            time.sleep(wait)
        self._last_request_ts = time.monotonic()

    # -- single request -----------------------------------------------------
    def get(self, path: str, params: dict[str, Any] | None = None,
            force: bool = False) -> dict[str, Any]:
        """
        GET ``{base}/{path}.json`` (cached). ``path`` has no leading slash.

        ``force=True`` bypasses the cache read and refetches — used by the weekly
        refresh so an in-progress season picks up its newest race.
        """
        params = dict(params or {})
        cache_file = self._cache_path(path, params)
        if cache_file.exists() and not force:
            return json.loads(cache_file.read_text(encoding="utf-8"))

        url = f"{self.base_url}/{path.lstrip('/')}.json"
        for attempt in range(5):
            self._throttle()
            resp = self._session.get(url, params=params, timeout=30)
            if resp.status_code == 429:
                retry_after = float(resp.headers.get("Retry-After", 2 ** attempt))
                time.sleep(min(retry_after, 60))
                continue
            resp.raise_for_status()
            payload = resp.json()
            cache_file.write_text(json.dumps(payload), encoding="utf-8")
            return payload
        raise RuntimeError(f"Repeatedly rate-limited fetching {url}")

    # -- pagination ---------------------------------------------------------
    def paginate(self, path: str, table_key: str, list_key: str,
                 params: dict[str, Any] | None = None,
                 force: bool = False) -> Iterator[dict[str, Any]]:
        """
        Yield every item from a paginated Ergast collection.

        ``table_key``/``list_key`` locate the collection in the envelope, e.g.
        ``("DriverTable", "Drivers")`` or ``("RaceTable", "Races")``.
        """
        params = dict(params or {})
        limit = self.settings.page_size
        offset = 0
        while True:
            page = self.get(path, {**params, "limit": limit, "offset": offset}, force=force)
            mrdata = page["MRData"]
            items = mrdata.get(table_key, {}).get(list_key, [])
            yield from items
            total = int(mrdata.get("total", 0))
            offset += limit
            if offset >= total or not items:
                break
