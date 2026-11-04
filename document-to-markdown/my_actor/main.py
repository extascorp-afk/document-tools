"""Document to Markdown Actor: Word, PowerPoint, Excel, HTML, EPUB, CSV, JSON, XML, Outlook MSG -> Markdown."""

from __future__ import annotations

import asyncio
import io
import mimetypes
import os
from typing import Any
from urllib.parse import unquote, urlparse

from apify import Actor, Event
from httpx2 import AsyncClient
from markitdown import MarkItDown, StreamInfo

MAX_BYTES = 50 * 1024 * 1024
PER_DOC_TIMEOUT_S = 180
# PDFs go to the dedicated PDF Actor (better tables + OCR); audio/YouTube converters are not offered.
SUPPORTED = {'.docx', '.pptx', '.xlsx', '.xls', '.html', '.htm', '.epub', '.csv', '.json', '.xml', '.msg', '.txt',
             '.md', '.rss', '.atom', '.ipynb', '.zip'}

md = MarkItDown(enable_plugins=False)


def convert(data: bytes, ext: str, mimetype: str | None, url: str) -> dict[str, Any]:
    res = md.convert_stream(io.BytesIO(data), stream_info=StreamInfo(extension=ext or None, mimetype=mimetype, url=url))
    text = (res.markdown or '').strip()
    return {'markdown': text + '\n', 'title': res.title, 'charCount': len(text)}


def guess_ext(url: str, content_type: str | None, disposition: str | None) -> str:
    if disposition and 'filename=' in disposition:
        name = disposition.split('filename=')[-1].strip('"\'; ')
        if ext := os.path.splitext(name)[1].lower():
            return ext
    if ext := os.path.splitext(unquote(urlparse(url).path))[1].lower():
        return ext
    return (mimetypes.guess_extension(content_type.split(';')[0].strip()) or '') if content_type else ''


async def fetch(client: AsyncClient, url: str) -> tuple[bytes, str, str | None]:
    async with client.stream('GET', url, follow_redirects=True) as resp:
        resp.raise_for_status()
        chunks, size = [], 0
        async for chunk in resp.aiter_bytes():
            size += len(chunk)
            if size > MAX_BYTES:
                raise ValueError(f'File larger than {MAX_BYTES // 1024 // 1024} MB')
            chunks.append(chunk)
        ctype = resp.headers.get('content-type')
        ext = guess_ext(str(resp.url), ctype, resp.headers.get('content-disposition'))
    return b''.join(chunks), ext, ctype


async def main() -> None:
    async with Actor:
        async def on_abort(_: object = None) -> None:
            await Actor.exit()

        Actor.on(Event.ABORTING, on_abort)
        inp = await Actor.get_input() or {}
        urls = [u.get('url') if isinstance(u, dict) else u for u in inp.get('documentUrls') or []]
        urls = [u.strip() for u in urls if isinstance(u, str) and u.strip()]
        if not urls:
            raise ValueError('Input "documentUrls" must contain at least one document URL.')
        concurrency = max(1, min(int(inp.get('maxConcurrency') or 4), 16))
        sem, stop = asyncio.Semaphore(concurrency), asyncio.Event()

        async def process(client: AsyncClient, url: str) -> None:
            async with sem:
                if stop.is_set():
                    return
                item: dict[str, Any] = {'url': url}
                try:
                    data, ext, ctype = await fetch(client, url)
                    if ext == '.pdf' or data[:5] == b'%PDF-':
                        raise ValueError('PDF detected: use the "PDF to Markdown Converter (Tables + OCR)" Actor')
                    if ext and ext not in SUPPORTED:
                        raise ValueError(f'Unsupported file type {ext}')
                    res = await asyncio.wait_for(asyncio.to_thread(convert, data, ext, ctype, url), PER_DOC_TIMEOUT_S)
                    if not res['charCount']:
                        raise ValueError('No text could be extracted from this document')
                    item |= {'status': 'ok', 'fileType': ext.lstrip('.') or None, **res}
                    # Users pay only for documents that converted successfully.
                    if (await Actor.charge(event_name='document-converted')).event_charge_limit_reached:
                        Actor.log.info('Max charge limit reached, stopping.')
                        stop.set()
                except Exception as e:  # noqa: BLE001 - one bad file must not fail the whole run
                    Actor.log.warning(f'Failed {url}: {e}')
                    item |= {'status': 'error', 'error': str(e) or type(e).__name__}
                await Actor.push_data(item)

        async with AsyncClient(timeout=60, headers={'User-Agent': 'Mozilla/5.0 (document-to-markdown Apify Actor)'}) as client:
            await asyncio.gather(*(process(client, u) for u in urls))
