"""Website to Markdown Actor: polite crawler that turns web pages into clean, LLM/RAG-ready Markdown. Honors robots.txt."""

from __future__ import annotations

import asyncio
import fnmatch
import re
import time
from typing import Any
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.robotparser import RobotFileParser

import trafilatura
from apify import Actor, Event
from httpx2 import AsyncClient
from lxml import html as lxml_html

UA = 'WebToMarkdownBot/1.0 (+https://apify.com/extas_corp/website-to-markdown)'
MAX_BYTES = 3_000_000
SKIP_EXT = re.compile(r'\.(png|jpe?g|gif|webp|svg|ico|pdf|zip|gz|mp[34]|avi|mov|css|js|json|xml|woff2?|ttf|exe|dmg)$', re.I)


def norm(url: str) -> str:
    url = urldefrag(url)[0]
    return url.rstrip('/') if urlparse(url).path in ('', '/') else url


def matches(url: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(url, p) for p in patterns)


class Robots:
    """Per-origin robots.txt cache. Missing robots.txt = allowed (RFC 9309); 401/403/5xx = disallow."""

    def __init__(self, client: AsyncClient) -> None:
        self.client = client
        self.cache: dict[str, RobotFileParser] = {}

    async def get(self, url: str) -> RobotFileParser:
        u = urlparse(url)
        origin = f'{u.scheme}://{u.netloc}'
        if origin not in self.cache:
            rp = RobotFileParser()
            try:
                r = await self.client.get(origin + '/robots.txt')
                if r.status_code >= 500 or r.status_code in (401, 403):
                    rp.disallow_all = True
                elif r.status_code == 200:
                    rp.parse(r.text.splitlines())
                else:
                    rp.allow_all = True
            except Exception:  # noqa: BLE001
                rp.allow_all = True
            self.cache[origin] = rp
        return self.cache[origin]

    async def allowed(self, url: str) -> tuple[bool, float]:
        rp = await self.get(url)
        return rp.can_fetch(UA, url), float(rp.crawl_delay(UA) or 0)


async def sitemap_urls(client: AsyncClient, start: str, robots: Robots, limit: int) -> list[str]:
    u = urlparse(start)
    rp = await robots.get(start)
    queue = list(rp.site_maps() or []) or [f'{u.scheme}://{u.netloc}/sitemap.xml']
    out: list[str] = []
    seen: set[str] = set()
    while queue and len(out) < limit and len(seen) < 20:
        sm = queue.pop(0)
        if sm in seen:
            continue
        seen.add(sm)
        try:
            r = await client.get(sm)
            if r.status_code != 200:
                continue
            locs = re.findall(r'<loc>\s*(?:<!\[CDATA\[)?\s*([^<\]\s]+)', r.text)
        except Exception:  # noqa: BLE001
            continue
        for loc in locs:
            (queue if loc.endswith(('.xml', '.xml.gz')) else out).append(loc)
    return out[:limit]


def extract(page: str, url: str, with_links: bool) -> dict[str, Any] | None:
    md = trafilatura.extract(page, url=url, output_format='markdown', include_links=with_links,
                             include_tables=True, include_images=False, favor_recall=True)
    if not md or len(md.strip()) < 20:
        return None
    meta = trafilatura.extract_metadata(page, default_url=url)
    return {
        'title': meta.title if meta else None, 'description': meta.description if meta else None,
        'author': meta.author if meta else None, 'date': meta.date if meta else None,
        'language': meta.language if meta else None, 'markdown': md.strip(),
    }


def links_of(page: str, base: str) -> list[str]:
    try:
        doc = lxml_html.fromstring(page)
    except Exception:  # noqa: BLE001
        return []
    out = []
    for a in doc.xpath('//a[@href]'):
        href = a.get('href', '').strip()
        if href.startswith(('mailto:', 'tel:', 'javascript:', '#')) or 'nofollow' in (a.get('rel') or ''):
            continue
        out.append(norm(urljoin(base, href)))
    return out


