
## Platform reference implementation
- Added `/platform/` as the unified CIRCULINK workspace.
- Implemented live overview, marketplace/map, household, collector, buyer, EPR, payments, messages, verification, admin and system views.
- Reused existing server-side workflows instead of creating prototype-only payment or inventory state.
- Replaced sample-data presentation with MongoDB-backed records and explicit empty/configuration states.
- Added implementation documentation in `docs/PLATFORM-REFERENCE-IMPLEMENTATION.md`.

# CIRCULINK — Vercel-ready upgrade release

This release preserves the existing CIRCULINK Flask/Python + MongoDB + Daraja application and applies additive upgrades rather than replacing the working platform.

## Included
- Existing marketplace, dashboards, admin, payments, receipts, certificates, circular operations, pickup and M-Pesa reconciliation modules preserved.
- Sample HTML design retained as `docs/reference/Circulink_Platform.original.html` and used as the visual reference for the upgrade.
- Server-authoritative checkout: browser-submitted price/total is ignored; current MongoDB listing price and stock are used.
- MongoDB transaction protects stock/order creation; sold-out listings are marked `sold_out`.
- MongoDB 2dsphere index support for listing coordinates.
- OTP hardening: hashed OTP storage, expiry, attempt limit and IP resend throttling.
- Secure session-cookie defaults and additional HTTP security headers.
- Hourly Vercel cron for safe cleanup of unreferenced media older than 12 hours.
- Vercel deployment environment template and production checklist.
- Original source ZIP retained under `archives/` strictly as rollback reference; it is not required by the application.

## Do not upload secrets
The release contains no production `.env` file. Set secrets in Vercel Project Settings > Environment Variables.

## Before live money
Configure MongoDB Atlas, production Daraja credentials, registered HTTPS callback URLs, Safaricom approval, transactional email, domain DNS/authentication, CRON_SECRET, and any required legal/payment-service arrangements.

## CIRCULINK V3 visual rebuild

- Re-skinned the entire Flask/Jinja web surface around the supplied `Circulink_Platform.html` visual system.
- Added the 248px desktop rail and responsive slide-in navigation.
- Added alabaster/light and device-aware dark themes with a manual switch.
- Centralized V3 colour, typography, radius, spacing, focus and surface tokens.
- Applied the V3 system to public, marketplace, account, dashboard, admin, request, payment, table and verification surfaces through the shared base template and final override layer.
- Preserved existing Flask routes, MongoDB data flows, Daraja/M-Pesa services, receipts, certificates, maps, notifications and inventory logic.
- No fabricated marketplace transaction records were added.
- Added `docs/design/CIRCULINK_V3_DESIGN_SYSTEM.md`.

The supplied product prompt mentions Node.js, but this release deliberately keeps the already-working Flask/Python application architecture so the deployment and payment stack are not replaced while the visual system is rebuilt.
