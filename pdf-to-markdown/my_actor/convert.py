"""PDF bytes -> Markdown. Pure functions, no Apify dependency, so they can be tested locally."""

from __future__ import annotations

import io
import statistics
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import pdfplumber

# A page with fewer real characters than this is treated as scanned (image only) and sent to OCR.
MIN_CHARS_FOR_TEXT_LAYER = 25


@dataclass
class PdfResult:
    markdown: str
    page_count: int
    pages_processed: int
    ocr_pages: int
    table_count: int
    metadata: dict[str, Any] = field(default_factory=dict)


def _cell(value: Any) -> str:
    return ' '.join(str(value or '').split()).replace('|', '\\|')


def table_to_markdown(rows: list[list[Any]]) -> str:
    rows = [r for r in rows if r and any(c not in (None, '') for c in r)]
    if not rows:
        return ''
    width = max(len(r) for r in rows)
    rows = [list(r) + [None] * (width - len(r)) for r in rows]
    lines = ['| ' + ' | '.join(_cell(c) for c in rows[0]) + ' |', '|' + ' --- |' * width]
    lines += ['| ' + ' | '.join(_cell(c) for c in r) + ' |' for r in rows[1:]]
    return '\n'.join(lines)


def _heading_prefix(size: float, body: float) -> str:
    if size >= body * 1.6:
        return '# '
    if size >= body * 1.3:
        return '## '
    if size >= body * 1.12:
        return '### '
    return ''


def _page_blocks(page: Any, body_size: float, with_tables: bool) -> tuple[list[tuple[float, str]], int]:
    """Return (top, markdown) blocks for one page, sorted by vertical position, plus the table count."""
    blocks: list[tuple[float, str]] = []
    bboxes = []
    if with_tables:
        for table in page.find_tables():
            rows = table.extract()
            # Boxes drawn around text (1 row or 1 column) are layout, not data tables.
            if len(rows) < 2 or max(len(r) for r in rows) < 2:
                continue
            # A frame around a text block: one huge cell, or mostly empty cells.
            cells = [c for r in rows for c in r]
            filled = [c for c in cells if c not in (None, '')]
            if any(len(str(c)) > 400 for c in filled) or len(filled) < 0.4 * len(cells):
                continue
            md = table_to_markdown(rows)
            if md:
                bboxes.append(table.bbox)
                blocks.append((table.bbox[1], md))

    def outside_tables(obj: dict) -> bool:
        if obj.get('object_type') != 'char':
            return True
        x, top = (obj['x0'] + obj['x1']) / 2, (obj['top'] + obj['bottom']) / 2
        return not any(b[0] <= x <= b[2] and b[1] <= top <= b[3] for b in bboxes)

    text_page = page.filter(outside_tables) if bboxes else page
    paragraph: list[str] = []
    para_top = 0.0
    last_bottom = None
    heading: list[str] = []  # consecutive lines with the same heading size
    heading_prefix = ''
    heading_top = 0.0

    def flush() -> None:
        if paragraph:
            blocks.append((para_top, ' '.join(paragraph)))
            paragraph.clear()

    def flush_heading() -> None:
        nonlocal heading_prefix
        if heading:
            text = ' '.join(heading)
            # More than 2 lines in a big font is a styled paragraph, not a heading.
            blocks.append((heading_top, text if len(heading) > 2 or len(text) > 150 else heading_prefix + text))
            heading.clear()
        heading_prefix = ''

    for line in text_page.extract_text_lines(return_chars=True, strip=True, x_tolerance_ratio=0.15):
        text = line['text'].strip()
        if not text:
            continue
        sizes = [c['size'] for c in line['chars'] if c['text'].strip()]
        prefix = _heading_prefix(statistics.median(sizes), body_size) if sizes else ''
        gap = line['top'] - last_bottom if last_bottom is not None else 0
        last_bottom = line['bottom']
        if prefix:
            flush()
            if prefix != heading_prefix:
                flush_heading()
                heading_prefix, heading_top = prefix, line['top']
            heading.append(text)
            continue
        flush_heading()
        # A vertical gap bigger than ~one line height starts a new paragraph.
        if paragraph and gap > (line['bottom'] - line['top']) * 0.9:
            flush()
        if not paragraph:
            para_top = line['top']
        if paragraph and paragraph[-1].endswith('-') and not paragraph[-1].endswith(' -'):
            paragraph[-1] = paragraph[-1][:-1] + text  # re-join a hyphenated word
        else:
            paragraph.append(text)
    flush()
    flush_heading()
    blocks.sort(key=lambda b: b[0])
    return blocks, len(bboxes)


