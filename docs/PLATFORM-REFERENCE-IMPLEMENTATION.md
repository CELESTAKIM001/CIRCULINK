# CIRCULINK platform reference implementation

This release turns the supplied Circulink platform HTML reference and pitch-deck framing into a Flask presentation/workspace layer backed by the existing MongoDB application.

## Implemented surfaces

- Overview: problem framing, live marketplace metrics and collection-to-compliance process.
- Marketplace: live listings, status, quantity, price and a live Leaflet map using stored coordinates.
- Household: pickup and recorded transaction entry points.
- Collector: live supply, batch and paid-transaction metrics plus operating flow.
- Buyer: live demand posts, orders and batch records.
- EPR compliance: recorded batch weight, configured target only when present, and batch trail.
- Payments: server-authoritative order, weigh confirmation, Daraja payout and receipt flow presentation.
- Messages: account-scoped conversation records and marketplace entry point.
- Verification: email, phone, account review, company registration, NEMA licence and payout state.
- Admin: live operational counts for administrator accounts.
- System: the supplied uniform design tokens, typography and responsive rules.

## Source fidelity

The implementation follows the supplied reference language and structure while replacing prototype-only sample records with database-backed records or explicit empty/configuration states. It does not silently invent live prices, weights, compliance targets, ratings, people or verification claims.

## Existing workflows preserved

The new workspace is a presentation/control surface over the existing Flask routes for marketplace listing, material demand, pickup scheduling, checkout, payments, receipts, certificates, wallet and administration. It does not bypass server-side authorization or payment logic.

## Deployment notes

- Flask remains the application framework.
- MongoDB remains the source of truth.
- Leaflet is served from the existing local vendor assets; OpenStreetMap tiles are used for the map background.
- EPR targets are read from the `settings` collection (`key=epr_target`) and are not fabricated when absent.
