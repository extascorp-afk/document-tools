# Hacker News Scraper: Stories, Comments, Search, Who is Hiring

Collect **Hacker News data** through the two official free APIs (HN Firebase API and Algolia HN Search). No login, no cookies, no browser, no proxies. Clean flat JSON.

- **Story lists**: front page, top, new, best, Ask HN, Show HN, jobs
- **Search** stories and/or comments by keyword, with date range, minimum points / comments, sort by relevance or newest
- **Full comment trees** for story IDs or `news.ycombinator.com/item?id=...` URLs (flattened, with `parent_id` and `story_id`)
- **User profiles** (karma, about, created) and their stories and comments
- **Who is hiring**: every posting of the monthly thread (also "Who wants to be hired?" and "Freelancer?"), any month
- `maxItems` per entry, automatic retries with backoff
- **$0.30 per 1,000 results.** Failed lookups are never charged.

## How to use

1. Pick **What to collect**.
2. Fill the matching field: *List* (lists), *Search keywords* (search), *Story IDs or URLs* (thread), *Usernames* (user), or just a month (hiring).
3. Set **Max results per entry** and click **Start**. Export as JSON, CSV or Excel, or use the API.

## Input examples

```json
{ "mode": "list", "lists": ["front", "show"], "maxItems": 30 }
```
```json
{ "mode": "search", "queries": ["web scraping"], "searchIn": "both", "sort": "date", "since": "2026-01-01", "minPoints": 10, "maxItems": 500 }
```
```json
{ "mode": "thread", "storyIds": ["8863", "https://news.ycombinator.com/item?id=39667625"], "maxItems": 1000 }
```
```json
{ "mode": "user", "usernames": ["pg"], "maxItems": 100 }
```
```json
{ "mode": "hiring", "hiringMonth": "2026-10", "maxItems": 1000 }
```

## Output

Every item: `type` (`story`, `comment`, `job`, `poll`, `user` or `error`), `id`, `title`, `url`, `domain`, `author`, `points`, `num_comments`, `created_at` (ISO 8601), `text` (plain text, HTML removed), `parent_id`, `story_id`, `hn_url`, `source` (the list / keyword / ID that produced it).

Users add `karma` and `submitted_count`. In *hiring* mode each item is one posting and `num_comments` counts the replies to it. Items with `type: error` are free.

## Notes

- *Top* returns up to 500 stories, *front page* about 30 (the real front page).
- Relevance search is capped by Algolia at 1,000 hits per keyword; use "Newest first" to go further back.
- Comment items found by search carry the parent story's `title` and `url`.

## Pricing

| Event | Price |
| --- | --- |
| Result (story, comment, posting or profile) | $0.0003 |

Data comes from public APIs. Please respect applicable privacy law when using personal data.

## More tools

Need to turn PDFs, Word, Excel or images into Markdown for LLMs and RAG? See the [Document to Markdown API](https://rapidapi.com/ExtasCorporation/api/document-to-markdown) on RapidAPI and the free browser tools at [hackthehydra.com](https://hackthehydra.com).

## Example output

```json
{
  "type": "comment",
  "id": 50338732,
  "author": "AdriaanvRossum",
  "num_comments": 4,
  "created_at": "2026-11-02T16:01:43.000Z",
  "text": "Simple Analytics | DevOps Engineer | REMOTE ...",
  "source": "hiring 2026-11"
}
```

## Use cases

- **Research**: pull all discussion of a technology or company, filtered by points and date.
- **Recruiting and SEO**: parse every posting of the monthly Who is hiring thread.
- **LLM datasets**: export comment trees for summarisation.

## Integrations

Python (Apify client):

```python
from apify_client import ApifyClient

client = ApifyClient("<APIFY_TOKEN>")
run = client.actor("extas_corp/hackernews-scraper").call(run_input={"mode": "list", "list": "top", "maxItems": 20})
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item["type"], item.get("title"))
```

**Make, Zapier, n8n**: add the Apify app, choose *Run Actor* (or *Run Actor and get dataset items*), set the Actor to `extas_corp/hackernews-scraper` and map the JSON input. The same Actor can be started on a schedule from Apify itself, with a webhook to your own endpoint when the run finishes.

## FAQ

**Where does the data come from?** The official HN Firebase API and Algolia HN Search. No scraping of the website.

**Do I need to pay to try it?** New Apify accounts include free monthly platform credit (about $5 on the free plan at the time of writing), so you can run the example input above and many more items before paying anything. You only pay the per-event price listed under Pricing; runs that return nothing or fail are not charged for the failed items.
