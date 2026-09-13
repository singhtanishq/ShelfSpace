import { lazy, Suspense } from "react";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { Toaster } from "sonner";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { PublicLayout } from "@/layouts/PublicLayout";
import { RequireAuth, RequireAdmin, GuestOnly } from "@/layouts/guards";
import { PageLoader } from "@/components/ui/states";
import { hydrateAuth } from "@/stores/auth";

const HomePage = lazy(() => import("@/features/catalog/HomePage").then((m) => ({ default: m.HomePage })));
const CatalogPage = lazy(() => import("@/features/catalog/CatalogPage").then((m) => ({ default: m.CatalogPage })));
const BookDetailPage = lazy(() => import("@/features/catalog/BookDetailPage").then((m) => ({ default: m.BookDetailPage })));
const CartPage = lazy(() => import("@/features/cart/CartPage").then((m) => ({ default: m.CartPage })));
const CheckoutPage = lazy(() => import("@/features/cart/CheckoutPage").then((m) => ({ default: m.CheckoutPage })));
const AuthPages = {
  Login: lazy(() => import("@/features/auth/AuthPages").then((m) => ({ default: m.LoginPage }))),
  Register: lazy(() => import("@/features/auth/AuthPages").then((m) => ({ default: m.RegisterPage }))),
  Forgot: lazy(() => import("@/features/auth/AuthPages").then((m) => ({ default: m.ForgotPasswordPage }))),
  Reset: lazy(() => import("@/features/auth/AuthPages").then((m) => ({ default: m.ResetPasswordPage }))),
  Verify: lazy(() => import("@/features/auth/AuthPages").then((m) => ({ default: m.VerifyEmailPage }))),
};
const Account = {
  Layout: lazy(() => import("@/features/account/AccountPages").then((m) => ({ default: m.AccountLayout }))),
  Profile: lazy(() => import("@/features/account/AccountPages").then((m) => ({ default: m.ProfilePage }))),
  Orders: lazy(() => import("@/features/account/AccountPages").then((m) => ({ default: m.OrdersPage }))),
  OrderDetail: lazy(() => import("@/features/account/AccountPages").then((m) => ({ default: m.OrderDetailPage }))),
  Addresses: lazy(() => import("@/features/account/AccountPages").then((m) => ({ default: m.AddressesPage }))),
  Wishlist: lazy(() => import("@/features/account/AccountPages").then((m) => ({ default: m.WishlistPage }))),
  MyReviews: lazy(() => import("@/features/account/AccountPages").then((m) => ({ default: m.MyReviewsPage }))),
  Security: lazy(() => import("@/features/account/AccountPages").then((m) => ({ default: m.SecurityPage }))),
  Notifications: lazy(() => import("@/features/account/AccountPages").then((m) => ({ default: m.NotificationsPage }))),
};
const AboutPage = lazy(() => import("@/features/static/StaticPages").then((m) => ({ default: m.AboutPage })));
const ContactPage = lazy(() => import("@/features/static/StaticPages").then((m) => ({ default: m.ContactPage })));
const Admin = {
  Layout: lazy(() => import("@/layouts/AdminLayout").then((m) => ({ default: m.AdminLayout }))),
  Dashboard: lazy(() => import("@/features/admin/AdminPages").then((m) => ({ default: m.AdminDashboardPage }))),
  Books: lazy(() => import("@/features/admin/AdminPages").then((m) => ({ default: m.AdminBooksPage }))),
  Inventory: lazy(() => import("@/features/admin/AdminPages").then((m) => ({ default: m.AdminInventoryPage }))),
  Terms: lazy(() => import("@/features/admin/AdminPages").then((m) => ({ default: m.AdminTermsPage }))),
  Orders: lazy(() => import("@/features/admin/AdminPages").then((m) => ({ default: m.AdminOrdersPage }))),
  OrderDetail: lazy(() => import("@/features/account/AccountPages").then((m) => ({ default: m.OrderDetailPage }))),
  Returns: lazy(() => import("@/features/admin/AdminPages").then((m) => ({ default: m.AdminReturnsPage }))),
  Users: lazy(() => import("@/features/admin/AdminPages").then((m) => ({ default: m.AdminUsersPage }))),
  Coupons: lazy(() => import("@/features/admin/AdminPages").then((m) => ({ default: m.AdminCouponsPage }))),
  Reviews: lazy(() => import("@/features/admin/AdminPages").then((m) => ({ default: m.AdminReviewsPage }))),
  Settings: lazy(() => import("@/features/admin/AdminPages").then((m) => ({ default: m.AdminSettingsPage }))),
  Audit: lazy(() => import("@/features/admin/AdminPages").then((m) => ({ default: m.AdminAuditPage }))),
};

