# Hacker News Scraper: Stories, Comments, Search, Jobs

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
