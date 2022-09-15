# ShelfSpace

**A modern, production-grade bookstore management & commerce platform.**

ShelfSpace is a full-stack web application for running a real bookstore: a polished customer
storefront (browsing, search, cart, checkout, order tracking, returns and reviews) backed by a
serious admin platform (analytics dashboard, catalog & inventory management, order fulfilment,
return decisions, coupons, users, audit trail).

It began life as a terminal-based Python/MySQL school project and has been completely rebuilt as a
professional web product — the original business rules (order windows, return/replacement
policies, email notifications, PDF invoices) were preserved and massively expanded.

![ShelfSpace storefront — landing page](docs/screenshots/01-overview/home-desktop.png)

*Every screenshot captured during the frontend audit is embedded individually in the
[visual showcase](#visual-showcase) below; [docs/screenshot-index.md](docs/screenshot-index.md)
holds the same collection as a per-image index.*

---

## Contents

1. [Feature highlights](#feature-highlights)
2. [Features in detail](#features-in-detail)
3. [Visual showcase](#visual-showcase)
4. [Route reference](#route-reference)
5. [Tech stack](#tech-stack)
6. [Architecture and project structure](#architecture-and-project-structure)
7. [Getting started](#getting-started)
8. [Available scripts](#available-scripts)
9. [Environment variables](#environment-variables)
10. [User workflows](#user-workflows)
11. [Responsive design](#responsive-design)
12. [Testing and quality checks](#testing-and-quality-checks)
13. [Known limitations](#known-limitations)
14. [Future improvements](#future-improvements)
15. [Development notes](#development-notes)
16. [License and documentation](#license-and-documentation)

---

## Feature highlights

### Storefront (customers)

- **Discovery** — landing page with featured books, best sellers and new arrivals; category and
  author browsing; full-text search across title, author, ISBN, publisher and description
- **Filters & sorting** — category, author, price range, rating, availability; sort by popularity,
  newest, price, rating or title; pagination
- **Book pages** — rich detail view with cover, metadata, stock status, related books and reviews
- **Cart** — server-backed cart with live stock validation, coupon codes, and a **guest cart kept
  in localStorage that merges into your account at sign-in** (reviewable in the cart page before
  you sign in)
- **Wishlist** — save books, move them to the cart later
- **Checkout** — saved address book, COD / mock card / mock UPI payments, order notes, coupons
- **Orders** — order history, six-step live status timeline, cancellation with restock & refund,
  **PDF invoice download**
- **Returns & replacements** — self-service requests within the configurable return window, with
  full status tracking and admin decisions
- **Reviews** — verified-purchase-only ratings that feed aggregate book scores
- **Account** — profile, addresses, notification centre, password change, my reviews
- **Notifications** — in-app notification centre for every order and return event

### Admin platform

- **Dashboard** — revenue/orders/customers KPIs, revenue & orders time series, top sellers,
  status distribution, customer growth, low-stock alerts; 7/30/90/365-day filters
- **Catalog management** — books (with cover upload), categories, authors, publishers; archive
  protection for anything referenced by orders
- **Inventory** — per-book stock with reserved quantities, low-stock/out-of-stock views, manual
  adjustments and a complete movement ledger
- **Orders** — searchable order list, detail view with a validated status state machine
  (`pending → confirmed → processing → shipped → out for delivery → delivered`), cancellation
  with automatic restock & refund, COD capture on delivery
- **Returns** — approve / reject / complete decisions; completed returns restock and settle
  refunds; completed replacements ship new copies
- **Users** — role management (customer/admin), deactivation, order/spend stats
- **Coupons** — percent or fixed discounts with minimums, caps, usage limits and expiry
- **Review moderation** — hide/show reviews (aggregates update automatically)
- **Settings** — store name, support email, tax, shipping, free-shipping threshold, return window
- **Audit log** — every administrative action recorded

### Platform

- JWT access tokens with rotating, revocable refresh tokens; email verification & password reset
- BCrypt password hashing, parameterized ORM queries, RBAC, rate-limited auth endpoints
- Transactional checkout with row-locked inventory (no overselling)
- Email service with an outbox worker, HTML + plain-text templates, and delivery logging
- REST API under `/api/v1` with interactive OpenAPI docs at `/docs`
- 91 backend tests, typed frontend with a Vitest suite, Docker-based one-command setup

---

## Features in detail

### Guest cart → account merge

Anonymous visitors add books to a localStorage-backed cart (visible in the header badge and in
`/cart` with an estimated subtotal). Signing in — from any entry point, including the cart page's
"Sign in to check out" — merges the guest items into the server-side cart and returns the user to
where they started. Quantities are combined and stock is re-validated server-side (screenshots
3.1–3.4 below).

### Checkout

Checkout preselects the default address, validates demo payment inputs client-side (12+ digit
card, `name@bank` UPI), and posts to a **transactional** backend endpoint: inventory rows are
locked, stock re-validated, totals recomputed, and the order written atomically. The result page
shows a success banner and the tracking timeline (screenshot 3.3–3.4).

### Order lifecycle

Both sides see the same six-step timeline. The admin "Manage status" panel only offers valid
transitions; customers can cancel while the order is `pending → processing` and request a
return/replacement while it is `delivered`. Every transition is recorded in the order history and
triggers an in-app notification (plus an email when `EMAIL_ENABLED=true`) (screenshots 3.5–3.6 and
5.3).

### Inventory ledger

Every stock change (order, cancellation, return, manual adjustment) writes a movement row with the
delta, reason and resulting balance — visible per book from the admin inventory table
(screenshot 5.5).

### Dashboard analytics

The dashboard aggregates revenue, orders, customers and inventory value over selectable windows,
plus top sellers, order-status mix and customer growth. Seed data spans a full year so every
range is meaningful (screenshot 5.1).

---

## Visual showcase

All 41 screenshots captured from the real running application (Vite dev server + FastAPI backend
with MySQL seed data) are embedded below, one per heading. Desktop captures are 1440×900, tablet
768×1024, mobile 390×844.

## 1. Storefront overview

### 1.1 Home page — desktop

The storefront hero with the "Browse the shelves" call to action, a guest cart badge in the
header, the trust-perk strip (free delivery, genuine copies, 14-day returns, curated shelves) and
the start of the category chip row.

![Home page — desktop](docs/screenshots/01-overview/home-desktop.png)

### 1.2 Home page — full page

Full-page capture of the landing page: hero, perks, category chips, and the featured rail with
discount badges (−10% on *Project Hail Mary*, −20% on *Sapiens* and *Dune*) followed by the
best-seller rail.

![Home page — full page](docs/screenshots/01-overview/home-desktop-full.png)

### 1.3 Home page — mobile

At 390px the landing page stacks into a single column with the hamburger menu and cart icon in the
header and the four trust perks arranged two per row.

![Home page — mobile](docs/screenshots/01-overview/home-mobile.png)

### 1.4 Mobile navigation — open

The open mobile menu drawer: search field, primary navigation links, and — when signed in — the
"My account" shortcut and sign-out action, as captured here.

![Mobile navigation — open](docs/screenshots/01-overview/home-mobile-menu-open.png)

## 2. Browsing the catalog

### 2.1 Catalog — desktop

The browsable catalog with 40 seeded titles, the filter sidebar (category list, author finder
with its own search, price range), the "Most popular" sort dropdown, and cards carrying star
ratings, struck-through original prices and discount badges.

![Catalog — desktop](docs/screenshots/02-storefront/catalog-desktop.png)

### 2.2 Book detail — desktop

The detail page for *Dune*: breadcrumb, −20% savings badge, live stock messaging, quantity
stepper, add-to-cart and wishlist actions, delivery assurances, the publisher/ISBN/pages/language
metadata table and the book description.

![Book detail — desktop](docs/screenshots/02-storefront/book-detail-desktop.png)

## 3. Cart, checkout & orders

### 3.1 Guest cart

An anonymous visitor's cart, stored on the device: two line items with quantity steppers, an
estimated subtotal of ₹748, and the "Sign in to check out" call to action that merges these items
into the account at sign-in.

![Guest cart](docs/screenshots/02-storefront/cart-guest-desktop.png)

### 3.2 Cart with coupon applied

The signed-in server cart with six items, WELCOME10 applied (−₹200 — the coupon's maximum
discount cap), free shipping above the configured threshold, and a total of ₹2,045 with the
"Proceed to checkout" action.

![Cart with coupon applied](docs/screenshots/02-storefront/cart-desktop.png)

### 3.3 Checkout

The checkout form: saved-address radio cards (Home selected, Office available) with inline edit
and a new-address option, the three payment methods (cash on delivery selected, demo card and
demo UPI), order notes, and the sticky order summary recomputing subtotal, coupon, shipping and
total.

![Checkout](docs/screenshots/02-storefront/checkout-desktop.png)

### 3.4 Order confirmation & tracking

The order detail page immediately after placing order `SS-20261024-00027`: success banner, pending
status badges, step 1 of the six-step tracking timeline highlighted, line items with an invoice
button, the delivery address, and the cancellation action still available.

![Order confirmation and tracking](docs/screenshots/02-storefront/order-confirmation-desktop.png)

### 3.5 Order history

The customer's order history with the "All orders" status filter, cover thumbnails per order and
status badges distinguishing pending, cancelled, delivered/paid and confirmed orders.

![Order history](docs/screenshots/02-storefront/account-orders-desktop.png)

### 3.6 Delivered order — tracking & returns

A delivered order: all six tracking steps reached ("Delivered on 23 Oct 2026"), the WELCOME10
discount reflected in the totals, a "Rate & review" shortcut on the item, and the
cancellation/return actions now disabled because the order is no longer eligible.

![Delivered order with completed timeline](docs/screenshots/02-storefront/order-detail-tracking-desktop.png)

## 4. Account management

### 4.1 Wishlist

Saved books (*Educated*, *Project Hail Mary*) with their prices and the "Move to cart" and
"Remove" actions for each entry.

![Wishlist](docs/screenshots/02-storefront/wishlist-desktop.png)

### 4.2 Address book

Two saved address cards — Home (marked Default) and Office — with edit/delete controls and the
"Add address" action.

![Address book](docs/screenshots/02-storefront/account-addresses-desktop.png)

### 4.3 Notifications

The in-app notification centre showing unread entries with accent borders (order placed, return
submitted/approved/completed, delivery updates), each with a per-item "Mark read" control plus
"Mark all as read".

![Notification centre](docs/screenshots/02-storefront/account-notifications-desktop.png)

### 4.4 Profile

The profile form with the editable full name and phone fields, the disabled email and username
fields (changes require contacting support), and the save action.

![Profile details](docs/screenshots/02-storefront/account-profile-desktop.png)

### 4.5 Security — password change

The change-password form with current, new and confirmation fields and the minimum-8-characters
hint.

![Security — password change](docs/screenshots/02-storefront/account-security-desktop.png)

### 4.6 My reviews

Reviews written by the signed-in customer, each with star rating, date, content and a delete
action.

![My reviews](docs/screenshots/02-storefront/account-my-reviews-desktop.png)

## 5. Admin platform

### 5.1 Dashboard

The analytics dashboard over a 365-day window: revenue ₹18,898.85 across 20 orders, 7 customers,
₹11,60,593 inventory value, the pending-orders/returns/low-stock alert strip, revenue and orders
time-series charts, and the top-selling books table led by *The Midnight Library*.

![Admin dashboard](docs/screenshots/03-admin/admin-dashboard-desktop.png)

### 5.2 Orders

The admin order list — 25 orders searchable by order number and filterable by status, with
payment method and payment-state badges (COD/UPI/card, paid/pending/refunded), fulfilment status
badges and a "Manage" action per row.

![Admin orders](docs/screenshots/03-admin/admin-orders-desktop.png)

### 5.3 Order management

The admin manage page for a delivered order, rendering the customer view — full tracking timeline,
line items with the WELCOME10 discount, delivery address and the completed return request
RT-00002 with its ₹399 refund — alongside the status-management controls further down the page.

![Admin order management](docs/screenshots/03-admin/admin-order-manage-desktop.png)

### 5.4 Books

The catalog management table: cover thumbnails, effective and original prices, stock counts,
ratings, Active/Featured badges, and View/Edit/Archive actions, with catalog search and the
"Add book" action in the header.

![Admin books](docs/screenshots/03-admin/admin-books-desktop.png)

### 5.5 Inventory

The stock table with per-book stock, reserved and available quantities, health badges, and the
History/Adjust actions that open the movement ledger and adjustment dialog.

![Admin inventory](docs/screenshots/03-admin/admin-inventory-desktop.png)

### 5.6 Taxonomy

The categories manager (switchable to authors and publishers) listing the nine seeded categories
with their descriptions and Edit/Delete actions.

![Admin taxonomy](docs/screenshots/03-admin/admin-terms-desktop.png)

### 5.7 Users

The user table — 8 registered accounts with avatar initials, inline role selectors
(customer/admin), order counts, lifetime spend, active/unverified status badges and
deactivate/reactivate actions.

![Admin users](docs/screenshots/03-admin/admin-users-desktop.png)

### 5.8 Coupons

The coupon manager showing the three seeded codes (WELCOME10 with its ₹200 cap and current usage
of 3, BOOKLOVER25, BIGSHELF15) with minimum-order amounts, usage counters, expiry dates and
Disable/Delete actions.

![Admin coupons](docs/screenshots/03-admin/admin-coupons-desktop.png)

### 5.9 Reviews

Review moderation: verified-purchase reviews with star ratings, reviewer and book references, and
Hide/Unhide controls, filterable to visible or hidden reviews only.

![Admin reviews](docs/screenshots/03-admin/admin-reviews-desktop.png)

### 5.10 Returns

The returns & replacements queue with type and status filters — both captured requests (RT-00002
"Corner bumped in transit" ₹399, RT-00001 "Finished reading early" ₹299) are completed with
refunds settled.

![Admin returns](docs/screenshots/03-admin/admin-returns-desktop.png)

### 5.11 Settings

Store settings in two cards: general identity (store name, support email, currency) and the
commerce rules — tax percent, shipping fee, free-shipping threshold, the 14-day return window and
the default low-stock threshold — each with explanatory hints.

![Admin settings](docs/screenshots/03-admin/admin-settings-desktop.png)

### 5.12 Audit log

The audit trail recording every administrative action with timestamp, actor, action type, entity
and JSON detail — including the book create/update/delete, category create/delete, return
decisions and order status transitions made during the audit session itself.

![Admin audit log](docs/screenshots/03-admin/admin-audit-desktop.png)

## 6. Authentication

### 6.1 Sign in

The centered sign-in card accepting email or username, with the forgot-password link and the
route to account creation.

![Sign in](docs/screenshots/04-auth/login-desktop.png)

### 6.2 Sign in — validation errors

Submitting the empty form surfaces inline red validation messages under both fields before any
request is made (client-side Zod validation).

![Sign in validation errors](docs/screenshots/04-auth/login-validation-error.png)

### 6.3 Registration

The account creation form with full name, username, email and password fields, the
minimum-8-characters hint and the link back to sign in.

![Registration](docs/screenshots/04-auth/register-desktop.png)

### 6.4 Password reset — request sent

The confirmation state after requesting a reset link: a privacy-safe message ("If an account
exists for **priya@example.com**…") noting the one-hour link expiry.

![Password reset sent](docs/screenshots/04-auth/forgot-password-sent.png)

## 7. Responsive design

### 7.1 Home — tablet

The landing page at 768px: the hero spans the width while the trust perks reflow to a 2×2 grid.

![Home — tablet](docs/screenshots/05-responsive/home-tablet.png)

### 7.2 Catalog — tablet

At 768px the catalog grid reflows to three columns and the filter sidebar collapses behind the
"Filters" button beside the sort dropdown.

![Catalog — tablet](docs/screenshots/05-responsive/catalog-tablet.png)

### 7.3 Catalog — mobile

At 390px the catalog shows a two-column card grid; the wishlist heart on every card is always
visible on touch widths (hover-reveal applies only on desktop).

![Catalog — mobile](docs/screenshots/05-responsive/catalog-mobile.png)

### 7.4 Book detail — mobile

The book page stacks cover, category chip, title and author vertically with full-width content.

![Book detail — mobile](docs/screenshots/05-responsive/book-detail-mobile.png)

### 7.5 Checkout — mobile

Checkout forms stack full-width on mobile with the payment method cards and order summary
following below the address selection.

![Checkout — mobile](docs/screenshots/05-responsive/checkout-mobile.png)

### 7.6 Admin dashboard — tablet

Below 1024px the admin sidebar becomes a horizontal scrollable pill bar and the KPI cards reflow
to two per row.

![Admin dashboard — tablet](docs/screenshots/05-responsive/admin-dashboard-tablet.png)

### 7.7 Admin dashboard — mobile

At 390px the admin dashboard keeps the pill navigation and two-column KPI grid with charts
rendering full-width.

![Admin dashboard — mobile](docs/screenshots/05-responsive/admin-dashboard-mobile.png)

---

## Route reference

29 routes declared in `frontend/src/App.tsx`. All admin routes are additionally guarded
server-side (a customer calling the admin API receives `403`).

| Route | Page | Access |
| ----- | ---- | ------ |
| `/` | Landing page | public |
| `/books` | Catalog (`?q= &category= &author= &min_price= &max_price= &min_rating= &in_stock= &sort= &page=`) | public |
| `/books/:slug` | Book detail | public |
| `/about`, `/contact` | Static pages | public |
| `/cart` | Cart (server cart when signed in, guest cart otherwise) | public |
| `/login`, `/register` | Auth (guest-only) | public |
| `/forgot-password`, `/reset-password?token=` | Password reset (guest-only) | public |
| `/verify-email?token=` | Email verification | public |
| `/checkout` | Checkout | customer |
| `/wishlist` | Wishlist | customer |
| `/account` | Profile | customer |
| `/account/orders` | Order history | customer |
| `/account/orders/:orderNumber` | Order detail | customer |
| `/account/addresses` | Address book | customer |
| `/account/reviews` | My reviews | customer |
| `/account/notifications` | Notifications | customer |
| `/account/security` | Password change | customer |
| `/admin` | Dashboard | admin |
| `/admin/books` | Catalog management | admin |
| `/admin/inventory` | Stock management | admin |
| `/admin/terms` | Categories / authors / publishers | admin |
| `/admin/orders` | Order list | admin |
| `/admin/orders/:orderNumber` | Order manage (status machine) | admin |
| `/admin/returns` | Return decisions | admin |
| `/admin/users` | User management | admin |
| `/admin/coupons` | Coupon management | admin |
| `/admin/reviews` | Review moderation | admin |
| `/admin/settings` | Store settings | admin |
| `/admin/audit` | Audit log | admin |
| `*` | 404 | public |

---

## Tech stack

| Layer | Technology |
| ----- | ---------- |
| Backend | Python 3.9+, FastAPI 0.115, Pydantic 2.10, SQLAlchemy 2.0, Alembic 1.14 |
| Database | MySQL 8 (SQLite for the test-suite) |
| Auth | JWT (PyJWT 2.10), BCrypt 4.2, refresh-token rotation |
| Email | SMTP via a queue worker, Jinja2 templates |
| Invoices | fpdf2 |
| Frontend | React 18, TypeScript 5.7, Vite 6, Tailwind CSS 3.4, TanStack Query 5, Zustand 5, React Router 7 |
| Forms | react-hook-form + Zod |
| Charts | Recharts 2.15 |
| Testing | pytest ×91 (backend), Vitest + Testing Library ×14 (frontend) |
| Infra | Docker Compose (MySQL + API + web/nginx) |

---

## Architecture and project structure

A modular monolith: React SPA ↔ FastAPI (routes → services → models) ↔ MySQL, with an in-process
email outbox worker and a media directory for covers and generated invoices.

```mermaid
flowchart TD
    A[React SPA - Vite dev server / nginx] -->|/api /media proxy| B[FastAPI routes - api/v1]
    B --> C[Pydantic schemas + RBAC deps]
    C --> D[Services - orders, returns, inventory, catalog, email]
    D --> E[(MySQL 8)]
    D --> F[email outbox worker]
    D --> G[media: covers + PDF invoices]
```

```text
ShelfSpace/
├── backend/
│   ├── app/
│   │   ├── api/            # HTTP routes (v1) — auth, catalog, cart, orders, admin
│   │   ├── core/           # config, database, security, logging
│   │   ├── models/         # SQLAlchemy ORM models (26 tables)
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # business logic (orders, returns, inventory, email, …)
│   │   ├── utils/          # exceptions, handlers, pagination, serializers, rate limit
│   │   ├── db/             # seed script + demo data
│   │   └── main.py         # FastAPI app factory
│   ├── alembic/            # database migrations
│   ├── email_templates/    # Jinja2 HTML + text templates
│   ├── media/              # uploaded covers & generated invoices (gitignored)
│   └── tests/              # pytest suite (91 tests)
├── frontend/
│   ├── src/
│   │   ├── api/            # axios client (token refresh interceptor) + typed endpoints
│   │   ├── components/     # design system (Button/Card/Input/Modal/Table/…) + BookCard
│   │   ├── features/       # pages by area (catalog, cart, account, admin, auth, static)
│   │   ├── layouts/        # public/admin layouts + route guards (RequireAuth/Admin/GuestOnly, SessionRestore)
│   │   ├── stores/         # Zustand stores (auth session, guest cart)
│   │   └── types/          # shared TypeScript types
│   └── tests/              # Vitest suite
├── docs/                   # architecture notes, screenshot index, test coverage, UI audit
├── scripts/dev.sh          # one-command local dev (backend + frontend)
├── docker-compose.yml      # MySQL + backend + frontend
└── README.md
```

More detail (checkout transaction, state machine, return lifecycle, email outbox) lives in
[docs/architecture.md](docs/architecture.md).

---

## Getting started

### Prerequisites

- **Docker Desktop** (easiest), **or**
- Python 3.9+, Node.js 20+, and a local MySQL 8 server

### Option A — Docker (one command)

```bash
docker compose up --build
```

This starts MySQL, applies migrations, seeds demo data, and launches both apps:

- Storefront: **http://localhost:8080**
- API: **http://localhost:8000** · Swagger docs: **http://localhost:8000/docs**

### Option B — Local development

The repository ships `scripts/dev.sh` which performs the steps below (virtualenv, npm install,
migrations, idempotent seed) and starts both servers. To run them by hand:

**1. Database** — create two databases in your local MySQL:

```sql
CREATE DATABASE book_shop CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE book_shop_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**2. Backend**

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env               # adjust DATABASE_URL if needed
alembic upgrade head               # create the schema
python -m app.db.seed              # seed demo data (add --fresh to reseed)
uvicorn app.main:app --reload      # http://127.0.0.1:8000
```

**3. Frontend**

```bash
cd frontend
npm install
npm run dev                        # http://localhost:5173 (proxies /api to :8000)
```

> **Ports 8000/5173 busy?** The Vite proxy target can be overridden without editing config:
> `BACKEND_URL=http://127.0.0.1:8001 npm run dev -- --port 5175` (this is how the app was run
> during the audit documented in `docs/test-coverage.md`).

### Demo accounts (from the seed)

| Role | Email | Password |
| ---- | ----- | -------- |
| Admin | `admin@example.com` | `Admin@123` |
| Customer | `priya@example.com` | `Customer@123` |
| Customer | `rohan@example.com` | `Customer@123` |

> The seed creates 40 books with generated cover art, 20+ orders across every lifecycle stage,
> reviews, coupons (`WELCOME10`, `BOOKLOVER25`, `BIGSHELF15`) and store settings.

---

## Available scripts

| Where | Script | What it does |
| ----- | ------ | ------------ |
| `frontend/` | `npm run dev` | Vite dev server with `/api` + `/media` proxy |
| `frontend/` | `npm run build` | `tsc -b` type-check + production bundle |
| `frontend/` | `npm run preview` | Serve the production build locally |
| `frontend/` | `npm test` | Vitest suite (14 tests) |
| `backend/` | `uvicorn app.main:app --reload` | API dev server |
| `backend/` | `.venv/bin/python -m pytest` | Backend test suite (in-memory SQLite) |
| `backend/` | `.venv/bin/ruff check app tests` | Lint |
| `backend/` | `alembic upgrade head` | Apply migrations |
| `backend/` | `python -m app.db.seed [--fresh]` | Seed / reseed demo data |
| repo root | `scripts/dev.sh` | Backend + frontend together with setup |

---

## Environment variables

Configuration lives in `backend/.env` (copy from `backend/.env.example`). Never commit `.env`.

| Variable | Purpose |
| -------- | ------- |
| `DATABASE_URL` | MySQL connection string (`mysql+pymysql://…`) |
| `SECRET_KEY` | JWT signing secret — generate a long random value |
| `ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS` | token lifetimes |
| `CORS_ORIGINS` | Allowed frontend origins (comma-separated) |
| `FRONTEND_URL` | Used in emails (verification / reset links) |
| `EMAIL_ENABLED` | `false` = log emails to `email_logs` without sending |
| `SMTP_HOST/PORT/USER/PASSWORD`, `EMAIL_FROM` | SMTP credentials |
| `MEDIA_DIR` | Where covers/invoices are stored |
| `EMAIL_WORKER_ENABLED` | Background email worker (disable in tests) |

Store-level rules (tax, shipping, return window, low-stock threshold) are editable at runtime from
the admin Settings page.

---

## User workflows

**Guest purchase** — browse or search the catalog → open a book → add to cart (badge updates
instantly) → open `/cart` to review quantities and the estimated subtotal → *Sign in to check out*
→ the guest cart merges into the account → pick a saved address → pay with COD / demo card /
demo UPI → order confirmation with a tracking timeline.

**Order tracking & returns** — orders page → open an order → follow the six-step timeline →
once *delivered*, "Return or replace" opens a request modal (per-item quantities, reason,
description) → admin approves/completes it → refund recorded and stock restored; the customer is
notified in-app.

**Order fulfilment (admin)** — dashboard shows pending orders → open an order → advance status
through the state machine with an optional note → COD is captured automatically on delivery →
every step appears in the customer's timeline and the audit log.

**Catalog management (admin)** — books → add/edit (authors, categories, price, discount, stock,
cover upload) → archive with protection rules (ordered books archive; never-ordered books are
removed permanently) → inventory page for stock adjustments with a full movement ledger.

**Payments are a mock gateway.** `payment_service.py` defines a `PaymentGateway` protocol with a
`MockPaymentGateway` implementation (card/UPI inputs are shape-validated, no real money moves).
To integrate Stripe/Razorpay, implement the protocol and register it in `PAYMENT_PROVIDERS` —
the checkout flow needs no other changes. Likewise, emails are logged but not sent unless
`EMAIL_ENABLED=true` with real SMTP credentials.

---

## Responsive design

Verified at **1440×900**, **1280×800**, **768×1024** and **390×844** with no horizontal overflow
on any route (see [docs/test-coverage.md](docs/test-coverage.md)).

- Below 1024px the catalog filter sidebar collapses behind a **Filters** button and the admin
  sidebar becomes a horizontal scrollable pill bar.
- Below 640px the header swaps to a hamburger menu containing search, primary links and
  account actions; the cart badge stays visible.
- Book-card wishlist hearts are always visible on touch widths (hover-reveal only on desktop).
- Tables scroll horizontally inside their cards rather than breaking the layout.

Tablet and mobile captures of the home page, catalog, book detail, checkout and admin dashboard
are embedded in [section 7 of the visual showcase](#7-responsive-design).

---

## Testing and quality checks

```bash
# Frontend unit/component tests (Vitest)
cd frontend && npm test                     # 14 tests

# Frontend type-check + production build
cd frontend && npm run build

# Backend suite (in-memory SQLite; no MySQL needed)
cd backend && .venv/bin/python -m pytest    # 91 tests

# Lint
cd backend && .venv/bin/ruff check app tests
```

The backend suite covers registration/login/token rotation, catalog search & filters, cart
validation, transactional checkout (including oversell races), the order state machine,
cancellation restocking, return eligibility windows and decisions, review rules, admin RBAC,
coupons, settings and the audit log.

A full manual audit (every route, interaction, viewport and console check) was completed in
October 2026 and is documented here:

- **[docs/test-coverage.md](docs/test-coverage.md)** — what was tested and how, including the
  manual browser matrix
- **[docs/ui-audit.md](docs/ui-audit.md)** — every frontend defect found and fixed, with root
  causes and verification
- **[docs/screenshot-index.md](docs/screenshot-index.md)** — the complete image catalog

---

## Known limitations

- **Payments are simulated.** The gateway abstraction ships with a mock implementation only.
- **Email is logged, not sent**, unless `EMAIL_ENABLED=true` with real SMTP credentials; account
  verification and password reset therefore require either the log or the dev-only inline
  verification URL surfaced at registration.
- **Return-window eligibility** is enforced by the backend but not surfaced on the order payload,
  so the storefront keeps the return button enabled and the API rejects out-of-window requests
  with an explanatory message (frontend-only fix not possible; see `docs/ui-audit.md`).
- **Admin "archive" is permanent** for books that never appear in an order (backend design); the
  confirm dialog now states this explicitly.
- **Cover upload** could not be exercised by the browser automation used for the audit (file
  chooser unsupported in that environment); the endpoint is covered by backend tests.
- No end-to-end browser test suite exists in the repository — the audit's browser checks were
  manual and are recorded in `docs/test-coverage.md`.

---

## Future improvements

- Real payment gateway integration (Stripe/Razorpay) behind the existing payment abstraction
- Elasticsearch/OpenSearch for catalog search at larger scale
- Async job queue (e.g. Celery/arq) for the email worker when running multiple API replicas
- Image pipeline (thumbnails/WebP) for uploaded covers; S3-compatible storage adapter
- Recommendation engine (purchase co-occurrence) beyond today's related-by-category/author
- Return-window eligibility exposed on the order payload for upfront UI gating
- Frontend component test coverage for critical checkout flows

---

## Development notes

- **Frontend conventions** — typed API modules in `src/api`, feature folders per area, shared
  design-system primitives in `src/components/ui`, Zustand only for auth session + guest cart,
  TanStack Query for all server state (query keys: `["cart"]`, `["books", query]`, …).
- **Route guards** — `RequireAuth` (session validation + restore), `RequireAdmin`,
  `GuestOnly` (also carries the post-login destination), plus a root-level `SessionRestore`
  so public pages see the signed-in state after a reload.
- **When changing shared components**, re-check the pages listed in `docs/ui-audit.md` — several
  fixes there (label association, dropdown behaviour) live in primitives used everywhere.
- Do not commit `.env`, `backend/media/` or build output; `.gitignore` already covers them.

## License and documentation

MIT — see [LICENSE](LICENSE).

- [docs/architecture.md](docs/architecture.md) — layers, key flows (checkout transaction, order
  state machine, return lifecycle, email outbox)
- [docs/screenshot-index.md](docs/screenshot-index.md) · [docs/test-coverage.md](docs/test-coverage.md) ·
  [docs/ui-audit.md](docs/ui-audit.md)
- API docs while running: Swagger UI at `/docs`, ReDoc at `/redoc`, OpenAPI JSON at `/openapi.json`
