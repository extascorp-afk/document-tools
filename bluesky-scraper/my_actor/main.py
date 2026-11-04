"""Bluesky Scraper Actor: public Bluesky data through the official AT Protocol AppView API."""

from __future__ import annotations

import asyncio
import re
from collections.abc import AsyncIterator
from typing import Any

from apify import Actor, Event
from httpx2 import AsyncClient

PUBLIC = 'https://api.bsky.app/xrpc'  # same AppView as public.api.bsky.app, but it also serves searchPosts
AUTHED = 'https://bsky.social/xrpc'


class Api:
    def __init__(self, client: AsyncClient, base: str, token: str | None = None) -> None:
        self.client, self.base = client, base
        self.headers = {'Authorization': f'Bearer {token}'} if token else {}

    async def get(self, method: str, **params: Any) -> dict[str, Any]:
        params = {k: v for k, v in params.items() if v not in (None, '')}
        status = 0
        for attempt in range(6):
            r = await self.client.get(f'{self.base}/{method}', params=params, headers=self.headers)
            status = r.status_code
            if status == 429 or status >= 500:
                wait = min(float(r.headers.get('retry-after') or 2 ** attempt), 60)
                Actor.log.info(f'HTTP {status}, retrying in {wait:.0f}s')
                await asyncio.sleep(wait)
                continue
            if status >= 400:
                try:
                    msg = r.json().get('message') or r.text[:200]
                except ValueError:
                    msg = r.text[:200]
                raise ValueError(f'{method}: HTTP {status} {msg}')
            return r.json()
        raise ValueError(f'{method}: still failing after retries (HTTP {status})')

    async def pages(self, method: str, key: str, **params: Any) -> AsyncIterator[dict[str, Any]]:
        cursor = None
        while True:
            data = await self.get(method, limit=100, cursor=cursor, **params)
            for x in data.get(key) or []:
                yield x
            cursor = data.get('cursor')
            if not cursor or not data.get(key):
                return


def post_item(p: dict[str, Any], source: str) -> dict[str, Any]:
    rec, a = p.get('record') or {}, p.get('author') or {}
    reply = (rec.get('reply') or {}).get('parent') or {}
    return {
        'type': 'post', 'source': source, 'uri': p['uri'],
        'url': f'https://bsky.app/profile/{a.get("handle") or a.get("did")}/post/{p["uri"].rsplit("/", 1)[-1]}',
        'text': rec.get('text', ''), 'createdAt': rec.get('createdAt'), 'langs': rec.get('langs'),
        'authorHandle': a.get('handle'), 'authorDid': a.get('did'), 'authorName': a.get('displayName'),
        'likeCount': p.get('likeCount', 0), 'repostCount': p.get('repostCount', 0),
        'replyCount': p.get('replyCount', 0), 'quoteCount': p.get('quoteCount', 0),
        'isReply': bool(reply), 'replyToUri': reply.get('uri'),
        'hashtags': [f['tag'] for facet in rec.get('facets') or [] for f in facet.get('features', []) if 'tag' in f],
        'embed': p.get('embed'), 'indexedAt': p.get('indexedAt'),
    }


def profile_item(p: dict[str, Any], source: str) -> dict[str, Any]:
    return {
        'type': 'profile', 'source': source, 'did': p.get('did'), 'handle': p.get('handle'),
        'url': f'https://bsky.app/profile/{p.get("handle")}', 'displayName': p.get('displayName'),
        'description': p.get('description'), 'avatar': p.get('avatar'), 'banner': p.get('banner'),
        'followersCount': p.get('followersCount'), 'followsCount': p.get('followsCount'),
        'postsCount': p.get('postsCount'), 'createdAt': p.get('createdAt') or p.get('indexedAt'),
    }


def clean_handle(h: str) -> str:
    m = re.search(r'bsky\.app/profile/([^/?#]+)', h)
    return (m.group(1) if m else h).strip().lstrip('@')


def to_uri(u: str) -> str:
    m = re.search(r'bsky\.app/profile/([^/?#]+)/post/([^/?#]+)', u)
    return f'at://{m.group(1)}/app.bsky.feed.post/{m.group(2)}' if m else u


def walk(node: dict[str, Any]) -> list[dict[str, Any]]:
    out = [node['post']] if node.get('post') else []
    for r in node.get('replies') or []:
        out += walk(r)
    return out


