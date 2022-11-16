# ShelfSpace Screenshot Index

All screenshots were captured from the real running application (Vite dev server on
`localhost:5175`, FastAPI backend on `localhost:8001`, MySQL seed data) during the October 2026
frontend audit. Viewports: desktop **1440×900**, tablet **768×1024**, mobile **390×844**.

Organisation:

| Folder | Contents |
| ------ | -------- |
| `01-overview/` | Landing page, desktop and mobile presentations |
| `02-storefront/` | Customer pages: catalog, book detail, cart, checkout, orders, account |
| `03-admin/` | Admin platform pages |
| `04-auth/` | Sign-in, registration and password flows |
| `05-responsive/` | Tablet and mobile layouts of representative pages |

---

## 01 — Overview

### Desktop

![Home page — desktop](screenshots/01-overview/home-desktop.png)

The storefront hero, category chips and navigation at desktop width. Demonstrates the default
entry point every visitor sees.

![Home page — desktop, full page](screenshots/01-overview/home-desktop-full.png)

Full-page capture: hero, perks strip, category chips, featured/best-seller/new-arrival rails,
the WELCOME10 promo banner and the footer.

### Mobile

![Home page — mobile](screenshots/01-overview/home-mobile.png)

The landing page collapses to a single column with the hamburger menu, search inside the menu and
the cart icon always visible.

![Home page — mobile menu open](screenshots/01-overview/home-mobile-menu-open.png)

The open mobile navigation drawer with search, primary links and Sign in / Sign up actions.

---

## 02 — Storefront

### Catalog

![Catalog — desktop](screenshots/02-storefront/catalog-desktop.png)

40 seeded titles with the filter sidebar (category, author finder, price range, rating,
availability), sort dropdown and result count.

### Book detail

![Book detail — desktop](screenshots/02-storefront/book-detail-desktop.png)

Cover, price with discount badge, stock indicator, quantity stepper, add-to-cart/wishlist
actions, metadata table and reader reviews for *Dune*.

### Cart

![Cart — signed-in with coupon](screenshots/02-storefront/cart-desktop.png)

Server-backed cart with quantity steppers, line totals and the WELCOME10 coupon applied
(−₹200, hitting the coupon's maximum-discount cap).

![Cart — guest](screenshots/02-storefront/cart-guest-desktop.png)

The guest cart stored in localStorage: line items with an estimated subtotal and a
"Sign in to check out" call to action. The cart merges into the account at sign-in.

### Checkout & orders

![Checkout — desktop](screenshots/02-storefront/checkout-desktop.png)

Saved-address picker (radio cards with inline edit), COD / demo-card / demo-UPI payment
methods, order notes and the sticky order summary with the coupon discount.

![Order confirmation](screenshots/02-storefront/order-confirmation-desktop.png)

The order detail page immediately after checkout: success banner, order number
`SS-20261024-00027`, pending status badges, the six-step tracking timeline and the invoice button.

![Account orders](screenshots/02-storefront/account-orders-desktop.png)

Order history with status/payment badges, thumbnails and the status filter dropdown.

![Order detail with tracking](screenshots/02-storefront/order-detail-tracking-desktop.png)

A delivered order: completed tracking timeline, per-item totals, the return request section
(`RT-00002`, completed) and the full status history.

### Account

![Addresses](screenshots/02-storefront/account-addresses-desktop.png)

Saved address cards with edit/delete actions and the default-address marker.

![Wishlist](screenshots/02-storefront/wishlist-desktop.png)

Saved books with "Move to cart" and remove actions.

![Notifications](screenshots/02-storefront/account-notifications-desktop.png)

The in-app notification centre with unread markers, per-item and bulk mark-as-read.

![Profile](screenshots/02-storefront/account-profile-desktop.png)

Profile details form with the disabled email/username fields and unverified-email banner.

![Security](screenshots/02-storefront/account-security-desktop.png)

Change-password form with current/new/confirm fields.

![My reviews](screenshots/02-storefront/account-my-reviews-desktop.png)

Reviews written by the signed-in customer with rating stars and delete action.

---

## 03 — Admin

All admin pages share the fixed sidebar navigation (desktop) or the horizontal pill bar
(see `05-responsive/`).

![Admin dashboard](screenshots/03-admin/admin-dashboard-desktop.png)

KPI cards (revenue, orders, customers, inventory value), alert strip, revenue/orders charts,
top sellers, status mix and customer growth — 365-day range.

![Admin orders](screenshots/03-admin/admin-orders-desktop.png)

Searchable, status-filtered order table with payment and fulfilment badges.

![Admin order manage](screenshots/03-admin/admin-order-manage-desktop.png)

The combined customer order view plus the "Manage status" panel with the allowed next
transitions and an attached note.

![Admin books](screenshots/03-admin/admin-books-desktop.png)

Catalog table with cover thumbnails, pricing, stock, ratings, active/featured badges and
view/edit/archive actions.

![Admin inventory](screenshots/03-admin/admin-inventory-desktop.png)

Stock table with reserved/available columns, health badges and history/adjust actions.

![Admin taxonomy](screenshots/03-admin/admin-terms-desktop.png)

Categories/authors/publishers manager.

![Admin users](screenshots/03-admin/admin-users-desktop.png)

Account list with inline role selector, order/spend stats, verification flags and
deactivate/reactivate actions.

![Admin coupons](screenshots/03-admin/admin-coupons-desktop.png)

Coupon table with discount shape, minimum order, usage counters and enable/disable actions.

![Admin reviews](screenshots/03-admin/admin-reviews-desktop.png)

Review moderation list with verified badges and hide/unhide.

![Admin returns](screenshots/03-admin/admin-returns-desktop.png)

Return and replacement requests with order links, refund amounts and decision buttons.

![Admin settings](screenshots/03-admin/admin-settings-desktop.png)

Store name/support email/currency plus the numeric commerce rules (tax, shipping,
free-shipping threshold, return window, low-stock default).

![Admin audit log](screenshots/03-admin/admin-audit-desktop.png)

Chronological record of administrative actions with actor, action, entity and detail.

---

## 04 — Authentication

![Login](screenshots/04-auth/login-desktop.png)

The sign-in screen (email/username or password).

![Login — validation errors](screenshots/04-auth/login-validation-error.png)

Submitting the empty form surfaces inline, per-field validation messages (role=alert).

![Register](screenshots/04-auth/register-desktop.png)

Account creation with username rules and minimum password length hints.

![Forgot password — sent](screenshots/04-auth/forgot-password-sent.png)

The confirmation state after requesting a reset link (privacy-safe wording).

---

## 05 — Responsive

![Catalog — tablet](screenshots/05-responsive/catalog-tablet.png)

At 768px the filter sidebar collapses behind the "Filters" button; the grid reflows.

![Catalog — mobile](screenshots/05-responsive/catalog-mobile.png)

Two-column card grid at 390px with the wishlist heart always visible on touch screens.

![Book detail — mobile](screenshots/05-responsive/book-detail-mobile.png)

Stacked cover/info layout with full-width actions.

![Checkout — mobile](screenshots/05-responsive/checkout-mobile.png)

Checkout forms stack to a single column; the summary moves below the forms.

![Home — tablet](screenshots/05-responsive/home-tablet.png)

Landing page at 768px.

![Admin dashboard — tablet](screenshots/05-responsive/admin-dashboard-tablet.png)

The admin sidebar becomes a horizontal scrollable pill bar below 1024px.

![Admin dashboard — mobile](screenshots/05-responsive/admin-dashboard-mobile.png)

KPI cards stack two-per-row at 390px; charts remain full-width.
