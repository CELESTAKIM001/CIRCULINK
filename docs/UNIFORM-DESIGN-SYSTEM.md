# CIRCULINK Uniform Design System

The supplied `Circulink_Platform.html` is the visual source of truth. The Flask application now loads `static/css/circulink-uniform.css` after the existing design layers so legacy and V3 routes share the same visual tokens.

## Core language
- Montserrat 600/700/800 for headings and metrics.
- Inter 400/500/600 for body and controls.
- Alabaster background `#F7F5EF`.
- Surface `#FCFBF8`.
- Charcoal `#262B2E`.
- Leaf green `#2E9E4F` and green tint `#E3F3E7`.
- Sunrise orange `#FF7A1A` is reserved for important actions/warnings.
- Blue and red are semantic status colors.
- 24px desktop cards, 18px mobile cards.
- Pill buttons and status chips.
- 44px controls.
- Tables scroll horizontally on small screens.
- Reduced-motion support is included.
- Dark theme tokens are included.

Business logic, Flask routes, MongoDB layers, Daraja integration, inventory/checkout controls, media cleanup, receipts and Vercel configuration are preserved from the database-layer release.
