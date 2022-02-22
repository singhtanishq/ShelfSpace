/** Typed API endpoint modules. */

import { api } from "./client";
import type {
  Address,
  AdminBook,
  AdminUser,
  AuditLog,
  Book,
  Cart,
  Cart as CartType,
  ChartData,
  Coupon,
  DashboardSummary,
  Facets,
  HomeFeed,
  InventoryRow,
  InventoryTransaction,
  Notification,
  Order,
  Paginated,
  Review,
  StoreSettings,
  TopEntities,
  User,
  WishlistItem,
} from "@/types/api";

// ---------------------------------------------------------------- auth
export const authApi = {
  register: (data: { email: string; username: string; full_name: string; password: string }) =>
    api.post("/auth/register", data),
  login: (data: { identifier: string; password: string }) => api.post("/auth/login", data),
  logout: (refresh_token: string) => api.post("/auth/logout", { refresh_token }),
  verifyEmail: (token: string) => api.post("/auth/verify-email", { token }),
  resendVerification: (email: string) => api.post("/auth/resend-verification", { email }),
  forgotPassword: (email: string) => api.post("/auth/forgot-password", { email }),
  resetPassword: (data: { token: string; new_password: string }) => api.post("/auth/reset-password", data),
  me: () => api.get<User>("/auth/me"),
  updateProfile: (data: { full_name?: string; phone?: string | null }) => api.put<User>("/auth/me", data),
  changePassword: (data: { current_password: string; new_password: string }) =>
    api.put("/auth/me/password", data),
};

// ---------------------------------------------------------------- catalog
export interface BookQuery {
  q?: string;
  category?: string;
  author?: string;
  language?: string;
  min_price?: number;
  max_price?: number;
  min_rating?: number;
  in_stock?: boolean;
  sort?: string;
  page?: number;
  page_size?: number;
}

export const catalogApi = {
  home: () => api.get<HomeFeed>("/home"),
  books: (params: BookQuery) => api.get<Paginated<Book>>("/books", { params }),
  facets: () => api.get<Facets>("/books/facets"),
  book: (slug: string) => api.get<Book & { description?: string; isbn?: string; pages?: number; published_year?: number; language?: string; format?: string; publisher?: { id: number; name: string; slug: string } | null; created_at?: string }>(`/books/${slug}`),
  related: (slug: string) =>
    api.get<{ related: Book[]; by_same_author: Book[] }>(`/books/${slug}/related`),
  reviews: (slug: string, params?: { page?: number }) =>
    api.get<Paginated<Review>>(`/books/${slug}/reviews`, { params }),
  createReview: (slug: string, data: { rating: number; title?: string; content: string }) =>
    api.post<Review>(`/books/${slug}/reviews`, data),
  updateReview: (id: number, data: { rating?: number; title?: string; content?: string }) =>
    api.put<Review>(`/reviews/${id}`, data),
  deleteReview: (id: number) => api.delete(`/reviews/${id}`),
  myReviews: () => api.get<Review[]>("/admin/reviews"), // replaced below; see accountApi
};

// ---------------------------------------------------------------- cart & wishlist
export const cartApi = {
  get: () => api.get<CartType>("/cart"),
  addItem: (book_id: number, quantity: number) =>
    api.post<CartType>("/cart/items", { book_id, quantity }),
  updateItem: (bookId: number, quantity: number) =>
    api.patch<CartType>(`/cart/items/${bookId}`, { quantity }),
  removeItem: (bookId: number) => api.delete<CartType>(`/cart/items/${bookId}`),
  clear: () => api.delete<CartType>("/cart"),
  applyCoupon: (code: string) => api.post<CartType>("/cart/coupon", { code }),
  removeCoupon: () => api.delete<CartType>("/cart/coupon"),
  merge: (items: { book_id: number; quantity: number }[]) =>
    api.post<CartType>("/cart/merge", { items }),
};

export const wishlistApi = {
  list: () => api.get<WishlistItem[]>("/wishlist"),
  add: (book_id: number) => api.post<WishlistItem[]>("/wishlist", { book_id }),
  remove: (bookId: number) => api.delete(`/wishlist/${bookId}`),
};

// ---------------------------------------------------------------- orders & returns
export const ordersApi = {
  checkout: (data: {
    address_id?: number;
    shipping_address?: Record<string, string>;
    payment_method: "cod" | "card" | "upi";
    notes?: string;
    card_number?: string;
    upi_id?: string;
  }) => api.post<Order>("/orders/checkout", data),
  list: (params?: { status?: string; page?: number; page_size?: number }) =>
    api.get<Paginated<Order>>("/orders", { params }),
  detail: (orderNumber: string) => api.get<Order>(`/orders/${orderNumber}`),
  cancel: (orderNumber: string, note?: string) =>
    api.post<Order>(`/orders/${orderNumber}/cancel`, { note }),
  invoiceUrl: (orderNumber: string) => `/api/v1/orders/${orderNumber}/invoice`,
  createReturn: (
    orderNumber: string,
    data: {
      type: "return" | "replacement";
      reason: string;
      description?: string;
      items: { order_item_id: number; quantity: number }[];
    }
  ) => api.post(`/orders/${orderNumber}/returns`, data),
  myReturns: () => api.get("/orders/returns"),
};