const router = createBrowserRouter([
  {
    element: <PublicLayout />,
    children: [
      { path: "/", element: <Suspense fallback={<PageLoader />}><HomePage /></Suspense> },
      { path: "/books", element: <Suspense fallback={<PageLoader />}><CatalogPage /></Suspense> },
      { path: "/books/:slug", element: <Suspense fallback={<PageLoader />}><BookDetailPage /></Suspense> },
      { path: "/about", element: <Suspense fallback={<PageLoader />}><AboutPage /></Suspense> },
      { path: "/contact", element: <Suspense fallback={<PageLoader />}><ContactPage /></Suspense> },
      { path: "/cart", element: <Suspense fallback={<PageLoader />}><CartPage /></Suspense> },
      {
        element: <RequireAuth />,
        children: [
          { path: "/checkout", element: <Suspense fallback={<PageLoader />}><CheckoutPage /></Suspense> },
          { path: "/wishlist", element: <Suspense fallback={<PageLoader />}><Account.Wishlist /></Suspense> },
          {
            path: "/account",
            element: <Suspense fallback={<PageLoader />}><Account.Layout /></Suspense>,
            children: [
              { index: true, element: <Suspense fallback={<PageLoader />}><Account.Profile /></Suspense> },
              { path: "orders", element: <Suspense fallback={<PageLoader />}><Account.Orders /></Suspense> },
              { path: "orders/:orderNumber", element: <Suspense fallback={<PageLoader />}><Account.OrderDetail /></Suspense> },
              { path: "addresses", element: <Suspense fallback={<PageLoader />}><Account.Addresses /></Suspense> },
              { path: "reviews", element: <Suspense fallback={<PageLoader />}><Account.MyReviews /></Suspense> },
              { path: "notifications", element: <Suspense fallback={<PageLoader />}><Account.Notifications /></Suspense> },
              { path: "security", element: <Suspense fallback={<PageLoader />}><Account.Security /></Suspense> },
            ],
          },
          {
            element: <RequireAdmin />,
            children: [
              {
                path: "/admin",
                element: <Suspense fallback={<PageLoader />}><Admin.Layout /></Suspense>,
                children: [
                  { index: true, element: <Suspense fallback={<PageLoader />}><Admin.Dashboard /></Suspense> },
                  { path: "books", element: <Suspense fallback={<PageLoader />}><Admin.Books /></Suspense> },
                  { path: "inventory", element: <Suspense fallback={<PageLoader />}><Admin.Inventory /></Suspense> },
                  { path: "terms", element: <Suspense fallback={<PageLoader />}><Admin.Terms /></Suspense> },
                  { path: "orders", element: <Suspense fallback={<PageLoader />}><Admin.Orders /></Suspense> },
                  { path: "orders/:orderNumber", element: <Suspense fallback={<PageLoader />}><Admin.OrderDetail adminMode /></Suspense> },
                  { path: "returns", element: <Suspense fallback={<PageLoader />}><Admin.Returns /></Suspense> },
                  { path: "users", element: <Suspense fallback={<PageLoader />}><Admin.Users /></Suspense> },
                  { path: "coupons", element: <Suspense fallback={<PageLoader />}><Admin.Coupons /></Suspense> },
                  { path: "reviews", element: <Suspense fallback={<PageLoader />}><Admin.Reviews /></Suspense> },
                  { path: "settings", element: <Suspense fallback={<PageLoader />}><Admin.Settings /></Suspense> },
                  { path: "audit", element: <Suspense fallback={<PageLoader />}><Admin.Audit /></Suspense> },
                ],
              },
            ],
          },
        ],
      },
      {
        element: <GuestOnly />,
        children: [
          { path: "/login", element: <Suspense fallback={<PageLoader />}><AuthPages.Login /></Suspense> },
          { path: "/register", element: <Suspense fallback={<PageLoader />}><AuthPages.Register /></Suspense> },
          { path: "/forgot-password", element: <Suspense fallback={<PageLoader />}><AuthPages.Forgot /></Suspense> },
          { path: "/reset-password", element: <Suspense fallback={<PageLoader />}><AuthPages.Reset /></Suspense> },
        ],
      },
      { path: "/verify-email", element: <Suspense fallback={<PageLoader />}><AuthPages.Verify /></Suspense> },
      { path: "*", element: <NotFound /> },
    ],
  },
]);

function NotFound() {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-3 px-4 text-center">
      <p className="font-serif text-6xl font-bold text-brand-200">404</p>
      <h1 className="text-lg font-semibold text-brand-800">This page seems to be off the shelf</h1>
      <a href="/" className="text-sm font-medium text-brand-600 hover:underline">Back to home</a>
    </div>
  );
}

hydrateAuth();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <Toaster position="top-center" richColors closeButton />
    </QueryClientProvider>
  );
}
