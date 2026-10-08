# CIRCULINK Marketplace Settlement Upgrade

## Added
- Company-only marketplace checkout with explicit payment/receipt messaging.
- M-Pesa confirmation now places marketplace orders into `paid_awaiting_receipt`; participant payouts are not created at payment time.
- Company dashboard now shows marketplace orders and a **Materials received** action.
- Physical receipt confirmation triggers an idempotent settlement workflow.
- Per-line collector and individual contributor allocation.
- System commission plus collector/source and individual/contributor service fees.
- Collector and contributor payout queue records are created only after receipt confirmation.
- Admin **Marketplace Orders** workspace to assign collector and contributor per material line.
- Admin **Payouts & Points** workspace can assign verified points to individual contributors.
- Collector workspace at `/circular/collector-points` for assigning contributor points.
- Point assignments write to the point ledger, update the contributor wallet, and create an audit event.
- Clear marketplace/cart/checkout messaging explaining that physical receipt releases settlement.

## Settlement lifecycle
1. Company adds materials to cart.
2. Company checks out and pays with M-Pesa.
3. Payment is confirmed; order becomes `paid_awaiting_receipt`.
4. Admin may assign collector/contributor participants to each order line.
5. Company physically receives the materials and clicks **Materials received**.
6. CIRCULINK calculates system commission, participant shares and participant service fees.
7. Collector/contributor payouts are queued and platform revenue is recorded.
8. Order becomes `received` with `settlement_status=SETTLED`.

The settlement service is designed to be safely retried after a partial failure and to avoid creating duplicate line settlements.
