# Apple App Store Reviews Scraper

Download **App Store reviews** for any iPhone, iPad or Mac app from **Apple's official customer-reviews feed** (the public RSS/JSON feed behind apps.apple.com) plus the iTunes lookup/search APIs. No login, no cookies, no browser, no proxies.

- **Any app**: paste an App Store URL, a numeric app ID, or just the app name
- **Any country**: one run can cover many storefronts (`us`, `gb`, `de`, `fr`, `jp`, ...)
- **Filters**: newest or most helpful first, star range (e.g. 1-2 stars to find complaints), `since` date
- Each review carries the app's name, developer, current average rating and rating count
- Up to 500 reviews per app and country (the limit of Apple's feed)
- **$0.20 per 1,000 reviews.** Failed lookups are never charged.

## Input examples

```json
{ "apps": ["389801252"], "countries": ["us"], "maxReviews": 100 }
```
```json
{ "apps": ["Duolingo", "https://apps.apple.com/gb/app/spotify-music-and-podcasts/id324684580"], "countries": ["us", "gb", "de"], "maxRating": 2, "since": "2026-01-01", "maxReviews": 500 }
```

## Output

`type` (`review` or `error`), `appId`, `appName`, `developer`, `appRating`, `appRatingCount`, `country`, `reviewId`, `rating` (1-5), `title`, `text`, `version`, `author` (public display name), `date` (ISO 8601 UTC), `helpfulVotes`, `totalVotes`, `appUrl`, `source`.

## Notes

- Apple only exposes the most recent 500 reviews per app and storefront; run several countries for more coverage.
- Review volume per country differs a lot; small storefronts may return few reviews.
- Items with `type: error` are free.

## Pricing

| Event | Price |
| --- | --- |
| Review | $0.0002 |

Data comes from Apple's public feeds. Reviews contain public display names; please respect applicable privacy law when using them.