def iso(v: str | None) -> str | None:
    v = (v or '').strip()
    return v + 'T00:00:00Z' if re.fullmatch(r'\d{4}-\d{2}-\d{2}', v) else v or None


async def collect(api: Api, inp: dict[str, Any], mode: str, entry: str) -> AsyncIterator[dict[str, Any]]:
    """Yield result items for one entry; the caller enforces maxItems."""
    if mode == 'search':
        args = dict(q=entry, sort=inp.get('sort') or 'latest', since=iso(inp.get('since')),
                    until=iso(inp.get('until')), lang=inp.get('language'))
        if args['sort'] == 'top':  # cursors are rejected (403) without login, so 'top' = first 100 unauthenticated
            async for p in api.pages('app.bsky.feed.searchPosts', 'posts', **args):
                yield post_item(p, entry)
            return
        # Latest: page by moving `until` back to the oldest post seen, since search cursors need login.
        seen: set[str] = set()
        while True:
            posts = (await api.get('app.bsky.feed.searchPosts', limit=100, **args)).get('posts') or []
            new = [p for p in posts if p['uri'] not in seen]
            if not new:
                return
            for p in new:
                seen.add(p['uri'])
                yield post_item(p, entry)
            args['until'] = min(p['record']['createdAt'] for p in posts)
    elif mode == 'authorFeed':
        flt = 'posts_with_replies' if inp.get('includeReplies', True) else 'posts_no_replies'
        async for f in api.pages('app.bsky.feed.getAuthorFeed', 'feed', actor=entry, filter=flt):
            yield post_item(f['post'], entry)
    elif mode == 'profiles':
        yield profile_item(await api.get('app.bsky.actor.getProfile', actor=entry), entry)
    elif mode in ('followers', 'following'):
        method, key = (('app.bsky.graph.getFollowers', 'followers') if mode == 'followers'
                       else ('app.bsky.graph.getFollows', 'follows'))
        async for p in api.pages(method, key, actor=entry):
            yield profile_item(p, entry) | {'relation': mode}
    else:  # thread
        data = await api.get('app.bsky.feed.getPostThread', uri=entry, depth=1000, parentHeight=0)
        for p in walk(data['thread']):
            yield post_item(p, entry)


async def main() -> None:
    async with Actor:
        async def on_abort(_: object = None) -> None:
            await Actor.exit()

        Actor.on(Event.ABORTING, on_abort)
        inp = await Actor.get_input() or {}
        mode = inp.get('mode') or 'search'
        limit = max(1, int(inp.get('maxItems') or 50))
        field = {'search': 'queries', 'thread': 'postUrls'}.get(mode, 'handles')
        entries = [e.strip() for e in inp.get(field) or [] if isinstance(e, str) and e.strip()]
        if not entries:
            raise ValueError(f'Mode "{mode}" needs at least one entry in "{field}".')
        if mode == 'thread':
            entries = [to_uri(e) for e in entries]
        elif mode != 'search':
            entries = [clean_handle(e) for e in entries]

        async with AsyncClient(timeout=30, headers={'User-Agent': 'bluesky-scraper Apify Actor'}) as client:
            token, base = None, PUBLIC
            if inp.get('identifier') and inp.get('appPassword'):
                r = await client.post(f'{AUTHED}/com.atproto.server.createSession',
                                      json={'identifier': inp['identifier'], 'password': inp['appPassword']})
                if r.status_code != 200:
                    raise ValueError('Bluesky login failed: check handle and app password.')
                token, base = r.json()['accessJwt'], AUTHED
            api = Api(client, base, token)

            for entry in entries:
                n = 0
                try:
                    async for item in collect(api, inp, mode, entry):
                        n += 1
                        # Charged per delivered item; failures below are pushed uncharged.
                        res = await Actor.push_data(item, charged_event_name='result')
                        if (res and res.event_charge_limit_reached):
                            Actor.log.info('Max charge limit reached, stopping.')
                            return
                        if n >= limit:
                            break
                except Exception as e:  # noqa: BLE001 - one bad entry must not fail the run
                    Actor.log.warning(f'{entry}: {e}')
                    await Actor.push_data({'type': 'error', 'source': entry, 'error': str(e)})
                Actor.log.info(f'{entry}: {n} results')
