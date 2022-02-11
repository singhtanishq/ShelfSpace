/** Shared API types mirroring the backend schemas. */

export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
  phone: string | null;
  role: "customer" | "admin";
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface Author {
  id: number;
  name: string;
  slug: string;
  bio: string | null;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  description: string | null;
}

export interface Publisher {
  id: number;
  name: string;
  slug: string;
}

export interface Book {
  id: number;
  title: string;
  slug: string;
  cover_image: string | null;
  price: number;
  discount_percent: number;
  effective_price: number;
  rating_avg: number;
  rating_count: number;
  is_active: boolean;
  is_featured: boolean;
  authors: Author[];
  categories: Category[];
  available_quantity: number;
}

export interface AdminBook extends Book {
  isbn: string | null;
  description: string | null;
  language: string;
  format: "paperback" | "hardcover";
  pages: number | null;
  published_year: number | null;
  publisher: Publisher | null;
  created_at: string;
  stock_quantity: number;
  reserved_quantity: number;
  low_stock_threshold: number;
  sales_count: number;
}

export interface Facets {
  price_min: number;
  price_max: number;
  languages: string[];
  categories: Category[];
  authors: Author[];
}

export interface HomeFeed {
  featured: Book[];
  best_sellers: Book[];
  new_arrivals: Book[];
  categories: Category[];
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface CartItem {
  book_id: number;
  title: string;
  slug: string;
  cover_image: string | null;
  author_names: string;
  unit_price: number;
  original_price: number;
  discount_percent: number;
  quantity: number;
  line_total: number;
  available_quantity: number;
  in_stock: boolean;
}

export interface Cart {
  items: CartItem[];
  subtotal: number;
  discount_total: number;
  shipping_fee: number;
  tax_total: number;
  total: number;
  coupon: { code: string; description: string | null } | null;
  coupon_error: string | null;
  currency: string;
  total_quantity: number;
}

export interface WishlistItem {
  book_id: number;
  title: string;
  slug: string;
  cover_image: string | null;
  author_names: string;
  price: number;
  effective_price: number;
  discount_percent: number;
  available_quantity: number;
  added_at: string;
}

export interface ShippingAddress {
  full_name: string;
  phone: string;
  line1: string;
  line2?: string | null;
  city: string;
  state: string;
  postal_code: string;
  country: string;
}

export interface Address extends ShippingAddress {
  id: number;
  label: string;
  is_default: boolean;
  created_at: string;
}

export interface OrderItem {
  id: number;
  book_id: number | null;
  title: string;
  author_names: string;
  cover_image: string | null;
  isbn: string | null;
  unit_price: number;
  quantity: number;
  line_total: number;
}

export interface ReturnRequest {
  id: number;
  return_number: string;
  order_id: number;
  order_number: string;
  user_id: number;
  type: "return" | "replacement";
  status: "requested" | "approved" | "rejected" | "completed";
  reason: string;
  description: string | null;
  refund_amount: number | null;
  refund_status: "none" | "initiated" | "completed";
  admin_note: string | null;
  created_at: string;
  decided_at: string | null;
  completed_at: string | null;
  items: { order_item_id: number; quantity: number; title: string }[];
}

export interface Order {
  id: number;
  order_number: string;
  user_id: number;
  status: OrderStatus;
  payment_method: "cod" | "card" | "upi";
  payment_status: "pending" | "paid" | "failed" | "refunded";
  subtotal: number;
  discount_total: number;
  shipping_fee: number;
  tax_total: number;
  total: number;
  coupon_code: string | null;
  shipping_address: ShippingAddress;
  notes: string | null;
  placed_at: string;
  delivered_at: string | null;
  cancelled_at: string | null;
  items: OrderItem[];
  status_history: {
    from_status: OrderStatus | null;
    to_status: OrderStatus;
    note: string | null;
    created_at: string;
    changed_by_id: number | null;
  }[];
  returns: ReturnRequest[];
}

export type OrderStatus =
  | "pending"
  | "confirmed"
  | "processing"
  | "shipped"
  | "out_for_delivery"
  | "delivered"
  | "cancelled"
  | "returned";

export interface Review {
  id: number;
  book_id: number;
  user_id: number;
  rating: number;
  title: string | null;
  content: string;
  is_verified_purchase: boolean;
  is_hidden: boolean;
  created_at: string;
  updated_at: string;
  author_name: string;
}

export interface Notification {
  id: number;
  type: string;
  title: string;
  body: string;
  link: string | null;
  is_read: boolean;
  created_at: string;
}

export interface Coupon {
  id: number;
  code: string;
  description: string | null;
  discount_type: "percent" | "fixed";
  value: number;
  min_order_amount: number;
  max_discount_amount: number | null;
  usage_limit: number | null;
  used_count: number;
  starts_at: string | null;
  expires_at: string | null;
  is_active: boolean;
  created_at: string;
}

export interface InventoryRow {
  book_id: number;
  title: string;
  slug: string;
  cover_image: string | null;
  stock_quantity: number;
  reserved_quantity: number;
  available_quantity: number;
  low_stock_threshold: number;
  is_low_stock: boolean;
  is_active: boolean;
  price: number;
}

export interface InventoryTransaction {
  id: number;
  change: number;
  change_type: string;
  balance_after: number;
  reference_type: string | null;
  reference_id: string | null;
  note: string | null;
  created_by: number | null;
  created_at: string;
}

export interface DashboardSummary {
  currency: string;
  total_revenue: number;
  total_orders: number;
  total_customers: number;
  total_books: number;
  active_books: number;
  inventory_value: number;
  pending_orders: number;
  open_returns: number;
  low_stock_count: number;
  out_of_stock_count: number;
  avg_order_value: number;
  orders_today: number;
  revenue_today: number;
}

export interface SeriesPoint {
  date: string;
  value: number;
  count: number;
}

export interface ChartData {
  revenue: SeriesPoint[];
  orders: SeriesPoint[];
  customer_growth: SeriesPoint[];
}

export interface TopBook {
  book_id: number | null;
  title: string;
  author_names: string;
  units_sold: number;
  revenue: number;
}

export interface TopCategory {
  name: string;
  units_sold: number;
  revenue: number;
}

export interface TopEntities {
  books: TopBook[];
  categories: TopCategory[];
  status_distribution: { status: string; count: number }[];
}

export interface AdminUser extends User {
  order_count: number;
  total_spent: number;
}

export interface StoreSettings {
  store_name: string;
  support_email: string;
  tax_percent: number;
  shipping_fee: number;
  free_shipping_threshold: number;
  return_window_days: number;
  low_stock_threshold: number;
  currency: string;
}

export interface AuditLog {
  id: number;
  actor_id: number | null;
  actor_name: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  detail: Record<string, unknown> | null;
  created_at: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: { field: string; message: string }[];
  };
}
