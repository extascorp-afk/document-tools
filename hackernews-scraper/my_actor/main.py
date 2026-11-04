"""Hacker News Scraper Actor: official HN Firebase API + Algolia HN Search API, no login."""

from __future__ import annotations

import asyncio
import html
import re
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from apify import Actor, Event
from httpx2 import AsyncClient

FIREBASE = 'https://hacker-news.firebaseio.com/v0'
ALGOLIA = 'https://hn.algolia.com/api/v1'
LISTS = {'top': 'topstories', 'new': 'newstories', 'best': 'beststories',
         'ask': 'askstories', 'show': 'showstories', 'jobs': 'jobstories'}
HIRING = {'hiring': 'Ask HN: Who is hiring?', 'hired': 'Ask HN: Who wants to be hired?',
          'freelancer': 'Ask HN: Freelancer? Seeking freelancer?'}
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
          'September', 'October', 'November', 'December']


async def get(client: AsyncClient, url: str, **params: Any) -> Any:
    params = {k: v for k, v in params.items() if v not in (None, '')}
    status = 0
    for attempt in range(6):
        r = await client.get(url, params=params)
        status = r.status_code
        if status == 429 or status >= 500:
            wait = min(float(r.headers.get('retry-after') or 2 ** attempt), 60)
            Actor.log.info(f'HTTP {status}, retrying in {wait:.0f}s')
            await asyncio.sleep(wait)
            continue
        if status == 404:
            raise ValueError(f'{url}: not found')
        if status >= 400:
            raise ValueError(f'{url}: HTTP {status} {r.text[:200]}')
        return r.json()
    raise ValueError(f'{url}: still failing after retries (HTTP {status})')


def plain(t: str | None) -> str | None:
    if not t:
        return None
    t = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>.*?</a>', r'\1', t, flags=re.S)  # HN truncates link text
    t = re.sub(r'<p>|<br\s*/?>', '\n', t)
    return html.unescape(re.sub(r'<[^>]+>', '', t)).strip() or None


def iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def item(id_: Any, type_: str | None, *, title=None, url=None, author=None, points=None, num_comments=None,
         created=None, text=None, parent_id=None, story_id=None, source: str = '') -> dict[str, Any]:
    """The one flat output shape for every story, comment, job and poll."""
    return {
        'type': type_, 'id': int(id_), 'title': title, 'url': url,
        'domain': (urlparse(url).netloc.removeprefix('www.') or None) if url else None,
        'author': author, 'points': points, 'num_comments': num_comments, 'created_at': created,
        'text': plain(text), 'parent_id': int(parent_id) if parent_id else None,
        'story_id': int(story_id) if story_id else None,
        'hn_url': f'https://news.ycombinator.com/item?id={id_}', 'source': source,
    }


def from_firebase(d: dict[str, Any], source: str) -> dict[str, Any]:
    return item(d['id'], d.get('type'), title=d.get('title'), url=d.get('url'), author=d.get('by'),
                points=d.get('score'), num_comments=d.get('descendants'),
                created=iso(d['time']) if d.get('time') else None, text=d.get('text'),
                parent_id=d.get('parent'), source=source)


def from_hit(h: dict[str, Any], source: str) -> dict[str, Any]:
    tags = h.get('_tags') or []
    type_ = next((t for t in ('story', 'comment', 'job', 'poll') if t in tags), 'story')
    return item(h['objectID'], type_, title=h.get('title') or h.get('story_title'),
                url=h.get('url') or h.get('story_url'), author=h.get('author'), points=h.get('points'),
                num_comments=h.get('num_comments'), created=h.get('created_at'),
                text=h.get('story_text') or h.get('comment_text') or h.get('text'),
                parent_id=h.get('parent_id'), story_id=h.get('story_id'), source=source)


def from_tree(n: dict[str, Any], story_id: int, source: str) -> dict[str, Any]:
    return item(n['id'], n.get('type'), title=n.get('title'), url=n.get('url'), author=n.get('author'),
                points=n.get('points'), created=n.get('created_at'), text=n.get('text'),
                parent_id=n.get('parent_id'), story_id=story_id, source=source)


def flatten(n: dict[str, Any], story_id: int, source: str) -> list[dict[str, Any]]:
    out = []
    for c in n.get('children') or []:
        if c.get('text'):  # deleted comments have no text
            out.append(from_tree(c, story_id, source))
        out += flatten(c, story_id, source)
    return out


