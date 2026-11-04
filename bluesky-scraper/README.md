# Bluesky Scraper: Posts, Profiles, Followers, Threads

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

| Event | Price |
| --- | --- |
| Result (post or profile) | $0.0005 |

Only public data you asked for is collected. Please respect Bluesky's terms and applicable privacy law when using personal data.
