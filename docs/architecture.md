# ShelfSpace architecture

A modular monolith with clean boundaries: a FastAPI backend (service-oriented), a MySQL database,
and a React SPA. No microservices, no message broker — professional simplicity.

```text
┌──────────────────────┐        ┌───────────────────────────────┐        ┌─────────┐
│  React SPA (Vite)    │  HTTP  │  FastAPI                      │  SQL   │  MySQL  │
│  TanStack Query      │ ─────► │  routes → services → models   │ ─────► │  8.x    │
│  Zustand (auth/cart) │        │  (pydantic validation)        │        │         │
└──────────────────────┘        └───────────────┬───────────────┘        └─────────┘
                                                │
                                        ┌───────▼────────┐
                                        │ email outbox   │  (worker thread,
                                        │ media/invoices │   own DB session)
                                        └────────────────┘
```

## Backend layering

```
route (api/v1)        → parse/validate request (pydantic), auth via dependencies
service (services/)   → business rules, transactions, cross-model coordination
model (models/)       → SQLAlchemy ORM, the single source of schema truth
```

Routes never contain business logic; services never parse HTTP. `get_db` opens one session per
request and commits at the end, so a whole request (including checkout) is a single transaction.

## Key flows

### Checkout (transactional, oversell-proof)

1. `order_service.checkout()` loads the user's cart.
2. Inventory rows for all cart items are locked with `SELECT … FOR UPDATE`.
3. Every line is re-validated against live stock (the cart UI values are never trusted).
4. Totals (discounts via coupon validation, shipping, tax) are computed server-side.
5. Non-COD payments authorize through the `PaymentGateway` abstraction (mock implementation).
6. Order, items (with catalog snapshots), payment row, status history and inventory ledger
   entries are written; stock is decremented; coupon usage counted; cart emptied.
7. Everything commits atomically — a failure anywhere leaves no half-written data.
8. Order-confirmation email is queued in the same transaction and delivered by the worker.

### Order state machine

`pending → confirmed → processing → shipped → out_for_delivery → delivered`, with `cancelled`
reachable from the first three stages and `returned` from `delivered` (via a completed return).
`ALLOWED_STATUS_TRANSITIONS` in `app/models/order.py` is the single authority; invalid jumps
return `422`. Side effects per transition:

- **cancelled** → restock every item, refund mock payments, notify
- **delivered** → record `delivered_at`, capture COD payments, notify

### Returns & replacements

Eligibility = order delivered + inside the configurable window (`return_window_days` setting)
+ no other open request + per-item quantity remaining. Decisions:

- **approve** — returns: refund initiated; replacements: queued for dispatch
- **reject** — frees the order for a new request
- **complete** — returns restock items and settle the refund (order becomes `returned` only when
  every unit is back); replacements decrement stock for the new copies

### Email outbox

`email_service.queue_email()` persists an `email_logs` row (status `queued`) inside the business
transaction. A daemon worker sends queued rows via SMTP with HTML + text templates and records
`sent`/`failed`/`skipped`. With `EMAIL_ENABLED=false` nothing leaves the machine but the whole
pipeline stays observable. The same pattern (outbox + worker) is the extension point for SMS/push.

## Database design (26 tables)

- **Identity**: `users`, `user_refresh_tokens`, `addresses`
- **Catalog**: `books`, `authors`, `publishers`, `categories`, `book_authors`, `book_categories`
- **Inventory**: `inventories` (stock + reserved + threshold), `inventory_transactions` (ledger)
- **Commerce**: `carts`, `cart_items`, `wishlist_items`, `coupons`, `orders`, `order_items`,
  `order_status_history`, `payments`
- **Post-purchase**: `return_requests`, `return_items`, `reviews`
- **Platform**: `notifications`, `email_logs`, `audit_logs`, `store_settings`

Design choices worth knowing:

- Orders snapshot **shipping address** and **item titles/authors/prices** at purchase time, so
  address edits or catalog changes never corrupt history.
- `books` caches `rating_avg`, `rating_count` and `sales_count`, maintained by the review and
  order services — no expensive aggregates on the hot catalog path.
- Cancellations and returns never delete rows; they append ledger entries and status history.
- Books and users **archive/deactivate** instead of hard-deleting when referenced by orders.

## Frontend architecture

- **Server state** — TanStack Query (keys per domain, invalidation after mutations)
- **Client state** — Zustand stores: `auth` (access token in memory, refresh token in
  localStorage, session restore on reload) and `guestCart` (localStorage, merged into the server
  cart at sign-in)
- **Routing** — react-router with lazy routes; `RequireAuth`/`RequireAdmin`/`GuestOnly` guards
- **Design system** — small Tailwind component set (Button/Input/Modal/Badge/Table/states) used
  consistently across storefront and admin; responsive down to mobile
- **API layer** — axios instance with a 401 → refresh → retry interceptor; typed endpoint modules

## Security model

- BCrypt(12) password hashing; JWT HS256 access tokens; hashed, rotating refresh tokens
- RBAC via FastAPI dependencies; ownership checks return 404 (no enumeration)
- Rate limiting on login/forgot-password/reset endpoints (in-process sliding window)
- File uploads: MIME allow-list + Pillow decode + UUID names + size cap
- Central exception handlers → uniform error envelope; stack traces stay in the server log