async def main() -> None:
    async with Actor:
        async def on_abort(_: object = None) -> None:
            await Actor.exit()

        Actor.on(Event.ABORTING, on_abort)
        inp = await Actor.get_input() or {}
        starts = [norm(str(s.get('url') if isinstance(s, dict) else s).strip()) for s in inp.get('startUrls') or []]
        if not starts or not all(urlparse(s).scheme in ('http', 'https') and urlparse(s).netloc for s in starts):
            raise ValueError('Add at least one http(s) URL to "startUrls".')
        max_pages = max(1, min(int(inp.get('maxPages') or 20), 5000))
        max_depth = max(0, min(int(1 if inp.get('maxDepth') is None else inp['maxDepth']), 10))
        same_host = inp.get('sameHostOnly', True)
        include = [str(p) for p in inp.get('includeUrlGlobs') or []]
        exclude = [str(p) for p in inp.get('excludeUrlGlobs') or []]
        use_sitemap = bool(inp.get('useSitemap', False))
        with_links = bool(inp.get('keepLinks', True))
        with_html = bool(inp.get('saveHtml', False))
        delay = max(0.0, float(0.5 if inp.get('delaySecs') is None else inp['delaySecs']))
        hosts = {urlparse(s).netloc for s in starts}

        n_ok = 0
        seen: set[str] = set(starts)
        queue: asyncio.Queue = asyncio.Queue()
        last_hit: dict[str, float] = {}
        stop = asyncio.Event()
        pending = 0  # queued + in-flight, to detect the end of the crawl

        async with AsyncClient(timeout=30, follow_redirects=True, headers={'User-Agent': UA, 'Accept': 'text/html,*/*;q=0.5'}) as client:
            robots = Robots(client)

            def want(u: str) -> bool:
                if urlparse(u).scheme not in ('http', 'https') or SKIP_EXT.search(urlparse(u).path):
                    return False
                if same_host and urlparse(u).netloc not in hosts:
                    return False
                return (not include or matches(u, include)) and not matches(u, exclude)

            def add(u: str, depth: int) -> None:
                nonlocal pending
                if u not in seen and want(u):
                    seen.add(u)
                    pending += 1
                    queue.put_nowait((u, depth))

            for s in starts:
                pending += 1
                queue.put_nowait((s, 0))
            if use_sitemap:
                for s in starts:
                    for u in await sitemap_urls(client, s, robots, max_pages * 3):
                        add(norm(u), 1)

            async def worker() -> None:
                nonlocal pending, n_ok
                while not stop.is_set():
                    try:
                        url, depth = await asyncio.wait_for(queue.get(), 1)
                    except asyncio.TimeoutError:
                        if pending <= 0:
                            return
                        continue
                    try:
                        if n_ok >= max_pages:
                            continue
                        ok, crawl_delay = await robots.allowed(url)
                        if not ok:
                            Actor.log.info(f'robots.txt disallows {url}')
                            await Actor.push_data({'type': 'skipped', 'url': url, 'reason': 'blocked by robots.txt'})
                            continue
                        host = urlparse(url).netloc
                        wait = last_hit.get(host, 0) + max(delay, crawl_delay) - time.monotonic()
                        last_hit[host] = time.monotonic() + max(wait, 0)
                        if wait > 0:
                            await asyncio.sleep(wait)
                        r = await client.get(url)
                        ctype = r.headers.get('content-type', '')
                        if r.status_code != 200 or 'html' not in ctype or len(r.content) > MAX_BYTES:
                            await Actor.push_data({'type': 'error', 'url': url, 'error': (f'HTTP {r.status_code}' if r.status_code != 200 else f'not HTML or over 3 MB ({ctype[:40]})')})
                            continue
                        page = r.text
                        if depth < max_depth:
                            for u in links_of(page, str(r.url)):
                                add(u, depth + 1)
                        res = extract(page, str(r.url), with_links)
                        if not res or n_ok >= max_pages:
                            continue
                        n_ok += 1
                        item = {'type': 'page', 'url': url, 'finalUrl': str(r.url), 'depth': depth, **res,
                                'wordCount': len(res['markdown'].split())}
                        if with_html:
                            item['html'] = page
                        # Charged per delivered page; skipped/error items are free.
                        out = await Actor.push_data(item, charged_event_name='page')
                        if out and out.event_charge_limit_reached:
                            Actor.log.info('Max charge limit reached, stopping.')
                            stop.set()
                    except Exception as e:  # noqa: BLE001 - one bad page must not fail the run
                        await Actor.push_data({'type': 'error', 'url': url, 'error': f'{type(e).__name__}: {e}'[:300]})
                    finally:
                        pending -= 1

            await asyncio.gather(*(worker() for _ in range(4)))
        Actor.log.info(f'Done: {n_ok} pages converted.')
