"""Google Play Reviews Actor: public Google Play review pages for any Android app, no login, no browser."""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from typing import Any

from apify import Actor, Event
from google_play_scraper import Sort, app as gp_app, reviews as gp_reviews, search as gp_search

SORTS = {'newest': Sort.NEWEST, 'relevant': Sort.MOST_RELEVANT, 'rating': Sort.RATING}


def parse_date(s: str) -> datetime:
    return datetime.fromisoformat(s.replace('Z', '+00:00')).replace(tzinfo=None) if 'T' in s else datetime.strptime(s, '%Y-%m-%d')


async def retry(fn: Any, *a: Any, **kw: Any) -> Any:
    for attempt in range(4):
        try:
            return await asyncio.to_thread(fn, *a, **kw)
        except Exception as e:  # noqa: BLE001
            if attempt == 3 or 'not found' in str(e).lower() or '404' in str(e):
                raise
            await asyncio.sleep(2 ** attempt)


async def resolve(entry: str, lang: str, country: str) -> str:
    """Entry -> package name (com.duolingo)."""
    if m := re.search(r'play\.google\.com/store/apps/details\?[^#]*?id=([\w.]+)', entry):
        return m[1]
    if re.fullmatch(r'[A-Za-z][\w]*(\.[\w]+)+', entry):
        return entry
    raw = await retry(gp_search, entry, n_hits=8, lang=lang, country=country)
    hits = [h for h in raw if h.get('appId')]  # the featured top hit often has no appId
    if raw and not raw[0].get('appId'):
        Actor.log.warning(f'"{entry}": the featured top result "{raw[0].get("title")}" has no package ID in Play search; using the best listed match. Pass the package name (com.example.app) or the Play URL for an exact app.')
    for h in hits:  # prefer an exact title match, else the top result
        if (h.get('title') or '').strip().lower() == entry.lower():
            return h['appId']
    if hits:
        return hits[0]['appId']
    raise ValueError(f'No app found for "{entry}"')


async def main() -> None:
    async with Actor:
        async def on_abort(_: object = None) -> None:
            await Actor.exit()

        Actor.on(Event.ABORTING, on_abort)
        inp = await Actor.get_input() or {}
        apps = [str(a).strip() for a in inp.get('apps') or [] if str(a).strip()]
        if not apps:
            raise ValueError('Add at least one app (Play Store URL, package name or app name) to "apps".')
        countries = [str(c).strip().lower() for c in inp.get('countries') or ['us'] if str(c).strip()]
        for c in countries:
            if not re.fullmatch(r'[a-z]{2}', c):
                raise ValueError(f'Bad country "{c}": use two-letter codes such as us, gb, de')
        lang = str(inp.get('language') or 'en').strip().lower()
        sort = SORTS.get(inp.get('sort') or 'newest', Sort.NEWEST)
        limit = max(1, min(int(inp.get('maxReviews') or 50), 5000))
        lo, hi = int(inp.get('minRating') or 1), int(inp.get('maxRating') or 5)
        since = None
        if inp.get('since'):
            try:
                since = parse_date(str(inp['since']).strip())
            except ValueError:
                raise ValueError(f'Bad date "{inp["since"]}": use 2026-01-31') from None

        for entry in apps:
            try:
                pkg = await resolve(entry, lang, countries[0])
            except Exception as e:  # noqa: BLE001 - one bad app must not fail the run
                Actor.log.warning(f'{entry}: {e}')
                await Actor.push_data({'type': 'error', 'source': entry, 'error': str(e)})
                continue
            for cc in countries:
                n = 0
                try:
                    info = await retry(gp_app, pkg, lang=lang, country=cc)
                    meta = {'appId': pkg, 'appName': info.get('title'), 'developer': info.get('developer'),
                            'appRating': info.get('score'), 'appRatingCount': info.get('ratings'),
                            'installs': info.get('installs'), 'appUrl': f'https://play.google.com/store/apps/details?id={pkg}'}
                    token, done = None, False
                    while not done:
                        batch, token = await retry(gp_reviews, pkg, lang=lang, country=cc, sort=sort,
                                                   count=min(200, limit * 3), continuation_token=token)
                        if not batch:
                            break
                        for r in batch:
                            old = bool(since and r['at'] < since)
                            if old and sort == Sort.NEWEST:
                                done = True
                                break
                            if old or not lo <= r['score'] <= hi:
                                continue
                            n += 1
                            item = {'type': 'review', **meta, 'country': cc, 'language': lang, 'reviewId': r['reviewId'],
                                    'rating': r['score'], 'text': r['content'], 'version': r.get('reviewCreatedVersion') or r.get('appVersion'),
                                    'author': r['userName'], 'date': r['at'].replace(tzinfo=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                                    'thumbsUp': r['thumbsUpCount'], 'developerReply': r.get('replyContent'),
                                    'developerReplyDate': r['repliedAt'].replace(tzinfo=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') if r.get('repliedAt') else None,
                                    'source': entry}
                            # Charged per delivered review; errors are pushed uncharged.
                            res = await Actor.push_data(item, charged_event_name='review')
                            if res and res.event_charge_limit_reached:
                                Actor.log.info('Max charge limit reached, stopping.')
                                return
                            if n >= limit:
                                done = True
                                break
                        if not token:
                            break
                except Exception as e:  # noqa: BLE001
                    Actor.log.warning(f'{entry} [{cc}]: {e}')
                    await Actor.push_data({'type': 'error', 'source': entry, 'country': cc, 'appId': pkg, 'error': str(e)[:300]})
                Actor.log.info(f'{entry} [{cc}]: {n} reviews')
