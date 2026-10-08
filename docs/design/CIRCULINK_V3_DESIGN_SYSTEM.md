# CIRCULINK V3 Design System

This release applies the supplied `Circulink_Platform.html` visual direction across the Flask/Jinja website without replacing existing business logic.

## Tokens

- Alabaster background: `#F7F5EF`
- Card surface: `#FCFBF8`
- Sand: `#EFEBE1`
- Sunken: `#F1EEE5`
- Charcoal: `#262B2E`
- Muted: `#5C6468`
- Faint: `#8A9290`
- Leaf green: `#2E9E4F`
- Green ink: `#1F7A3A`
- Green tint: `#E3F3E7`
- Sunrise orange: `#FF7A1A`
- Orange ink: `#B34C00`
- Orange tint: `#FFE8D4`
- Info blue: `#2F6FA8`
- Error red: `#C0372C`

Dark-mode tokens follow the supplied prototype. Device preference is respected by default and the header switch stores an explicit user choice in local storage.

## Layout

- 248px desktop navigation rail.
- Sticky topbar with search, theme control and account actions.
- Rail becomes a slide-in drawer below 1000px.
- 32px desktop content margin and 16px mobile margin.
- 24px card gaps and 24px card padding, reduced on phones.
- No intentional horizontal page scrolling at 400px.

## Components

All major existing CIRCULINK templates inherit the same token layer: buttons, forms, cards, notices, marketplace listings, dashboards, admin panels, tables, map containers and receipt verification views.

Orange is intentionally limited to critical focus/warning emphasis. Green is structural and primary. Icons use the existing SVG line-icon set; emoji UI is not introduced.

## Data rule

This visual release does not add fabricated marketplace records. Marketplace, order, payment, certificate, notification and account values continue to come from the application's database/context. Static copy is product guidance, not simulated transaction data.

## Accessibility

- Visible keyboard focus uses a 3px orange ring.
- Interactive controls retain labels and accessible names.
- Reduced motion disables transitions/animation.
- Light and dark themes use the specified contrast-oriented palette.
