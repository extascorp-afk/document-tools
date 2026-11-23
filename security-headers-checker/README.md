# Security Headers Checker: Bulk HSTS, CSP, Cookie Flags & security.txt Grade

Paste a list of sites and get, for each one, an **A to F grade** for its HTTP security headers and a **list of what to fix**. It also reads the `security.txt` file (RFC 9116) that tells researchers how to report a vulnerability. One request per site, plus the security.txt lookup: it reads only what the server sends to any browser.

- **Headers graded**: `Strict-Transport-Security` (max-age, includeSubDomains), `Content-Security-Policy` (missing, `'unsafe-inline'` without nonce/hash, `'unsafe-eval'`, wildcard sources), clickjacking protection (`X-Frame-Options` or CSP `frame-ancestors`), `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, `Cross-Origin-Opener-Policy`.
- **Information leaks**: `Server` with a version number, `X-Powered-By`, `X-AspNet-Version`.
- **Cookie flags**: every `Set-Cookie` of the response is checked for `Secure`, `HttpOnly`, `SameSite`.
- **security.txt**: looks in `/.well-known/security.txt` then `/security.txt`; reports Contact, Expires, Policy, and problems (no Contact, no Expires, expired, bad date).
- Redirects are followed and the **final** page is graded (`http://` and `www` variants end up where a visitor ends up).
- Findings have a severity (`high`, `medium`, `low`) and a plain message.
- Errors are reported per URL, they never stop the run.
- **Safe by design**: URLs that resolve to private, local or link-local addresses are refused (also after a redirect).
- **Free during launch**: no per-URL fee at the moment, you only pay Apify platform usage (covered by the Free plan's monthly credit for normal use).

## Input example

```json
{
  "urls": ["github.com", "example.com", "https://www.mozilla.org"],
  "checkSecurityTxt": true
}
```

A bare domain is checked over HTTPS. Duplicates are checked once.

## Example output

`example.com` (real run):
```json
{
  "url": "https://example.com",
  "finalUrl": "https://example.com",
  "status": 200,
  "grade": "F",
  "score": 0,
  "error": null,
  "findings": [
    {"severity": "high", "header": "strict-transport-security", "message": "missing: browsers may be downgraded to HTTP"},
    {"severity": "high", "header": "content-security-policy", "message": "missing: no browser-side defence against script injection"},
    {"severity": "medium", "header": "x-frame-options", "message": "no clickjacking protection (X-Frame-Options or CSP frame-ancestors)"},
    {"severity": "medium", "header": "x-content-type-options", "message": "missing or not \"nosniff\""}
  ],
  "headers": {"server": "cloudflare"},
  "securityTxt": {"found": false}
}
```
(findings shortened here: the real row also lists `referrer-policy`, `permissions-policy` and `cross-origin-opener-policy`.)

`github.com` (real run) scores 80, grade B: HSTS and CSP are present, the findings are `permissions-policy` and `cross-origin-opener-policy` missing, and one cookie without `HttpOnly`; its `securityTxt.found` is `true`.

## How the grade works

The score starts at 0 and adds points for each good header: HSTS 20 (10 if max-age is under 6 months), CSP 25 (minus points for `'unsafe-inline'` without nonce/hash or a wildcard source), clickjacking protection 15, `nosniff` 10, `Referrer-Policy` 10, `Permissions-Policy` 10, `Cross-Origin-Opener-Policy` 10. Grades: A from 85, B from 70, C from 50, D from 30, F below. A site with any `high` finding cannot be better than C. Cookie flags and version leaks are reported as findings but do not change the score.

## Pricing

**Free during launch**: no per-URL fee, only Apify platform usage. A price per checked URL may be introduced later, with advance notice.

## Limits

- It grades the headers of **one response** (the page you give, after redirects). Other pages or API routes of the same site can send different headers.
- The grade is a **checklist of well-known headers, not a security audit**. A good grade does not mean a site is secure, and a poor one does not mean it is vulnerable.
- It does not execute JavaScript, so headers added by a browser-only layer are not seen. Sites that block automated clients (Cloudflare challenge, 403) are reported with their HTTP status and the headers of that block page.
- The CSP check is a set of simple rules (missing, `'unsafe-inline'`, `'unsafe-eval'`, wildcards). It does not evaluate a full policy.
- Only `Set-Cookie` headers of that single response are checked; cookies set later by scripts are not.
- `Expires` in security.txt is compared with today's date; signed (PGP) files are read as plain text, the signature is not verified.
- It sends normal GET requests with a clear User-Agent. Only check sites you are allowed to look at; it does not probe, scan ports or test for vulnerabilities.
