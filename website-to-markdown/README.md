# Website to Markdown Crawler for LLM and RAG

Turn any website into **clean Markdown, one record per page**, ready for LLM context, RAG vector stores, fine-tuning sets and AI agents. It strips navigation, footers, cookie banners and ads, keeps headings, lists, tables, code blocks and (optionally) links, and returns title, author, date and language as metadata.

- **Lightweight**: plain HTTP + main-content extraction (trafilatura). No browser, no proxies, so it is cheap and fast. Works on server-rendered pages (docs, blogs, wikis, news, product docs). It does not run JavaScript, so pure single-page apps may come back empty.
- **Polite by design**: obeys `robots.txt` (including Crawl-delay), identifies itself with a clear User-Agent, throttles per host. Pages blocked by robots.txt are reported as free `skipped` items.
- **Whole-site coverage**: follow links to a chosen depth and/or seed from `sitemap.xml`; include/exclude URL patterns; stay on the same host.
- **$1 per 1,000 pages.** Skipped pages and errors are never charged.

## Input examples

Convert one page:
```json
{ "startUrls": [{ "url": "https://docs.python.org/3/tutorial/index.html" }], "maxDepth": 0 }
```

Crawl a documentation section for a RAG index:
```json
{
  "startUrls": [{ "url": "https://docs.apify.com/academy" }],
  "maxPages": 200, "maxDepth": 3, "useSitemap": true,
  "includeUrlGlobs": ["https://docs.apify.com/academy/*"],
  "excludeUrlGlobs": ["*/changelog*"], "keepLinks": false
}
```

## Output

Each item: `type` (`page`, `skipped` or `error`), `url`, `finalUrl`, `depth`, `title`, `description`, `author`, `date`, `language`, `markdown`, `wordCount`, and `html` if requested.

```json
{ "type": "page", "url": "https://docs.python.org/3/tutorial/index.html", "title": "The Python Tutorial", "language": "en", "wordCount": 361, "markdown": "# The Python Tutorial\n\n..." }
```

## Use with the API

```bash
curl -X POST "https://api.apify.com/v2/acts/extas_corp~website-to-markdown/run-sync-get-dataset-items?token=$APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"startUrls":[{"url":"https://example.com"}],"maxDepth":0}'
```

Works with LangChain, LlamaIndex, n8n, Make and the Apify MCP server.

## Pricing

| Event | Price |
| --- | --- |
| Page converted | $0.001 |

## Notes

- Only crawl content you are allowed to process. The Actor respects robots.txt, but you remain responsible for the site's terms and for copyright.
- Need PDFs, Word, Excel or PowerPoint instead of web pages? See [PDF to Markdown](https://apify.com/extas_corp/pdf-to-markdown) and [Document to Markdown](https://apify.com/extas_corp/document-to-markdown). Free browser tools: [hackthehydra.com](https://hackthehydra.com).
