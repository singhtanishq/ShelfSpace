# ShelfSpace — Test Coverage Report

**Date:** 24 October 2026 (frontend audit)
**Environment:** macOS (arm64), Node 24, Python 3 venv, MySQL 8 (`book_shop` seed data)
**How it ran:** The FastAPI backend was started on `127.0.0.1:8001` and the Vite dev server on
`localhost:5175` (proxying `/api` and `/media` to the backend) — ports 8000/5173 were occupied by
an unrelated project, so `BACKEND_URL` was pointed at 8001. All testing was manual, black-box
browser automation (ZCode in-app browser, Playwright surface) plus the project's own automated
suites.

> **Manual vs automated:** the tables below distinguish **manual browser testing** (a real
> browser driving the running app) from **automated suites** (`vitest`, `tsc`, `vite build`).
> No end-to-end framework is configured in this repository; nothing in this report comes from
> one.

---

## 1. Automated checks

| Check | Command | Result |
| ----- | ------- | ------ |
| Frontend unit/component tests | `npm test` (vitest) | **14/14 passed** (13 pre-existing + 1 new guest-cart store test) |
| Type check + production build | `npm run build` (`tsc -b && vite build`) | **Passed** |
| Backend suite | `backend/.venv/bin/python -m pytest` | Not re-run in this audit (untouched backend); last known state per README: 90+ tests |

## 2. Route inventory (29 routes discovered)

Routes were derived from `frontend/src/App.tsx` and verified live.

| Route | Page | Access | Manual result |
| ----- | ---- | ------ | ------------- |
| `/` | Landing page | public | Pass |
| `/books` | Catalog + filters | public | Pass |
| `/books?category=…&min_rating=…` | Filtered catalog | public | Pass |
| `/books/:slug` | Book detail | public | Pass |
| `/about`, `/contact` | Static pages | public | Pass |
| `/cart` | Cart (server or guest) | public | Pass (after fix) |
| `/login`, `/register`, `/forgot-password`, `/reset-password` | Auth (guest-only) | public | Pass |
| `/verify-email` | Email verification | public | Pass (missing-token error state verified in code path; live link flows need `EMAIL_ENABLED`) |
| `*` | 404 page | public | Pass |
| `/checkout` | Checkout | customer | Pass |
| `/wishlist` | Wishlist | customer | Pass |
| `/account` | Profile | customer | Pass |
| `/account/orders` | Order history | customer | Pass |
| `/account/orders/:orderNumber` | Order detail | customer | Pass |
| `/account/addresses` | Address book | customer | Pass |
| `/account/reviews` | My reviews | customer | Pass |
| `/account/notifications` | Notifications | customer | Pass |
| `/account/security` | Password change | customer | Pass (error path) |
| `/admin` | Dashboard | admin | Pass |
| `/admin/books` | Catalog admin | admin | Pass |
| `/admin/inventory` | Stock admin | admin | Pass |
| `/admin/terms` | Taxonomy admin | admin | Pass |
| `/admin/orders` | Order list | admin | Pass |
| `/admin/orders/:orderNumber` | Order manage | admin | Pass |
| `/admin/returns` | Returns admin | admin | Pass |
| `/admin/users` | Users admin | admin | Pass (after fix) |
| `/admin/coupons` | Coupons admin | admin | Pass |
| `/admin/reviews` | Moderation | admin | Pass |
| `/admin/settings` | Store settings | admin | Pass (after fix) |
| `/admin/audit` | Audit log | admin | Pass |

Access control was verified by direct URL navigation: guests hitting `/checkout`, `/wishlist`,
`/account*` were redirected to `/login` (with a `from` state); a customer hitting `/admin/*` was
redirected to `/`; signed-in users visiting `/login` were redirected away.

## 3. Manual browser tests — storefront

