# CIRCULINK Admin Design System

The admin/operations console follows the same CIRCULINK V3 visual language as the public marketplace and workspaces.

## Navigation

The operations console uses this fixed information architecture: Command Center, Users, Material Types, Listings, Payments, Material Requests, Finance & Revenue, Payouts & Points, Commission & Points, Certificates, Plans, Inbox, Notifications, M-Hub Feature, Settings, and Audit History.

Each item uses a Microsoft Fluent System Icon, never emoji or text-only `+`/check/cross symbols. The active item uses the CIRCULINK green tint and green leading accent.

## Visual rules

- Operations sidebar: deep CIRCULINK charcoal-green.
- Main canvas: alabaster `#F7F5EF`.
- Cards: surface `#FCFBF8`, 20–24px radius, subtle hairline border.
- Primary action: CIRCULINK green `#2E9E4F`.
- Critical/warning accent: sunrise orange `#FF7A1A`, used sparingly.
- Typography: Montserrat for headings/numbers; Inter for body/UI.
- Tables scroll horizontally inside their own container on small screens.
- Mobile navigation collapses to a two-column menu and then a single column below 480px.

## Map points

Marketplace map points remain data-driven. They come from valid listing `location.geo` records and administrator-managed `map_points`; the UI must not fabricate coordinates.
