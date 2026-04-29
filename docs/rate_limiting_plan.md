# Rate limiting plan (Step 37A scaffold)

Paid quotas belong to Step 38A. This milestone only documents boundaries for a future throttle layer without implementing Redis-heavy middleware yet.

## Current behavior (frozen)

| Surface | Enforcement today |
|---------|-------------------|
| Public routes (`/`, `/faq/`, `/about/`, `/pricing/`, `/contact/`) | Public; no quotas. |
| Product shell (`/analyze/`, `/dashboard/**`, authenticated APIs) | **Authentication gate** protects usage; anonymous clients receive login redirects / `authentication_required`. |
| Feedback (`POST /api/v1/feedback`) | Requires auth; payloads are allow-listed and minimized. Spam protection still backlog. |

## Future direction

1. **Analyze & presentation endpoints** — apply per-account limits first (trusted users), layered with IP-based anomalies for abuse bursts.
2. **Feedback endpoints** — add low-cost throttle (per user + per IP) even before monetization because spam wastes storage/time.
3. **Anonymous endpoints** — keep generous limits for informational pages but monitor abuse fingerprints (future WAF / CDN capabilities).
4. **Billing step (38A)** ties persistent quotas & plan upgrades to Stripe (or alternate PSP), not infra-only knobs.

Implementation backlog options (explicitly postponed here):

| Idea | Scope |
|------|-------|
| Redis-backed leaky bucket middleware | Larger dependency + ops footprint. |
| Cloudflare/AWS WAF quotas | Hosted reverse proxy responsibilities. |

Until then, Wisdomize intentionally relies on **auth gating**, **strict feedback schema**, safe logging posture, and read-only health checks for monitoring.