| Scenario | Result | Notes |
| -------- | ------ | ----- |
| Guest add-to-cart from catalog & detail; badge updates | Pass | Guest cart persisted to localStorage |
| Guest cart page shows items, steppers, subtotal | Pass | **After fix** — previously "empty" |
| Guest steppers (increase/remove), live subtotal | Pass | |
| Guest → sign in: cart merges into server cart, lands back on `/cart` | Pass | **After fix** (destination previously lost) |
| Coupon WELCOME10 applied / invalid code rejected | Pass | Cap at ₹200 max observed and correct |
| Checkout: address preselection, card/UPI gating (short card number and malformed UPI disable Place order) | Pass | |
| COD order placed end-to-end | Pass | Success banner, tracking timeline, invoice button |
| Order cancellation (own pending order) | Pass | Confirm dialog, restock, refund toast |
| Return request within window (delivered order) | Pass | `RT-00002` created, admin decisions completed |
| Return request outside window | Correct rejection | Backend enforces the 14-day window; see UI audit §known-limitations |
| Verified-purchase review: edit flow | Pass | Seed review present for priya; edit submitted with same values |
| Wishlist add/remove; move-to-cart button present | Pass | |
| Notifications: mark read, mark all | Pass | |
| Profile update | Pass | Toast + persisted value |
| Security: wrong current password rejected | Pass | Error toast, no state change |
| Address add/delete (own account) | Pass | Modal + confirm dialog |
| Logout (incl. from protected pages) | Pass | **After fix** — lands on `/` |
| Search from header → results page | Pass | `requestSubmit` path used by automation; Enter key works in real browsers |
| Pagination on `/books` (4 pages) | Pass | |
| 404 page for unknown paths | Pass | |

## 4. Manual browser tests — admin

| Scenario | Result | Notes |
| -------- | ------ | ----- |
| Dashboard KPIs/charts (7/30/90/365-day ranges) | Pass | Revenue chart renders daily spikes (sparse order days) — data-correct |
| Order state machine: pending → confirmed → processing → shipped → out for delivery → delivered | Pass | Two orders advanced; timeline + badges updated each step |
| Terminal-state guard (cancelled order shows "no transitions") | Pass | |
| Books: create → edit price → archive | Pass | Unreferenced books are hard-deleted by the backend; dialog copy corrected to say so |
| Inventory: low-stock filter, +10 adjustment, movement ledger | Pass | Book left the low-stock filter after adjustment |
| Taxonomy: category create/delete | Pass | |
| Coupons: create/delete, enable/disable toggle | Pass | Seed coupons restored to active |
| Reviews: hide → hidden filter → unhide | Pass | Aggregates recalculated server-side |
| Returns: approve → complete | Pass | Refund recorded, restock applied |
| Settings page renders and saves | Pass | **After fix** — page previously crashed on load |
| Users page renders, search box present | Pass | **After fix** — page previously crashed on load |
| Audit log records admin actions | Pass | review.show / book.delete etc. observed |

## 5. Responsive checks (manual, per viewport)

Horizontal-overflow probe (`scrollWidth > clientWidth`) run on every key route:

- **1440×900** and **1280×800**: `/`, `/books`, `/books/:slug`, `/about`, `/contact`, `/cart`,
  `/login`, `/admin`, `/admin/orders`, `/admin/books` — **no overflow**.
- **768×1024**: `/`, `/books`, `/books/:slug`, `/cart`, `/login`, `/account`, `/admin`,
  `/admin/inventory` — **no overflow**. Filter sidebar collapses behind a "Filters" button;
  admin sidebar becomes a horizontal pill bar.
- **390×844**: `/`, `/books`, `/books/:slug`, `/cart`, `/login`, `/account`, `/admin`,
  `/admin/orders`, `/admin/settings`, `/admin/users` — **no overflow**. Mobile menu opens with
  search; book-card wishlist hearts are always visible on touch widths (fixed in this audit).

## 6. Console / network observations

- No failed asset requests on any public page (image fallback component handles missing covers).
- `401 /api/v1/cart` for guests on the cart page **before the fix**; eliminated by gating the
  query behind the auth token.
- No uncaught client exceptions after fixes (the two pre-existing admin crashes were the only
  ones observed).

## 7. Known limitations / not covered

- **Cover upload** (`/admin/books` file input) could not be exercised: the in-app browser
  environment does not support file choosers. Endpoint covered by backend tests instead.
- **Email delivery flows** (verification links, reset emails): `EMAIL_ENABLED=false` in the local
  environment; the register flow surfaces the verification URL inline instead. The reset-token
  page was reached only in its missing-token error state.
- **Real payments**: out of scope by design (mock gateway).
- **The 14-day return window** is enforced by the backend; the UI keeps the return button enabled
  for delivered orders regardless of delivery age because store settings are not exposed to the
  customer API. See `ui-audit.md`.
- Automated **end-to-end suite**: none exists in the repo; all browser checks above were manual.
