"""App Store Reviews Actor: Apple's official customer-reviews RSS feed + iTunes lookup/search APIs, no login."""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from typing import Any

from apify import Actor, Event
from httpx2 import AsyncClient

RSS = 'https://itunes.apple.com/{cc}/rss/customerreviews/page={page}/id={id}/sortby={sort}/json'
LOOKUP = 'https://itunes.apple.com/lookup'
SEARCH = 'https://itunes.apple.com/search'


async def get(client: AsyncClient, url: str, **params: Any) -> Any:
    status = 0
    for attempt in range(6):
        r = await client.get(url, params=params)
        status = r.status_code
        if status in (403, 429) or status >= 500:
            wait = min(float(r.headers.get('retry-after') or 2 ** attempt), 60)
            Actor.log.info(f'HTTP {status}, retrying in {wait:.0f}s')
            await asyncio.sleep(wait)
            continue
        if status == 404:
            return None  # unknown app or country storefront
        if status >= 400:
            raise ValueError(f'HTTP {status} {r.text[:200]}')
        try:
            return r.json()
        except ValueError:
            return None  # empty body = no reviews on that page
    raise ValueError(f'still failing after retries (HTTP {status})')


def label(d: dict[str, Any], key: str) -> str | None:
    v = d.get(key)
    return v.get('label') if isinstance(v, dict) else None


def to_int(v: str | None) -> int | None:
    return int(v) if v and v.lstrip('-').isdigit() else None


def parse_date(s: str) -> datetime:
    return datetime.fromisoformat(s.replace('Z', '+00:00')).astimezone(timezone.utc)


def parse_review(e: dict[str, Any], app: dict[str, Any], cc: str, source: str) -> dict[str, Any] | None:
    if 'im:rating' not in e:  # page 1 may start with an entry describing the app itself
        return None
    d = label(e, 'updated')
    return {
        'type': 'review', 'appId': app['id'], 'appName': app.get('name'), 'developer': app.get('developer'),
        'appRating': app.get('rating'), 'appRatingCount': app.get('ratingCount'), 'country': cc,
        'reviewId': label(e, 'id'), 'rating': int(label(e, 'im:rating')), 'title': label(e, 'title'),
        'text': (e.get('content') or {}).get('label'), 'version': label(e, 'im:version'),
        'author': ((e.get('author') or {}).get('name') or {}).get('label'),
        'date': parse_date(d).strftime('%Y-%m-%dT%H:%M:%SZ') if d else None,
        'helpfulVotes': to_int(label(e, 'im:voteSum')), 'totalVotes': to_int(label(e, 'im:voteCount')),
        'appUrl': app.get('url'), 'source': source,
    }


async def resolve(client: AsyncClient, entry: str, cc: str) -> tuple[str, str | None]:
    """Entry -> (numeric app id, country hint from a URL)."""
    if entry.isdigit():
        return entry, None
    if m := re.search(r'apps\.apple\.com/(?:([a-z]{2})/)?[^?#]*?/?id(\d+)', entry):
        return m[2], m[1]
    d = await get(client, SEARCH, term=entry, entity='software', limit=1, country=cc)
    if not d or not d.get('results'):
        raise ValueError(f'No app found for "{entry}"')
    return str(d['results'][0]['trackId']), None


async def app_info(client: AsyncClient, app_id: str, cc: str) -> dict[str, Any]:
    d = await get(client, LOOKUP, id=app_id, country=cc)
    r = (d or {}).get('results') or []
    if not r:
        return {'id': app_id}
    r = r[0]
    return {'id': app_id, 'name': r.get('trackName'), 'developer': r.get('artistName'),
            'rating': r.get('averageUserRating'), 'ratingCount': r.get('userRatingCount'),
            'url': r.get('trackViewUrl')}


async def main() -> None:
    async with Actor:
        async def on_abort(_: object = None) -> None:
            await Actor.exit()

        Actor.on(Event.ABORTING, on_abort)
        inp = await Actor.get_input() or {}
        apps = [str(a).strip() for a in inp.get('apps') or [] if str(a).strip()]
        if not apps:
            raise ValueError('Add at least one app (URL, numeric ID or name) to "apps".')
        countries = [str(c).strip().lower() for c in inp.get('countries') or [] if str(c).strip()]
        for c in countries:
            if not re.fullmatch(r'[a-z]{2}', c):
                raise ValueError(f'Bad country "{c}": use two-letter codes such as us, gb, de')
        sort = inp.get('sort') or 'mostrecent'
        limit = max(1, min(int(inp.get('maxReviews') or 20), 500))
        lo, hi = int(inp.get('minRating') or 1), int(inp.get('maxRating') or 5)
        since = None
        if inp.get('since'):
            try:
                since = parse_date(str(inp['since']).strip())
            except ValueError:
                raise ValueError(f'Bad date "{inp["since"]}": use 2026-01-31') from None

        async with AsyncClient(timeout=30, headers={'User-Agent': 'appstore-reviews-scraper Apify Actor'}) as client:
            for entry in apps:
                try:
                    app_id, hint = await resolve(client, entry, (countries or ['us'])[0])
                except Exception as e:  # noqa: BLE001 - one bad app must not fail the run
                    Actor.log.warning(f'{entry}: {e}')
                    await Actor.push_data({'type': 'error', 'source': entry, 'error': str(e)})
                    continue
                for cc in countries or [hint or 'us']:
                    n = 0
                    try:
                        app = await app_info(client, app_id, cc)
                        done = False
                        for page in range(1, 11):
                            d = await get(client, RSS.format(cc=cc, page=page, id=app_id, sort=sort))
                            entries = ((d or {}).get('feed') or {}).get('entry') or []
                            if isinstance(entries, dict):
                                entries = [entries]
                            if not entries:
                                break
                            for e in entries:
                                it = parse_review(e, app, cc, entry)
                                if not it:
                                    continue
                                old = bool(since and it['date'] and parse_date(it['date']) < since)
                                if old and sort == 'mostrecent':
                                    done = True
                                    break
                                if old or not lo <= it['rating'] <= hi:
                                    continue
                                n += 1
                                # Charged per delivered review; errors are pushed uncharged.
                                res = await Actor.push_data(it, charged_event_name='review')
                                if res and res.event_charge_limit_reached:
                                    Actor.log.info('Max charge limit reached, stopping.')
                                    return
                                if n >= limit:
                                    done = True
                                    break
                            if done:
                                break
                    except Exception as e:  # noqa: BLE001
                        Actor.log.warning(f'{entry} [{cc}]: {e}')
                        await Actor.push_data({'type': 'error', 'source': entry, 'country': cc, 'appId': app_id, 'error': str(e)})
                    Actor.log.info(f'{entry} [{cc}]: {n} reviews')
