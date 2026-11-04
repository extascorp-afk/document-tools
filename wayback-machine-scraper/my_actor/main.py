"""Wayback Machine Actor: the Internet Archive's public CDX Server API, no login."""

from __future__ import annotations

import asyncio
import re
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

from apify import Actor, Event
from httpx2 import AsyncClient

CDX = 'https://web.archive.org/cdx/search/cdx'
FIELDS = ['urlkey', 'timestamp', 'original', 'mimetype', 'statuscode', 'digest', 'length']
COLLAPSE = {'none': None, 'second': 'timestamp:14', 'hour': 'timestamp:10', 'day': 'timestamp:8',
            'month': 'timestamp:6', 'year': 'timestamp:4', 'digest': 'digest'}


async def get(client: AsyncClient, params: dict[str, Any]) -> list[list[str]]:
    status = 0
    for attempt in range(5):
        try:
            r = await client.get(CDX, params=params)
        except Exception as e:  # noqa: BLE001 - the CDX server drops connections under load
            Actor.log.info(f'{type(e).__name__}, retrying')
            await asyncio.sleep(2 ** attempt)
            continue
        status = r.status_code
        if status in (429, 502, 503, 504) or status >= 500:
            wait = min(float(r.headers.get("retry-after") or 3 * 2 ** attempt), 45)
            Actor.log.info(f'HTTP {status}, retrying in {wait:.0f}s')
            await asyncio.sleep(wait)
            continue
        if status >= 400:
            raise ValueError(f'HTTP {status} {r.text[:200]}')
        if not r.text.strip():
            return []
        return r.json()
    raise ValueError(f'Wayback CDX still failing after retries (HTTP {status})')


def stamp(v: str | None, end: bool = False) -> str | None:
    """2026, 2026-01, 2026-01-31 or a full timestamp -> CDX timestamp prefix."""
    v = (v or '').strip()
    if not v:
        return None
    digits = re.sub(r'[-:T\sZ]', '', v)
    if not digits.isdigit() or len(digits) not in (4, 6, 8, 10, 12, 14):
        raise ValueError(f'Bad date "{v}": use 2026, 2026-01 or 2026-01-31')
    return digits


def snapshot(row: list[str], source: str) -> dict[str, Any]:
    r = dict(zip(FIELDS, row))
    ts, url = r['timestamp'], r['original']
    return {
        'type': 'snapshot', 'url': url, 'timestamp': ts,
        'date': datetime.strptime(ts, '%Y%m%d%H%M%S').replace(tzinfo=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'statusCode': int(r['statuscode']) if r['statuscode'].isdigit() else None,
        'mimeType': r['mimetype'], 'digest': r['digest'], 'length': int(r['length']) if r['length'].isdigit() else None,
        'archiveUrl': f'https://web.archive.org/web/{ts}/{url}',
        'rawUrl': f'https://web.archive.org/web/{ts}id_/{url}',
        'source': source,
    }


async def query(client: AsyncClient, entry: str, params: dict[str, Any], limit: int) -> AsyncIterator[dict[str, Any]]:
    """Page through CDX with resume keys (a single CDX call can time out on large result sets)."""
    base = {k: v for k, v in params.items() if v not in (None, '')}
    key, seen = None, 0
    while seen < limit:
        p = base | {'url': entry, 'output': 'json', 'showResumeKey': 'true', 'limit': min(limit - seen, 5000)}
        if key:
            p['resumeKey'] = key
        rows = await get(client, p)
        key = None
        if len(rows) >= 2 and rows[-2] == [] and len(rows[-1]) == 1:
            key = rows[-1][0]
            rows = rows[:-2]
        for row in rows[1:] if rows and rows[0][0] == 'urlkey' else rows:
            seen += 1
            yield snapshot(row, entry)
        if not key or not rows:
            return


async def main() -> None:
    async with Actor:
        async def on_abort(_: object = None) -> None:
            await Actor.exit()

        Actor.on(Event.ABORTING, on_abort)
        inp = await Actor.get_input() or {}
        mode = inp.get('mode') or 'snapshots'
        urls = [str(u).strip() for u in inp.get('urls') or [] if str(u).strip()]
        if not urls:
            raise ValueError('Add at least one URL or domain to "urls".')
        limit = max(1, int(inp.get('maxItems') or 20))
        status = (inp.get('statusFilter') or '200').strip()
        flt = [f'statuscode:{status}'] if status and status != 'any' else []
        if inp.get('mimeType'):
            flt.append(f'mimetype:{inp["mimeType"].strip()}')
        common: dict[str, Any] = {'filter': flt, 'from': stamp(inp.get('from')), 'to': stamp(inp.get('to'))}

        if mode == 'closest':
            at = stamp(inp.get('closestTo'))
            if not at:
                raise ValueError('Mode "closest" needs a date in "closestTo", e.g. 2020-06-15.')
            at = at.ljust(14, '0') if len(at) < 14 else at
            plans = {'match': 'exact', 'extra': {'closest': at, 'sort': 'closest'}, 'cap': 1}
        elif mode == 'urls':
            plans = {'match': inp.get('matchType') or 'domain', 'extra': {'collapse': 'urlkey'}, 'cap': None}
        else:
            c = COLLAPSE.get(inp.get('collapse') or 'none')
            plans = {'match': inp.get('matchType') or 'exact', 'extra': {'collapse': c}, 'cap': None}
        if plans['match'] not in ('exact', 'prefix', 'host', 'domain'):
            raise ValueError('matchType must be exact, prefix, host or domain')

        async with AsyncClient(timeout=90, headers={'User-Agent': 'wayback-machine-scraper Apify Actor'}) as client:
            for entry in urls:
                n = 0
                try:
                    # shortcut: filters apply to closest mode too, so "closest" = nearest snapshot matching them.
                    async for it in query(client, entry, common | plans['extra'] | {'matchType': plans['match']},
                                          min(limit, plans['cap'] or limit)):
                        n += 1
                        # Charged per delivered snapshot; errors are pushed uncharged.
                        res = await Actor.push_data(it, charged_event_name='snapshot')
                        if res and res.event_charge_limit_reached:
                            Actor.log.info('Max charge limit reached, stopping.')
                            return
                except Exception as e:  # noqa: BLE001 - one bad URL must not fail the run
                    Actor.log.warning(f'{entry}: {e}')
                    await Actor.push_data({'type': 'error', 'source': entry, 'error': str(e)})
                Actor.log.info(f'{entry}: {n} snapshots')
