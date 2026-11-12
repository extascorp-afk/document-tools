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

**Free during launch:** this Actor currently has no per-result fee. You only pay Apify platform usage, which the Free plan's monthly credit covers for normal use. The prices below are the regular prices and are not charged at the moment.

| Event | Price |
| --- | --- |
| Page converted | $0.001 |

## Notes

- Only crawl content you are allowed to process. The Actor respects robots.txt, but you remain responsible for the site's terms and for copyright.
- Need PDFs, Word, Excel or PowerPoint instead of web pages? See [PDF to Markdown](https://apify.com/extas_corp/pdf-to-markdown) and [Document to Markdown](https://apify.com/extas_corp/document-to-markdown). Free browser tools: [hackthehydra.com](https://hackthehydra.com).

## Use cases

- **LLM and RAG**: index a whole documentation site or knowledge base as clean Markdown.
- **SEO and content audits**: pull titles, descriptions and body text of every page, filtered by URL pattern.
- **Research**: archive blogs, wikis or news sections in a readable, diffable format.

## Integrations

Python (Apify client):

```python
from apify_client import ApifyClient

client = ApifyClient("<APIFY_TOKEN>")
run = client.actor("extas_corp/website-to-markdown").call(run_input={"startUrls": [{"url": "https://docs.python.org/3/tutorial/index.html"}], "maxPages": 20})
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item["title"], item["wordCount"])
```

**LangChain / RAG** (turn each result into a `Document`):

```python
from apify_client import ApifyClient
from langchain_core.documents import Document

client = ApifyClient("<APIFY_TOKEN>")
run = client.actor("extas_corp/website-to-markdown").call(run_input={"startUrls": [{"url": "https://docs.python.org/3/tutorial/index.html"}], "maxPages": 20})
docs = [Document(page_content=i["markdown"], metadata={"source": i.get("url")})
        for i in client.dataset(run["defaultDatasetId"]).iterate_items() if i.get("markdown")]
```

**Make, Zapier, n8n**: add the Apify app, choose *Run Actor* (or *Run Actor and get dataset items*), set the Actor to `extas_corp/website-to-markdown` and map the JSON input. The same Actor can be started on a schedule from Apify itself, with a webhook to your own endpoint when the run finishes.

## FAQ

**Does it run JavaScript?** No. It fetches server-rendered HTML, which is why it is cheap. Pure single-page apps may come back empty.

**Does it respect robots.txt?** Yes, including Crawl-delay. Blocked pages are returned as free `skipped` items.

**Are failed pages charged?** No. Only pages converted to Markdown are charged.

**Do I need to pay to try it?** New Apify accounts include free monthly platform credit (about $5 on the free plan at the time of writing), so you can run the example input above and many more items before paying anything. You only pay the per-event price listed under Pricing; runs that return nothing or fail are not charged for the failed items.
