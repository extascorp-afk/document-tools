# Bluesky Scraper: Posts, Profiles, Followers, Threads (No Login)

Collect **public Bluesky data** through the official AT Protocol API. No login, no cookies, no browser, no proxies. Just fast, structured JSON.

- **Search posts** by keyword, phrase, #hashtag, `from:handle`, with date range (`since` / `until`), language and sort
- **Posts of accounts** (author feed), with or without replies
- **Profiles**: bio, display name, followers / following / posts counts, avatar, creation date
- **Followers** and **following** lists of any account
- **Post thread**: the post and all replies underneath it
- Automatic retries with backoff on rate limits, cursor pagination, `maxItems` per entry
- **$0.50 per 1,000 results.** Failed lookups are never charged.

## How to use

1. Pick **What to collect**.
2. Fill the matching field: *Search keywords* (search), *Handles* (accounts, profiles, followers, following) or *Post URLs* (thread).
3. Set **Max results per entry** and click **Start**. Export as JSON, CSV or Excel, or use the API.

## Input examples

```json
{ "mode": "search", "queries": ["#ai", "from:bsky.app"], "since": "2026-01-01", "language": "en", "maxItems": 500 }
```
```json
{ "mode": "profiles", "handles": ["bsky.app", "https://bsky.app/profile/jay.bsky.team"] }
```
```json
{ "mode": "thread", "postUrls": ["https://bsky.app/profile/bsky.app/post/3l6oveex3ii2l"] }
```

## Output

Posts: `uri`, `url`, `text`, `createdAt`, `langs`, `authorHandle`, `authorDid`, `authorName`, `likeCount`, `repostCount`, `replyCount`, `quoteCount`, `isReply`, `replyToUri`, `hashtags`, `embed` (images, links, quoted posts).

Profiles (also used for followers / following): `did`, `handle`, `displayName`, `description`, `avatar`, `banner`, `followersCount`, `followsCount`, `postsCount`, `createdAt`.

Every item has `type` (`post`, `profile` or `error`) and `source` (the keyword / handle / URL that produced it). Items with `type: error` are free.

## Authentication

Not needed. The Actor uses the public AppView endpoints `getAuthorFeed`, `getProfile`, `getFollowers`, `getFollows`, `getPostThread` and `searchPosts`.

Notes on search without login: `Latest` sort pages through results by date, so you can collect thousands of posts per keyword. `Top` sort returns the first 100 results only, because Bluesky rejects search cursors for anonymous requests. If Bluesky ever blocks anonymous search from your region, supply your handle and an **app password** (bsky.app > Settings > Privacy and security > App passwords; never your main password). It is only used to log in during the run.

## Pricing

**Free during launch:** this Actor currently has no per-result fee. You only pay Apify platform usage, which the Free plan's monthly credit covers for normal use. The prices below are the regular prices and are not charged at the moment.

| Event | Price |
| --- | --- |
| Result (post or profile) | $0.0005 |

Only public data you asked for is collected. Please respect Bluesky's terms and applicable privacy law when using personal data.

## More tools

Need to turn PDFs, Word, Excel or images into Markdown for LLMs and RAG? See the [Document to Markdown API](https://rapidapi.com/ExtasCorporation/api/document-to-markdown) on RapidAPI and the free browser tools at [hackthehydra.com](https://hackthehydra.com).

## Example output

```json
{
  "type": "profile",
  "handle": "bsky.app",
  "displayName": "Bluesky",
  "followersCount": 35525482,
  "followsCount": 38,
  "postsCount": 916,
  "createdAt": "2023-04-12T04:53:57.057Z"
}
```

## Use cases

- **Social listening**: track keywords and hashtags in public posts.
- **Research**: collect threads, followers and profiles for network studies.
- **LLM datasets**: gather public post text by topic and date range.

## Integrations

Python (Apify client):

```python
from apify_client import ApifyClient

client = ApifyClient("<APIFY_TOKEN>")
run = client.actor("extas_corp/bluesky-scraper").call(run_input={"mode": "search", "queries": ["apify"], "maxItems": 50})
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item["type"], item.get("text") or item.get("handle"))
```

**Make, Zapier, n8n**: add the Apify app, choose *Run Actor* (or *Run Actor and get dataset items*), set the Actor to `extas_corp/bluesky-scraper` and map the JSON input. The same Actor can be started on a schedule from Apify itself, with a webhook to your own endpoint when the run finishes.

## FAQ

**Do I need a Bluesky account?** No for public data. Some endpoints can use an app password, never your main password.

**Do I need to pay to try it?** New Apify accounts include free monthly platform credit (about $5 on the free plan at the time of writing), so you can run the example input above and many more items before paying anything. You only pay the per-event price listed under Pricing; runs that return nothing or fail are not charged for the failed items.
