"""PDF to Markdown Actor: downloads PDFs, converts them to clean Markdown (headings, paragraphs, tables, OCR fallback)."""

from __future__ import annotations

import asyncio
from typing import Any

from apify import Actor, Event
from httpx2 import AsyncClient

from .convert import pdf_to_markdown

MAX_PDF_BYTES = 100 * 1024 * 1024
PER_PDF_TIMEOUT_S = 300


def make_ocr(lang: str):
    import pytesseract  # imported lazily: only needed for scanned pages

    def ocr(page: Any) -> str:
        image = page.to_image(resolution=200).original
        return pytesseract.image_to_string(image, lang=lang)

    return ocr


async def fetch_pdf(client: AsyncClient, url: str) -> bytes:
    async with client.stream('GET', url, follow_redirects=True) as resp:
        resp.raise_for_status()
        chunks, size = [], 0
        async for chunk in resp.aiter_bytes():
            size += len(chunk)
            if size > MAX_PDF_BYTES:
                raise ValueError(f'PDF larger than {MAX_PDF_BYTES // 1024 // 1024} MB')
            chunks.append(chunk)
    data = b''.join(chunks)
    if not data.lstrip()[:5].startswith(b'%PDF'):
        raise ValueError('URL did not return a PDF file')
    return data


async def main() -> None:
    async with Actor:
        async def on_abort(_: object = None) -> None:
            await Actor.exit()

        Actor.on(Event.ABORTING, on_abort)
        inp = await Actor.get_input() or {}
        urls = [u.get('url') if isinstance(u, dict) else u for u in inp.get('pdfUrls') or []]
        urls = [u.strip() for u in urls if isinstance(u, str) and u.strip()]
        if not urls:
            raise ValueError('Input "pdfUrls" must contain at least one PDF URL.')
        with_tables = bool(inp.get('extractTables', True))
        max_pages = int(inp.get('maxPages') or 0)
        ocr = make_ocr(inp.get('ocrLanguage') or 'eng') if inp.get('ocrScannedPages', True) else None
        concurrency = max(1, min(int(inp.get('maxConcurrency') or 4), 16))

        sem = asyncio.Semaphore(concurrency)
        stop = asyncio.Event()

        async def process(client: AsyncClient, url: str) -> None:
            async with sem:
                if stop.is_set():
                    return
                item: dict[str, Any] = {'url': url}
                try:
                    data = await fetch_pdf(client, url)
                    res = await asyncio.wait_for(
                        asyncio.to_thread(pdf_to_markdown, data, with_tables=with_tables, max_pages=max_pages, ocr=ocr),
                        PER_PDF_TIMEOUT_S,
                    )
                    item |= {
                        'status': 'ok',
                        'markdown': res.markdown,
                        'pageCount': res.page_count,
                        'pagesProcessed': res.pages_processed,
                        'ocrPages': res.ocr_pages,
                        'tableCount': res.table_count,
                        'charCount': len(res.markdown),
                        'title': res.metadata.get('Title'),
                        'author': res.metadata.get('Author'),
                        'metadata': res.metadata,
                    }
                    # Users pay only for PDFs that converted successfully.
                    charge = await Actor.charge(event_name='pdf-processed')
                    if res.ocr_pages:
                        await Actor.charge(event_name='ocr-page', count=res.ocr_pages)
                    if charge.event_charge_limit_reached:
                        Actor.log.info('Max charge limit reached, stopping.')
                        stop.set()
                except Exception as e:  # noqa: BLE001 - one bad PDF must not fail the whole run
                    Actor.log.warning(f'Failed {url}: {e}')
                    item |= {'status': 'error', 'error': str(e) or type(e).__name__}
                await Actor.push_data(item)

        async with AsyncClient(timeout=60, headers={'User-Agent': 'Mozilla/5.0 (pdf-to-markdown Apify Actor)'}) as client:
            await asyncio.gather(*(process(client, u) for u in urls))
