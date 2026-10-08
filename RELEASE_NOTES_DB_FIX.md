# CIRCULINK database reliability upgrade

- Fixed MongoDB `IndexKeySpecsConflict` caused by legacy `certificate_no_1`.
- Added idempotent index reconciliation for existing Atlas databases.
- Added explicit index names and safe compatibility checks.
- Added missing indexes for orders, pickups, events, matches, plans, subscriptions and platform configuration.
- Added database-backed platform layers, map layers, content blocks, feature flags, workflow states and verification requirements.
- Moved map seed points from hardcoded API data into `map_points`.
- Added `/api/platform/layers` for enabled configuration layers.
- Added database name/collection visibility to `/api/health`.
- Registration now records `users`, `accounts`, an `ACCOUNT_CREATED` event and an audit record.
- Added the latest supplied HTML prototype under `docs/reference/Circulink_Platform.latest.html`.
