# ShelfSpace

**A modern, production-grade bookstore management & commerce platform.**

ShelfSpace is a full-stack web application for running a real bookstore: a polished customer
storefront (browsing, search, cart, checkout, order tracking, returns and reviews) backed by a
serious admin platform (analytics dashboard, catalog & inventory management, order fulfilment,
return decisions, coupons, users, audit trail).

It began life as a terminal-based Python/MySQL school project and has been completely rebuilt as a
professional web product — the original business rules (order windows, return/replacement policies,
email notifications, PDF invoices) were preserved and massively expanded.

---

## Feature highlights

### Storefront (customers)

- **Discovery** — landing page with featured books, best sellers and new arrivals; category and
  author browsing; full-text search across title, author, ISBN, publisher and description
- **Filters & sorting** — category, author, price range, rating, availability; sort by popularity,
  newest, price or rating; pagination
- **Book pages** — rich detail view with cover, metadata, stock status, related books and reviews
- **Cart** — server-backed cart with live stock validation, coupon codes, and a guest cart that
  merges into your account at sign-in
- **Wishlist** — save books, move them to the cart later
- **Checkout** — saved address book, COD / mock card / mock UPI payments, order notes, coupons
- **Orders** — order history, live status tracking timeline, cancellation, **PDF invoice download**
- **Returns & replacements** — self-service requests within the configurable return window, with
  full status tracking and admin decisions
- **Reviews** — verified-purchase-only ratings that feed aggregate book scores
- **Account** — profile, addresses, notifications center, password change, my reviews
- **Notifications** — in-app notification center for every order and return event

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
- 90+ backend tests, typed frontend, Docker-based one-command setup

---

## Tech stack

| Layer    | Technology                                                                 |
| -------- | -------------------------------------------------------------------------- |
| Backend  | Python 3.9+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic                 |
| Database | MySQL 8 (SQLite for the test-suite)                                        |
| Auth     | JWT (PyJWT), BCrypt, refresh-token rotation                                |
| Email    | SMTP via a queue worker, Jinja2 templates                                  |
| Invoices | fpdf2                                                                      |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, TanStack Query, Zustand, Router  |
| Charts   | Recharts                                                                   |
| Testing  | pytest (backend), Vitest + Testing Library (frontend)                      |
| Infra    | Docker Compose (MySQL + API + web/nginx)                                   |

---

## Project structure

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
│   └── tests/              # pytest suite
├── frontend/
│   ├── src/
│   │   ├── api/            # axios client + typed endpoint modules
│   │   ├── components/     # design system + shared components
│   │   ├── features/       # pages by area (catalog, cart, account, admin, …)
│   │   ├── layouts/        # public/admin layouts + route guards
│   │   ├── stores/         # Zustand stores (auth, guest cart)
│   │   └── types/          # shared TypeScript types
│   └── tests/              # Vitest suite
├── docs/                   # architecture notes
├── docker-compose.yml      # MySQL + backend + frontend
└── README.md
```

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

### Demo accounts (from the seed)

| Role     | Email               | Password       |
| -------- | ------------------- | -------------- |
| Admin    | `admin@example.com` | `Admin@123`    |
| Customer | `priya@example.com` | `Customer@123` |
| Customer | `rohan@example.com` | `Customer@123` |

> The seed creates 40 books with generated cover art, 20+ orders across every lifecycle stage,
> reviews, coupons (`WELCOME10`, `BOOKLOVER25`, `BIGSHELF15`) and store settings.

---

## Environment variables

Configuration lives in `backend/.env` (copy from `backend/.env.example`). Never commit `.env`.

| Variable                    | Purpose                                              |
| --------------------------- | ---------------------------------------------------- |
| `DATABASE_URL`              | MySQL connection string (`mysql+pymysql://…`)        |
| `SECRET_KEY`                | JWT signing secret — generate a long random value    |
| `ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS` | token lifetimes |
| `CORS_ORIGINS`              | Allowed frontend origins (comma-separated)           |
| `FRONTEND_URL`              | Used in emails (verification / reset links)          |
| `EMAIL_ENABLED`             | `false` = log emails to `email_logs` without sending |
| `SMTP_HOST/PORT/USER/PASSWORD`, `EMAIL_FROM` | SMTP credentials                    |
| `MEDIA_DIR`                 | Where covers/invoices are stored                     |
| `EMAIL_WORKER_ENABLED`      | Background email worker (disable in tests)           |

Store-level rules (tax, shipping, return window, low-stock threshold) are editable at runtime from
the admin Settings page.

---

## Testing

```bash
# Backend (in-memory SQLite; no MySQL needed)
cd backend && .venv/bin/python -m pytest

# Lint
cd backend && .venv/bin/ruff check app tests

# Frontend
cd frontend && npm test
cd frontend && npm run build        # type-check + production build
```

