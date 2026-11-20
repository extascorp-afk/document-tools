# Domain Availability Checker: Bulk RDAP, Expiry Date & Days Left

Paste a list of domains and get, for each one, whether it is **available or registered**, and for registered domains **when it expires**, the registrar, the registry status codes, the nameservers and DNSSEC. Two jobs in one Actor:

- **Finding a name**: give bare names and a list of TLDs (`mybrand` x `com, io, dev`) and see which combinations are free.
- **Watching a portfolio**: schedule it and get a warning before one of your domains, or a client's, expires or falls into redemption.

The answers come from the registries themselves through **RDAP**, the official successor of WHOIS, found through the IANA bootstrap list. No login, no browser, no proxies, no WHOIS text parsing.

- `available`: true, false, or null when the registry cannot confirm it (see Limits)
- `expiresAt`, `daysLeft`, and `expiresSoon` with your own threshold (default 30 days)
- `registrar` and its IANA id, `createdAt`, `updatedAt`
- `statuses` exactly as published (`client transfer prohibited`, `redemption period`, `pending delete`, `client hold`...), with a warning for the ones that mean trouble
- `nameservers` and `dnssec`
- Subdomains and URLs are reduced to the registrable domain (`https://www.example.co.uk/page` is checked as `example.co.uk`)
- Polite by design: a few parallel requests per registry, automatic wait and retry when a registry asks to slow down
- Errors are reported per domain, they never stop the run
- **No personal data**: only the registrar (a company) is read. Registrant, admin and technical contacts are never collected.
- **Free during launch**: no per-domain fee at the moment, you only pay Apify platform usage (covered by the Free plan's monthly credit for normal use).

## Input example

```json
{
  "domains": ["apify.com", "https://github.com/login", "mybrandidea2027"],
  "tlds": ["com", "net", "org", "dev"],
  "warnDays": 30
}
```

`apify.com` and `github.com` are checked as they are. `mybrandidea2027` has no dot, so it is combined with the four TLDs. Duplicates are checked once.

## Example output

A registered domain (real run):
```json
{
  "domain": "github.com",
  "available": false,
  "source": "rdap",
  "error": null,
  "registrar": "MarkMonitor Inc.",
  "registrarIanaId": "292",
  "createdAt": "2007-10-09T18:20:50+00:00",
  "updatedAt": "2026-09-07T09:22:52+00:00",
  "expiresAt": "2028-10-09T18:20:50+00:00",
  "daysLeft": 689,
  "expiresSoon": false,
  "statuses": ["client delete prohibited", "client transfer prohibited", "client update prohibited"],
  "nameservers": ["dns1.p08.nsone.net", "dns2.p08.nsone.net", "dns3.p08.nsone.net", "dns4.p08.nsone.net", "ns-1283.awsdns-32.org", "ns-1707.awsdns-21.co.uk", "ns-421.awsdns-52.com", "ns-520.awsdns-01.net"],
  "dnssec": false,
  "warnings": []
}
```

A free name (real run, shortened):
```json
{
  "domain": "mybrandidea2027.dev",
  "available": true,
  "source": "rdap",
  "expiresAt": null,
  "warnings": []
}
```

A TLD without RDAP (real run, shortened):
```json
{
  "domain": "stripe.io",
  "available": false,
  "source": "dns",
  "expiresAt": null,
  "nameservers": ["ns-1177.awsdns-19.org", "ns-126.awsdns-15.com", "ns-1979.awsdns-55.co.uk", "ns-856.awsdns-43.net"],
  "warnings": ["this TLD has no RDAP service: registered (found in DNS), no expiry date available"]
}
```

## Use cases

- **Domain expiry monitoring**: schedule the Actor weekly and alert (Make, Zapier, n8n, webhooks, e-mail) when `expiresSoon` is true or `warnings` is not empty
- **Agencies and IT teams**: one run for every client domain, exported as CSV or Excel with expiry date and registrar
- **Naming a product or a company**: test a list of name ideas across several TLDs in one run
- **Due diligence**: registration date, registrar and status of the domains of a company you are about to buy from or acquire
- **Before a migration**: nameservers and DNSSEC state of every domain in one table

## Integrations

Python:
```python
from apify_client import ApifyClient
client = ApifyClient("<YOUR_API_TOKEN>")
run = client.actor("extas_corp/domain-availability-checker").call(
    run_input={"domains": ["example.com", "mybrand"], "tlds": ["com", "io"], "warnDays": 45})
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item["domain"], item["available"], item["expiresAt"], item["warnings"], item["error"])
```
Results can be exported as CSV, Excel or JSON from the dataset, or pushed to Google Sheets, Make, Zapier or n8n.

## Limits

- **`available: true` means the registry has no registration for that name.** A registry can still refuse it (reserved names, such as most one-letter names) or sell it at a premium price. The final answer is always the registrar's checkout.
- **TLDs without RDAP** (for example .io, .de, .co, .me, .eu, .it, .es, .ch, .us, .jp at the time of writing): the Actor falls back to DNS. A name found in DNS is reported as registered, without expiry date or registrar. A name not found in DNS gets `available: null` and a warning, because a domain can be registered without nameservers.
- Some registries do not publish an expiry date or a registrar: those fields are then null, never guessed.
- The expiry date is the registry's. During the grace period after expiry the domain is still registered: `daysLeft` is negative and a warning says so.
- Registries rate-limit RDAP. The Actor slows down and retries (up to 4 attempts); a domain still refused is returned with `error`, run it again later.
- Subdomains are not checked separately: only the registrable domain is.
- No registrant or contact data, by design. This is not a WHOIS contact lookup.

## FAQ

**Is RDAP more reliable than WHOIS?** It is the same registry data in a structured, standard format (JSON), so there is no text parsing that breaks when a registry changes its layout.

**Why is `available` null?** The TLD has no RDAP server and the name is not in DNS. It is probably free, but only the registry or a registrar can confirm it.

**Does it need a proxy or a browser?** No. One HTTPS request to the registry per domain.

**Can it tell me the price of a domain?** No. Prices depend on the registrar.

**Do I need to pay to try it?** The Apify Free plan includes monthly platform credit, enough to check thousands of domains.
