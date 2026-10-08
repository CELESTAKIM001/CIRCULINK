# CIRCULINK database layer architecture

## Why the previous deployment failed

The MongoDB cluster was reachable. The application was marking the database as unavailable because startup index creation stopped on an existing `certificate_no_1` index whose `unique` option differed from the requested definition. `init_db()` then set the database handle to `None`, which made registration and sign-in return HTTP 503.

The new implementation reconciles indexes instead of blindly recreating them. It gives every important index an explicit name, reuses compatible legacy indexes, and replaces only an incompatible index definition. A single legacy index mismatch therefore cannot take the entire application offline.

## Data layers represented by the HTML prototype

The HTML prototype remains presentation code. Data-bearing and configurable factors are persisted in MongoDB through these layers:

- `users` and `accounts`: identity, role, account type, verification and account state.
- `listings`, `material_catalog`, `demand_posts`, `offers`, `deals`, `matches`: marketplace supply/demand and matching.
- `orders`, `transactions`, `payments`, `escrow`, `payouts`, `point_ledger`, `point_redemptions`: commercial and payment records.
- `pickups`, `fulfillments`, `batches`, `certificates`: collection, fulfilment, traceability and compliance.
- `media`: uploaded image metadata/content with the existing 12-hour unreferenced cleanup policy.
- `notifications`, `notification_preferences`, `otps`: communication and account security.
- `audit_logs`, `events`, `mpesa_callbacks`: operational history and provider reconciliation.
- `settings`, `plans`, `subscriptions`, `platform_revenue`, `contact_messages`, `mhub_events`: platform administration.
- `platform_layers`: database-backed page, navigation, workspace, workflow, feature and map-layer definitions represented by the prototype.
- `map_points`: GIS points for collection/drop-off/facility layers; active marketplace listings are added dynamically.
- `content_blocks`, `feature_flags`, `workflow_states`, `verification_requirements`: configurable platform behaviour and future admin controls.

Static CSS, SVG icon definitions and semantic HTML stay in source control because storing every DOM node in MongoDB would make the application slower and harder to maintain. User/business content, operational states, GIS points and configurable product rules are the database layer.

## Startup sequence

1. Read `MONGODB_URI` and `MONGODB_DB`.
2. Ping Atlas before doing writes.
3. Reconcile indexes idempotently.
4. Seed only missing/default platform layer documents with upserts.
5. Expose `/api/health` so deployment logs can verify the live database name and collection list.
6. Registration writes the user, account profile, account-created event and audit record before issuing the OTP.

## Required Vercel variables

`MONGODB_URI` must contain the Atlas connection string. `MONGODB_DB` must match the Atlas database used by the project; the current CIRCULINK Atlas screenshot shows `link`, so the example/default is `link`. Never commit the real URI or password.