The backend suite covers registration/login/token rotation, catalog search & filters, cart
validation, transactional checkout (including oversell races), the order state machine,
cancellation restocking, return eligibility windows and decisions, review rules, admin RBAC,
coupons, settings and the audit log.

---

## API

Interactive documentation is generated from the code:

- Swagger UI: **`/docs`** · ReDoc: **`/redoc`** · OpenAPI JSON: **`/openapi.json`**

Conventions:

- All endpoints are prefixed with `/api/v1`
- Auth via `Authorization: Bearer <access_token>`
- Consistent error envelope: `{"error": {"code", "message", "details?"}}`
- Cursor-free offset pagination: `?page=&page_size=` → `{items, total, page, page_size, pages}`

| Area            | Endpoints                                              |
| --------------- | ------------------------------------------------------ |
| Auth            | `/auth/register`, `/auth/login`, `/auth/refresh`, …    |
| Catalog         | `/home`, `/books`, `/books/{slug}`, `/books/facets`    |
| Cart            | `/cart`, `/cart/items`, `/cart/coupon`, `/cart/merge`  |
| Wishlist        | `/wishlist`                                            |
| Orders          | `/orders/checkout`, `/orders/{number}`, `/orders/{number}/invoice` |
| Returns         | `/orders/{number}/returns`, `/admin/returns/{id}/{decision}` |
| Reviews         | `/books/{slug}/reviews`                                |
| Notifications   | `/notifications`                                       |
| Account         | `/account/addresses`, `/account/reviews`               |
| Admin           | `/admin/dashboard/*`, `/admin/books`, `/admin/orders`, `/admin/users`, `/admin/coupons`, `/admin/settings`, `/admin/audit-logs` |

---

## Authentication & roles

- **JWT access token** (short-lived) + **opaque refresh token** stored hashed and rotated on every
  refresh; logout revokes the token server-side.
- Passwords are hashed with BCrypt; login is rate-limited per IP; registration has server-side
  validation (email format, username rules, password length).
- Roles: `customer` and `admin`. Admin routes are guarded server-side — customers receive `403`.
- Object ownership is enforced (users can only read their own orders/addresses/notifications), and
  ownership violations intentionally return `404` to avoid resource enumeration.
- Email verification and password reset use single-use hashed tokens with expiry.

> **Payments are a mock gateway.** `payment_service.py` defines a `PaymentGateway` protocol with a
> `MockPaymentGateway` implementation (card/UPI inputs are shape-validated, no real money moves).
> To integrate Stripe/Razorpay, implement the protocol and register it in `PAYMENT_PROVIDERS` —
> the checkout flow needs no other changes. Likewise, emails are logged but not sent unless
> `EMAIL_ENABLED=true` with real SMTP credentials.

---

## Deployment notes

- Build the API image (`backend/Dockerfile`) and the web image (`frontend/Dockerfile`, nginx serves
  the SPA and proxies `/api` + `/media` to the API container).
- Run `alembic upgrade head` as a release step before starting workers.
- Set a strong `SECRET_KEY`, real SMTP credentials, `ENVIRONMENT=production`, `DEBUG=false`, and
  restrict `CORS_ORIGINS` to your domains.
- Serve behind HTTPS; the API is stateless (JWT), so you can scale it horizontally. The email
  worker is in-process — move to a dedicated worker/queue if you run many replicas.
- Mount `backend/media` on persistent storage.

### Security practices in this repository

- No secrets in code — everything comes from environment variables (`.env` is gitignored,
  `.env.example` is committed).
- All SQL goes through SQLAlchemy's parameterized queries (no string interpolation).
- Uploaded cover images are validated by content type, size and decoded with Pillow, stored under
  generated UUID names.
- Structured logging of auth attempts, orders, status changes and admin actions (audit trail),
  with no passwords or tokens logged.
- Centralized error handlers keep stack traces out of API responses in production.

---

## Screenshots

| Storefront | Admin |
| ---------- | ----- |
| Landing page with featured books, best sellers and new arrivals | KPI dashboard with revenue/orders charts |
| Catalog with filters, sorting and search | Order list with the status state machine |
| Book detail with reviews and related titles | Inventory with movement ledger |
| Cart, coupons and checkout | Returns & replacement decisions |

_(Run it locally to see it live — seed data makes every screen feel real.)_

---

## Documentation

- [Architecture overview](docs/architecture.md) — how the layers fit together, key flows
  (checkout transaction, order state machine, return lifecycle, email outbox).

## License

MIT — see [LICENSE](LICENSE).

## Future improvements

- Real payment gateway integration (Stripe/Razorpay) behind the existing payment abstraction
- Elasticsearch/OpenSearch for catalog search at larger scale
- Async job queue (e.g. Celery/arq) for the email worker when running multiple API replicas
- Image pipeline (thumbnails/WebP) for uploaded covers; S3-compatible storage adapter
- Recommendation engine (purchase co-occurrence) beyond today's related-by-category/author
- Frontend component test coverage for critical checkout flows
