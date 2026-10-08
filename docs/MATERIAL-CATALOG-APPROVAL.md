# Material Catalog Approval

CIRCULINK now separates material catalog governance from listing publication. Users can request a new material type at `/marketplace/material-types/new`. Requests are stored in `material_catalog` with `status=pending` and `enabled=false`.

Admins review requests at `/admin/material-types`. Approval sets `status=approved`, `enabled=true`, and assigns a stable `material:<slug>` identifier. Only approved material types (plus legacy catalog records without a status field) are exposed in the listing material dropdown.

This keeps user-created product/material types out of the public dropdown until an administrator explicitly approves them.
