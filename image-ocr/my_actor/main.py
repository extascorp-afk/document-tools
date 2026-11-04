"""Bulk Image OCR Actor: downloads images by URL and extracts their text with Tesseract."""

from __future__ import annotations

import asyncio
import io
from typing import Any

import pytesseract
from apify import Actor, Event
from httpx2 import AsyncClient
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_IMAGE_BYTES = 30 * 1024 * 1024
PER_IMAGE_TIMEOUT_S = 120
Image.MAX_IMAGE_PIXELS = 100_000_000  # guard against decompression bombs


def ocr_image(data: bytes, lang: str, with_words: bool, psm: int) -> dict[str, Any]:
    try:
        img = Image.open(io.BytesIO(data))
    except UnidentifiedImageError:
        raise ValueError('URL did not return a supported image (PNG, JPEG, WebP, TIFF, BMP, GIF)') from None
    img = ImageOps.exif_transpose(img)  # phone photos carry their rotation in EXIF
    if img.mode not in ('RGB', 'L'):
        img = img.convert('RGB')
    config = f'--psm {psm}'
    d = pytesseract.image_to_data(img, lang=lang, config=config, output_type=pytesseract.Output.DICT)
    words = [
        {'text': t, 'confidence': round(float(c), 1), 'left': l, 'top': tp, 'width': w, 'height': h,
         'block': b, 'line': ln}
        for t, c, l, tp, w, h, b, ln in zip(
            d['text'], d['conf'], d['left'], d['top'], d['width'], d['height'], d['block_num'], d['line_num'],
            strict=True)
        if str(t).strip() and float(c) >= 0
    ]
    # Rebuild lines from Tesseract's block/line numbering.
    lines: dict[tuple[int, int], list[str]] = {}
    for w in words:
        lines.setdefault((w['block'], w['line']), []).append(w['text'])
    text = '\n'.join(' '.join(v) for v in lines.values())
    out: dict[str, Any] = {
        'text': text,
        'meanConfidence': round(sum(w['confidence'] for w in words) / len(words), 1) if words else 0,
        'wordCount': len(words),
        'imageWidth': img.width,
        'imageHeight': img.height,
    }
    if with_words:
        out['words'] = words
    return out


async def fetch(client: AsyncClient, url: str) -> bytes:
    async with client.stream('GET', url, follow_redirects=True) as resp:
        resp.raise_for_status()
        chunks, size = [], 0
        async for chunk in resp.aiter_bytes():
            size += len(chunk)
            if size > MAX_IMAGE_BYTES:
                raise ValueError(f'Image larger than {MAX_IMAGE_BYTES // 1024 // 1024} MB')
            chunks.append(chunk)
    return b''.join(chunks)


async def main() -> None:
    async with Actor:
        async def on_abort(_: object = None) -> None:
            await Actor.exit()

        Actor.on(Event.ABORTING, on_abort)
        inp = await Actor.get_input() or {}
        urls = [u.get('url') if isinstance(u, dict) else u for u in inp.get('imageUrls') or []]
        urls = [u.strip() for u in urls if isinstance(u, str) and u.strip()]
        if not urls:
            raise ValueError('Input "imageUrls" must contain at least one image URL.')
        lang = inp.get('language') or 'eng'
        with_words = bool(inp.get('includeWordBoxes', False))
        psm = int(inp.get('pageSegmentationMode') or 3)
        concurrency = max(1, min(int(inp.get('maxConcurrency') or 4), 16))
        sem, stop = asyncio.Semaphore(concurrency), asyncio.Event()

        async def process(client: AsyncClient, url: str) -> None:
            async with sem:
                if stop.is_set():
                    return
                item: dict[str, Any] = {'url': url}
                try:
                    data = await fetch(client, url)
                    res = await asyncio.wait_for(
                        asyncio.to_thread(ocr_image, data, lang, with_words, psm), PER_IMAGE_TIMEOUT_S)
                    item |= {'status': 'ok', **res}
                    # Users pay only for images that were read successfully.
                    if (await Actor.charge(event_name='image-ocr')).event_charge_limit_reached:
                        Actor.log.info('Max charge limit reached, stopping.')
                        stop.set()
                except Exception as e:  # noqa: BLE001 - one bad image must not fail the whole run
                    Actor.log.warning(f'Failed {url}: {e}')
                    item |= {'status': 'error', 'error': str(e) or type(e).__name__}
                await Actor.push_data(item)

        async with AsyncClient(timeout=60, headers={'User-Agent': 'Mozilla/5.0 (image-ocr Apify Actor)'}) as client:
            await asyncio.gather(*(process(client, u) for u in urls))