def epoch(v: str | None) -> int | None:
    v = (v or '').strip()
    if not v:
        return None
    try:
        d = datetime.fromisoformat(v.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError(f'Bad date "{v}": use 2026-01-31 or 2026-01-31T00:00:00Z') from None
    return int((d if d.tzinfo else d.replace(tzinfo=timezone.utc)).timestamp())


async def algolia(client: AsyncClient, q: str, tags: str, by_date: bool, filters: list[str]) -> AsyncIterator[dict]:
    """Algolia serves max 1000 hits per query, so date-sorted runs slide a created_at_i window backwards."""
    until, last = None, None
    while True:
        for page in range(10):
            nf = filters + ([f'created_at_i<{until}'] if until else [])
            d = await get(client, f'{ALGOLIA}/{"search_by_date" if by_date else "search"}', query=q, tags=tags,
                          numericFilters=','.join(nf), hitsPerPage=100, page=page)
            for h in d['hits']:
                yield h
                last = h
            if page + 1 >= d['nbPages'] or not d['hits']:
                return
        if not by_date or not last:  # relevance sort stops at Algolia's 1000-hit cap
            return
        until = last['created_at_i']


async def find_hiring(client: AsyncClient, kind: str, month: str | None) -> dict[str, Any]:
    prefix = HIRING[kind]
    want = None
    if month:
        m = re.fullmatch(r'(\d{4})-(\d{2})', month.strip())
        if not m or not 1 <= int(m[2]) <= 12:
            raise ValueError('hiringMonth must look like 2026-11')
        want = f'{MONTHS[int(m[2]) - 1]} {m[1]}'
    d = await get(client, f'{ALGOLIA}/search_by_date', query=f"{prefix.split('?')[0]} {want or ''}".strip(), tags='story,author_whoishiring',
                  hitsPerPage=100)
    for h in d['hits']:
        t = h.get('title') or ''
        if t.startswith(prefix) and (not want or want in t):
            return h
    raise ValueError(f'No "{prefix}" thread found' + (f' for {want}' if want else ''))


async def collect(client: AsyncClient, inp: dict[str, Any], mode: str, entry: str) -> AsyncIterator[dict[str, Any]]:
    """Yield result items for one entry; the caller enforces maxItems."""
    if mode == 'list':
        if entry == 'front':
            async for h in algolia(client, '', 'front_page', False, []):
                yield from_hit(h, entry)
            return
        ids = await get(client, f'{FIREBASE}/{LISTS[entry]}.json')
        sem = asyncio.Semaphore(20)

        async def one(i: int) -> dict | None:
            async with sem:
                return await get(client, f'{FIREBASE}/item/{i}.json')
        step = 40  # batches, so a small maxItems does not download all 500 items
        for k in range(0, len(ids), step):
            for d in await asyncio.gather(*(one(i) for i in ids[k:k + step])):
                if d and not d.get('deleted') and not d.get('dead'):
                    yield from_firebase(d, entry)
    elif mode == 'search':
        tags = {'story': 'story', 'comment': 'comment', 'both': '(story,comment)'}[inp.get('searchIn') or 'story']
        f = []
        for key, op in (('since', '>='), ('until', '<')):
            if (e := epoch(inp.get(key))) is not None:
                f.append(f'created_at_i{op}{e}')
        for key, col in (('minPoints', 'points'), ('minComments', 'num_comments')):
            if inp.get(key):
                f.append(f'{col}>={int(inp[key])}')
        async for h in algolia(client, entry, tags, inp.get('sort') == 'date', f):
            yield from_hit(h, entry)
    elif mode == 'thread':
        m = re.search(r'id=(\d+)', entry) or re.fullmatch(r'(\d+)', entry)
        if not m:
            raise ValueError('Expected a story ID or news.ycombinator.com/item?id=... URL')
        tree = await get(client, f'{ALGOLIA}/items/{m[1]}')
        sid = tree.get('story_id') or tree['id']
        yield from_tree(tree, sid, entry)
        for c in flatten(tree, sid, entry):
            yield c
    elif mode == 'user':
        u = await get(client, f'{FIREBASE}/user/{entry}.json')
        if not u:
            raise ValueError(f'User "{entry}" not found')
        yield {'type': 'user', 'id': u['id'], 'author': u['id'], 'karma': u.get('karma'),
               'created_at': iso(u['created']), 'text': plain(u.get('about')),
               'submitted_count': len(u.get('submitted') or []),
               'hn_url': f'https://news.ycombinator.com/user?id={entry}', 'source': entry}
        if inp.get('includeSubmissions', True):
            async for h in algolia(client, '', f'author_{entry}', True, []):
                yield from_hit(h, entry)
    else:  # hiring
        t = await find_hiring(client, inp.get('hiringThread') or 'hiring', inp.get('hiringMonth'))
        Actor.log.info(f'Thread: {t["title"]} ({t["objectID"]})')
        tree = await get(client, f'{ALGOLIA}/items/{t["objectID"]}')
        for c in tree.get('children') or []:  # top-level comments = the postings
            if c.get('text'):
                yield from_tree(c, tree['id'], t['title']) | {'num_comments': len(c.get('children') or [])}


async def main() -> None:
    async with Actor:
        async def on_abort(_: object = None) -> None:
            await Actor.exit()

        Actor.on(Event.ABORTING, on_abort)
        inp = await Actor.get_input() or {}
        mode = inp.get('mode') or 'list'
        limit = max(1, int(inp.get('maxItems') or 20))
        field = {'list': 'lists', 'search': 'queries', 'thread': 'storyIds', 'user': 'usernames'}.get(mode)
        entries = [str(e).strip() for e in inp.get(field) or [] if str(e).strip()] if field else ['hiring']
        if mode == 'list':
            entries = entries or [inp.get('list') or 'top']
            bad = [e for e in entries if e != 'front' and e not in LISTS]
            if bad:
                raise ValueError(f'Unknown list {bad}: use front, {", ".join(LISTS)}')
        elif mode == 'search':
            entries = entries or ['']  # empty query = everything matching the filters
        elif not entries:
            raise ValueError(f'Mode "{mode}" needs at least one entry in "{field}".')

        async with AsyncClient(timeout=30, headers={'User-Agent': 'hackernews-scraper Apify Actor'}) as client:
            for entry in entries:
                n = 0
                try:
                    async for it in collect(client, inp, mode, entry):
                        n += 1
                        # Charged per delivered item; failures below are pushed uncharged.
                        res = await Actor.push_data(it, charged_event_name='result')
                        if res and res.event_charge_limit_reached:
                            Actor.log.info('Max charge limit reached, stopping.')
                            return
                        if n >= limit:
                            break
                except Exception as e:  # noqa: BLE001 - one bad entry must not fail the run
                    Actor.log.warning(f'{entry}: {e}')
                    await Actor.push_data({'type': 'error', 'source': entry, 'error': str(e)})
                Actor.log.info(f'{entry or "(all)"}: {n} results')