def column_split(page: Any) -> float | None:
    """Return the x of the gutter if the page body is laid out in two columns, else None."""
    words = page.extract_words()
    if len(words) < 80:
        return None
    w = float(page.width)
    # Ignore full-width lines (titles, abstracts) when looking for the gutter.
    narrow = [x for x in words if (x['x1'] - x['x0']) < w * 0.4]
    best_x, best_cross = None, None
    for i in range(35, 66):
        x = w * i / 100
        cross = sum(1 for wd in narrow if wd['x0'] < x < wd['x1'])
        if best_cross is None or cross < best_cross:
            best_x, best_cross = x, cross
    left = sum(1 for wd in narrow if wd['x1'] <= best_x)
    right = sum(1 for wd in narrow if wd['x0'] >= best_x)
    # A real gutter: few words cross it (titles, figure labels), and both sides hold a good share of the text.
    if best_cross <= len(narrow) * 0.05 and min(left, right) >= len(narrow) * 0.3:
        return best_x
    return None


def column_regions(page: Any, gutter: float) -> list[tuple[float, float, float, float]]:
    """Split a two-column page into crop boxes in reading order.

    Horizontal bands containing words that cross the gutter (titles, full-width figures) are read
    full width; the bands between them are read left column first, then right column.
    """
    h, w = float(page.height), float(page.width)
    spans = sorted((wd['top'] - 2, wd['bottom'] + 2) for wd in page.extract_words() if wd['x0'] < gutter < wd['x1'])
    merged: list[list[float]] = []
    for top, bottom in spans:
        if merged and top <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], bottom)
        else:
            merged.append([top, bottom])
    boxes, y = [], 0.0
    for top, bottom in merged + [[h, h]]:
        top, bottom = max(top, 0.0), min(bottom, h)
        if top - y > 1:
            boxes += [(0, y, gutter, top), (gutter, y, w, top)]
        if bottom - top > 0:
            boxes.append((0, top, w, bottom))
        y = max(y, bottom)
    return boxes


def pdf_to_markdown(
    data: bytes,
    *,
    with_tables: bool = True,
    max_pages: int = 0,
    ocr: Callable[[Any], str] | None = None,
    password: str | None = None,
) -> PdfResult:
    """Convert PDF bytes to Markdown. `ocr(page)` is called for pages without a text layer, if given."""
    with pdfplumber.open(io.BytesIO(data), password=password or '') as pdf:
        pages = pdf.pages if max_pages <= 0 else pdf.pages[:max_pages]
        sizes = [c['size'] for p in pages[:20] for c in p.chars if c['text'].strip()]
        body = statistics.mode(round(s, 1) for s in sizes) if sizes else 10.0
        parts: list[str] = []
        ocr_pages = tables = 0
        for page in pages:
            if len([c for c in page.chars if c['text'].strip()]) < MIN_CHARS_FOR_TEXT_LAYER and ocr:
                text = ocr(page).strip()
                ocr_pages += 1
                if text:
                    parts.append(text)
                continue
            split = column_split(page)
            if split:
                # Two-column layout: full-width bands as is, column bands left then right.
                blocks, n = [], 0
                for box in column_regions(page, split):
                    b, k = _page_blocks(page.within_bbox(box), body, with_tables)  # within_bbox: no duplicated chars at band edges
                    blocks += b
                    n += k
            else:
                blocks, n = _page_blocks(page, body, with_tables)
            tables += n
            if blocks:
                parts.append('\n\n'.join(b[1] for b in blocks))
        meta = {k: v for k, v in (pdf.metadata or {}).items() if isinstance(v, str | int | float)}
        return PdfResult(
            markdown='\n\n'.join(parts).strip() + '\n',
            page_count=len(pdf.pages),
            pages_processed=len(pages),
            ocr_pages=ocr_pages,
            table_count=tables,
            metadata=meta,
        )
