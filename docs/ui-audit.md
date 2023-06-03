# ShelfSpace — UI/UX Audit

**Date:** 24 October 2026 · **Scope:** frontend only (`frontend/src`) · **Method:** full source
review of all 30 application-owned files followed by black-box browser testing of every route at
desktop (1440), laptop (1280), tablet (768) and mobile (390) widths.

The design system (brand-blue + amber palette, `Card`/`Button`/`Input`/`Modal` primitives,
Inter + serif display type) was in good shape before this audit; the existing visual direction
was preserved. All fixes below are targeted corrections, not redesigns.

---

## Issue register

| ID | Severity | Area | Description | Root cause | Fix | Verified |
| -- | -------- | ---- | ----------- | ---------- | --- | -------- |
| UI-01 | **Critical** | Admin → Settings | Page always rendered the React error boundary ("Rendered more hooks than during the previous render") — completely unusable | `useMutation` was declared *after* an early `return <PageLoader/>`, so the hook count changed once data arrived | Moved `useMutation` above the early return in `AdminSettingsPage` | Yes — page loads, fields render, save works |
| UI-02 | **Critical** | Admin → Users | Page always crashed with "Cannot read properties of undefined (reading 'length')" | `GET /admin/users` returns a bare array, but the page read `data.items.length` (paginated envelope) | Consume the array, fetch `page_size: 60`, keep server-side search, drop the misleading pagination control, fix the endpoint type | Yes — 8 seeded accounts render, search present |
| UI-03 | **High** | Cart | Guests with items saw "Your cart is empty" while the header badge showed N items; guests could not review their cart before signing in | `CartPage` only rendered the server cart; the localStorage guest cart was never displayed. The cart query also fired a guaranteed `401` for guests | Added a guest-cart variant: line items (cover, title, author, unit price, stepper, remove), estimated subtotal, "Sign in to check out" CTA. Query gated with `enabled: !!accessToken`. New `setQuantity` action in the guest store (+ unit test) | Yes — full guest → sign-in → merge → `/cart` flow passes |
| UI-04 | **High** | Auth/session | After a full page reload on any public page a signed-in user was treated as signed out: wishlist button said "Sign in to save…", add-to-cart went to the guest cart | Session restore from the persisted refresh token lived inside `RequireAuth`, so it only ran on protected routes | New `SessionRestore` component mounted once at the app root; the restore query dedupes with the guard's own | Yes — reload on `/` and `/books/:slug` keeps the session |
| UI-05 | **High** | Auth/session | After signing in, the user was always sent to `/` — the page they came from (e.g. `/cart`, `/checkout`) was lost | `GuestOnly`'s render-phase `Navigate to="/"` always superseded the login page's `navigate(from)` | `GuestOnly` now redirects to `location.state.from ?? "/"` so the intended destination wins regardless of ordering | Yes — guest cart CTA returns to `/cart` after sign-in |
| UI-06 | **Medium** | Accessibility | Zero label↔input associations in every form (`Field` rendered `htmlFor` but no input ever had an `id`) — screen readers announced only placeholders | `Field` never generated or passed an id | `Field` now auto-generates an id (`useId`) and injects it into the child control via `cloneElement`; explicit `id`/`htmlFor` still wins | Yes — settings/login inputs report `labels.length === 1` |
| UI-07 | **Medium** | Catalog (touch) | The wishlist heart on book cards was `opacity-0` until hover — invisible and undiscoverable on touch devices | Hover-only reveal applied at all breakpoints | Heart is always visible below `lg`; hover-reveal retained on desktop (`lg:opacity-0 lg:group-hover:opacity-100`) | Yes — computed opacity 1 at 390px |
| UI-08 | **Low** | Copy | "Added 2 copy to your cart" | Missing pluralisation | `copy`/`copies` based on quantity | Yes — toast reads "Added 2 copies…" |
| UI-09 | **Low** | Admin → Books | Archive dialog claimed books are "re-activatable any time"; the backend permanently deletes books never referenced by orders | Dialog copy overstated reversibility | Copy now states both outcomes (ordered books archive, never-ordered books are removed permanently) | Yes |
| UI-10 | **Low** | Header | The avatar dropdown stayed open after choosing an entry (`<details>` state survives client-side navigation) | No close handler | `onClick` closes the dropdown when an inner link/button is clicked | Yes — `details.open === false` after navigation |
| UI-11 | **Low** | Auth/session | Signing out from a protected page landed on `/login` instead of home (the auth guard's redirect won the race against `navigate("/")`) | Guard re-rendered on the store update before the router transition committed | `onLogout` now finishes with `window.location.assign("/")` — a clean, race-free navigation that also resets the store | Yes — logout from `/account` lands on `/` |

Non-frontend issues found during testing (documented, **not** modified):

- **Return-window eligibility** (medium): the "Return or replace" button is enabled for any
  delivered order, but the backend rejects requests outside the store's 14-day return window.
  The customer API does not expose store settings, so the UI cannot know eligibility without a
  backend change; the error toast explains the rejection. Fixing this properly belongs to the
  API (e.g. include `return_eligible` on the order payload).
- **Login for admins without a `from` destination** lands on `/` rather than `/admin` (same
  render-phase redirect ordering as UI-05). Admins reach the dashboard via the header icon; a
  future improvement could pass the destination through `GuestOnly` state as well.

## Verification performed

- Every fix was re-tested in the running app (see `test-coverage.md` for the per-scenario
  results) at the affected viewport(s).
- `npm test` (14/14), `npm run build` (type-check + bundle) re-run after the final change.
- Pages sharing touched components (BookCard, Field, guards, PublicLayout) were re-checked:
  catalog grids on storefront, every admin form using `Field`, login/register/checkout forms,
  both role journeys.

## Files changed

| File | Change |
| ---- | ------ |
| `frontend/src/features/admin/AdminPages.tsx` | UI-01, UI-02, UI-09 |
| `frontend/src/features/cart/CartPage.tsx` | UI-03 (guest cart variant + query gate) |
| `frontend/src/stores/guestCart.ts` | UI-03 (`setQuantity` action) |
| `frontend/src/layouts/guards.tsx` | UI-04 (`SessionRestore`), UI-05 (`GuestOnly` destination) |
| `frontend/src/App.tsx` | UI-04 (mount `SessionRestore`) |
| `frontend/src/components/ui/Input.tsx` | UI-06 (label association) |
| `frontend/src/components/books/BookCard.tsx` | UI-07 (heart visibility) |
| `frontend/src/features/catalog/BookDetailPage.tsx` | UI-08 (pluralisation) |
| `frontend/src/layouts/PublicLayout.tsx` | UI-10 (dropdown close), UI-11 (logout) |
| `frontend/src/api/endpoints.ts` | UI-02 (users endpoint return type) |
| `frontend/tests/stores.test.ts` | New test for `setQuantity` |
| `frontend/vite.config.ts` | `BACKEND_URL` env override for the dev proxy (default unchanged) — allows the audit to run on non-default ports |
