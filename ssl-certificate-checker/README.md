# SSL Certificate Checker: Bulk Expiry, Issuer & Trust Monitor

Paste a list of domains and get, for each one, **when its SSL/TLS certificate expires**, who issued it, which names it covers and whether a normal client would trust it. Schedule it daily and you have a certificate expiry monitor for all your sites, your clients' sites or your vendors.

No login, no browser, no proxies: one TLS handshake per host, nothing is downloaded from the site.

- **Expiry**: `validTo`, `daysLeft`, `expired`, and `expiresSoon` with your own threshold (default 30 days)
- **Trust**: `trusted` is false when the chain is untrusted, self-signed, expired or the **hostname does not match**, with the exact reason in `trustError`
- The certificate is still read and reported when it is not trusted (that is when you need the details most)
- Issuer, subject, all alternative names (SANs), wildcard flag, serial number, signature hash
- Negotiated TLS version and cipher
- Any TLS port: `example.com:8443`, `smtp.example.com:465`, `imap.example.com:993`
- DNS, connection and timeout errors are reported per host, they never stop the run
- One `ok` column to filter and alert on: trusted, not expired, not expiring soon
- Up to 100 hosts in parallel
- **Free during launch**: no per-host fee at the moment, you only pay Apify platform usage (covered by the Free plan's monthly credit for normal use).

## Input example

```json
{
  "domains": ["apify.com", "https://github.com/login", "smtp.gmail.com:465", "expired.badssl.com"],
  "warnDays": 30
}
```

Full URLs are accepted: only the host and port are used. Duplicates are checked once.

## Example output

A healthy certificate (real run):
```json
{
  "host": "github.com",
  "port": 443,
  "ok": true,
  "trusted": true,
  "error": null,
  "warnings": [],
  "subject": "github.com",
  "issuer": "Sectigo Limited",
  "issuerCommonName": "Sectigo Public Server Authentication CA DV E36",
  "validFrom": "2026-10-30T00:00:00+00:00",
  "validTo": "2027-01-27T23:59:59+00:00",
  "daysLeft": 75,
  "expired": false,
  "expiresSoon": false,
  "selfSigned": false,
  "altNames": ["github.com", "www.github.com"],
  "altNameCount": 2,
  "wildcard": false,
  "serialNumber": "3E1D6026B4B0AEA279DCA2EFBBCED82B",
  "signatureAlgorithm": "sha256",
  "trustError": null,
  "tlsVersion": "TLSv1.3",
  "cipher": "TLS_AES_128_GCM_SHA256"
}
```

A certificate served for the wrong host (shortened):
```json
{
  "host": "wrong.host.badssl.com",
  "ok": false,
  "trusted": false,
  "trustError": "Hostname mismatch, certificate is not valid for 'wrong.host.badssl.com'.",
  "warnings": ["not trusted: Hostname mismatch, certificate is not valid for 'wrong.host.badssl.com'."],
  "subject": "*.badssl.com",
  "daysLeft": 45
}
```

A host that cannot be reached has `error` set (for example a DNS failure or `TimeoutError`) and no certificate fields.

## Use cases

- **Expiry monitoring**: schedule the Actor daily and alert (Make, Zapier, n8n, webhooks, e-mail) when `ok` is false or `daysLeft` drops below your limit
- **Agencies and hosting providers**: one run for every client domain, exported as CSV or Excel
- **After a migration or CDN change**: check that every hostname (www, apex, subdomains) serves a certificate that actually covers it
- **Vendor and third-party checks**: issuer, expiry and TLS version of the services you depend on
- **Mail and other TLS services**: SMTPS 465, IMAPS 993, custom ports

## Integrations

Python:
```python
from apify_client import ApifyClient
client = ApifyClient("<YOUR_API_TOKEN>")
run = client.actor("extas_corp/ssl-certificate-checker").call(run_input={"domains": ["example.com"], "warnDays": 21})
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    if not item["ok"]:
        print(item["host"], item.get("daysLeft"), item["warnings"], item["error"])
```
Results can be exported as CSV, Excel or JSON from the dataset, or pushed to Google Sheets, Make, Zapier or n8n.

## Limits

- It checks the certificate the server presents to a standard client (SNI = the host you gave). It is not a full TLS security scan: no cipher suite enumeration, no protocol downgrade tests, no vulnerability checks.
- Trust is evaluated against the public CA bundle of the Actor's image. A private or corporate CA is reported as not trusted.
- Revocation (OCSP / CRL) is not checked.
- Servers that only speak TLS 1.0 / 1.1 are reported as an `error` (handshake refused), not as a certificate.
- STARTTLS ports (SMTP 25/587, IMAP 143) are not supported: only ports that speak TLS from the first byte.
- It sees the certificate from Apify's datacenter. A CDN may serve a different certificate in another region.

## FAQ

**Does it need a proxy or a browser?** No. One direct TLS handshake per host.

**Why is `ok` false although the site opens in my browser?** Most often the certificate expires within `warnDays` (see `expiresSoon`), or the server does not send its intermediate certificate: browsers can repair that, strict clients such as API clients and bots cannot. `trustError` gives the reason.

**Can I check an internal host?** Only hosts reachable from the public internet.

**Do I need to pay to try it?** The Apify Free plan includes monthly platform credit, enough to check thousands of hosts.