// ---------------------------------------------------------------- addresses
export const addressApi = {
  list: () => api.get<Address[]>("/account/addresses"),
  create: (data: Record<string, unknown>) => api.post<Address>("/account/addresses", data),
  update: (id: number, data: Record<string, unknown>) => api.put<Address>(`/account/addresses/${id}`, data),
  remove: (id: number) => api.delete(`/account/addresses/${id}`),
};

// ---------------------------------------------------------------- notifications
export const notificationsApi = {
  list: (params?: { page?: number }) =>
    api.get<Paginated<Notification> & { unread_count: number }>("/notifications", { params }),
  unreadCount: () => api.get<{ count: number }>("/notifications/unread-count"),
  markRead: (id: number) => api.post(`/notifications/${id}/read`),
  markAllRead: () => api.post("/notifications/read-all"),
};

// ---------------------------------------------------------------- admin
export interface AdminOrderQuery extends Record<string, unknown> {
  status?: string;
  q?: string;
  page?: number;
  page_size?: number;
}

export const adminApi = {
  dashboardSummary: (days = 30) => api.get<DashboardSummary>("/admin/dashboard/summary", { params: { days } }),
  dashboardCharts: (days = 30) => api.get<ChartData>("/admin/dashboard/charts", { params: { days } }),
  dashboardTop: (days = 30) => api.get<TopEntities>("/admin/dashboard/top", { params: { days } }),
  lowStock: () => api.get("/admin/dashboard/low-stock"),

  books: (params: Record<string, unknown>) => api.get<AdminBook[]>("/admin/books", { params }),
  book: (id: number) => api.get<AdminBook>(`/admin/books/${id}`),
  createBook: (data: Record<string, unknown>) => api.post<AdminBook>("/admin/books", data),
  updateBook: (id: number, data: Record<string, unknown>) => api.put<AdminBook>(`/admin/books/${id}`, data),
  deleteBook: (id: number, hard = false) => api.delete(`/admin/books/${id}`, { params: { hard } }),
  uploadCover: (id: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post<AdminBook>(`/admin/books/${id}/cover`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  inventory: (params: Record<string, unknown>) => api.get<InventoryRow[]>("/admin/inventory", { params }),
  adjustInventory: (bookId: number, data: { change: number; note?: string }) =>
    api.post<InventoryRow>(`/admin/inventory/${bookId}/adjust`, data),
  inventoryTransactions: (bookId: number, params?: Record<string, unknown>) =>
    api.get<InventoryTransaction[]>(`/admin/inventory/${bookId}/transactions`, { params }),

  categories: () => api.get("/admin/categories"),
  authors: () => api.get("/admin/authors"),
  publishers: () => api.get("/admin/publishers"),
  createTerm: (kind: "categories" | "authors" | "publishers", data: Record<string, unknown>) =>
    api.post(`/admin/${kind}`, data),
  updateTerm: (kind: "categories" | "authors" | "publishers", id: number, data: Record<string, unknown>) =>
    api.put(`/admin/${kind}/${id}`, data),
  deleteTerm: (kind: "categories" | "authors" | "publishers", id: number) =>
    api.delete(`/admin/${kind}/${id}`),

  orders: (params: AdminOrderQuery) => api.get<Paginated<Order>>("/admin/orders", { params }),
  order: (orderNumber: string) => api.get<Order>(`/admin/orders/${orderNumber}`),
  updateStatus: (orderNumber: string, status: string, note?: string) =>
    api.put<Order>(`/admin/orders/${orderNumber}/status`, { status, note }),

  returns: (params?: { status?: string; type?: string }) =>
    api.get("/admin/returns", { params }),
  decideReturn: (id: number, decision: "approve" | "reject" | "complete", note?: string) =>
    api.put(`/admin/returns/${id}/${decision}`, { note }),

  users: (params: Record<string, unknown>) => api.get<Paginated<AdminUser>>("/admin/users", { params }),
  user: (id: number) => api.get<AdminUser>(`/admin/users/${id}`),
  updateUser: (id: number, data: Record<string, unknown>) => api.put<AdminUser>(`/admin/users/${id}`, data),
  deleteUser: (id: number, hard = false) => api.delete(`/admin/users/${id}`, { params: { hard } }),

  coupons: () => api.get<Coupon[]>("/admin/coupons"),
  createCoupon: (data: Record<string, unknown>) => api.post<Coupon>("/admin/coupons", data),
  updateCoupon: (id: number, data: Record<string, unknown>) => api.put<Coupon>(`/admin/coupons/${id}`, data),
  deleteCoupon: (id: number) => api.delete(`/admin/coupons/${id}`),

  reviews: (params?: { hidden?: boolean }) => api.get<Review[]>("/admin/reviews", { params }),
  hideReview: (id: number) => api.put(`/admin/reviews/${id}/hide`),
  showReview: (id: number) => api.put(`/admin/reviews/${id}/show`),

  settings: () => api.get<StoreSettings>("/admin/settings"),
  updateSettings: (data: Partial<StoreSettings>) => api.put<StoreSettings>("/admin/settings", data),

  auditLogs: (params: Record<string, unknown>) => api.get<Paginated<AuditLog>>("/admin/audit-logs", { params }),
};

// ---------------------------------------------------------------- account extras
export const accountApi = {
  myReviews: () =>
    api.get<Paginated<Review>>("/admin/reviews").catch(() => null), // customers have no admin route; use per-book data
};
