import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, type NavigateFunction } from "react-router-dom";
import { Trash2, ShoppingBag, Tag } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { cartApi, catalogApi } from "@/api/endpoints";
import { BookCover } from "@/components/books/BookCard";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { QuantityStepper } from "@/components/ui/misc";
import { EmptyState, PageLoader } from "@/components/ui/states";
import { useAuthStore } from "@/stores/auth";
import { useGuestCart } from "@/stores/guestCart";
import { formatCurrency } from "@/utils";
import type { Book } from "@/types/api";

export function CartPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const accessToken = useAuthStore((s) => s.accessToken);
  const [couponCode, setCouponCode] = useState("");

  const { data: cart, isLoading } = useQuery({
    queryKey: ["cart"],
    queryFn: () => cartApi.get().then((r) => r.data),
    enabled: !!accessToken,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["cart"] });

  const updateQty = useMutation({
    mutationFn: ({ bookId, qty }: { bookId: number; qty: number }) => cartApi.updateItem(bookId, qty),
    onSuccess: invalidate,
    onError: (err: any) => toast.error(err?.response?.data?.error?.message ?? "Could not update quantity"),
  });

  const removeItem = useMutation({
    mutationFn: (bookId: number) => cartApi.removeItem(bookId),
    onSuccess: () => {
      toast.success("Removed from cart");
      invalidate();
    },
  });

  const applyCoupon = useMutation({
    mutationFn: () => cartApi.applyCoupon(couponCode),
    onSuccess: (r) => {
      toast.success(`Coupon ${r.data.coupon?.code} applied!`);
      setCouponCode("");
      invalidate();
    },
    onError: (err: any) => toast.error(err?.response?.data?.error?.message ?? "Invalid coupon"),
  });

  const removeCoupon = useMutation({
    mutationFn: () => cartApi.removeCoupon(),
    onSuccess: invalidate,
  });

  // Signed-in cart
  if (accessToken) {
    return (
      <CartContent
        isLoading={isLoading}
        cart={cart}
        couponCode={couponCode}
        setCouponCode={setCouponCode}
        applyCoupon={applyCoupon}
        removeCoupon={removeCoupon}
        updateQty={updateQty}
        removeItem={removeItem}
        navigate={navigate}
      />
    );
  }

  // Guest cart (persisted locally, merged into the account at sign-in)
  return <GuestCartContent navigate={navigate} />;
}

/* ---------------------------------------------------------------- signed-in */

function CartContent({
  isLoading,
  cart,
  couponCode,
  setCouponCode,
  applyCoupon,
  removeCoupon,
  updateQty,
  removeItem,
  navigate,
}: any) {
  if (isLoading) return <PageLoader label="Loading your cart…" />;

  if (!cart || cart.items.length === 0) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16">
        <EmptyState
          icon={<ShoppingBag className="h-10 w-10" aria-hidden />}
          title="Your cart is empty"
          description="Browse the shelves and add some books you love."
          action={<Button onClick={() => navigate("/books")}>Browse books</Button>}
        />
      </div>
    );
  }

  const outOfStockItems = cart.items.filter((i: any) => !i.in_stock);

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <h1 className="font-serif text-2xl font-bold text-brand-900 sm:text-3xl">Your cart</h1>
      <p className="mt-1 text-sm text-brand-400">
        {cart.total_quantity} item{cart.total_quantity === 1 ? "" : "s"} in your cart
      </p>

      {outOfStockItems.length > 0 && (
        <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          Some items in your cart exceed available stock. Adjust the quantities below before checkout.
        </div>
      )}

      <div className="mt-6 grid gap-8 lg:grid-cols-[1fr_360px]">
        {/* Items */}
        <div className="space-y-4">
          {cart.items.map((item: any) => (
            <Card key={item.book_id} className="flex gap-4 p-4">
              <Link to={`/books/${item.slug}`} className="shrink-0">
                <BookCover src={item.cover_image} alt={item.title} className="h-28 w-20 rounded-lg" />
              </Link>
              <div className="flex min-w-0 flex-1 flex-col">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <Link to={`/books/${item.slug}`} className="line-clamp-1 font-semibold text-brand-900 hover:text-brand-600">
                      {item.title}
                    </Link>
                    <p className="mt-0.5 text-sm text-brand-400">{item.author_names}</p>
                  </div>
                  <button
                    onClick={() => removeItem.mutate(item.book_id)}
                    className="rounded-lg p-1.5 text-brand-300 hover:bg-red-50 hover:text-red-600"
                    aria-label={`Remove ${item.title} from cart`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
                <div className="mt-auto flex flex-wrap items-center justify-between gap-3 pt-3">
                  <QuantityStepper
                    value={item.quantity}
                    max={Math.max(item.available_quantity, 1)}
                    onChange={(qty: number) => updateQty.mutate({ bookId: item.book_id, qty })}
                  />
                  <div className="text-right">
                    <p className="font-bold text-brand-900">{formatCurrency(item.line_total)}</p>
                    {item.discount_percent > 0 && (
                      <p className="text-xs text-brand-300 line-through">{formatCurrency(item.original_price * item.quantity)}</p>
                    )}
                    {!item.in_stock && <p className="text-xs font-medium text-red-600">Exceeds stock ({item.available_quantity} left)</p>}
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>

        {/* Summary */}
        <div>
          <Card>
            <CardHeader title="Order summary" />
            <CardBody className="space-y-3 text-sm">
              <div className="flex justify-between text-brand-600">
                <span>Subtotal</span>
                <span className="font-medium">{formatCurrency(cart.subtotal)}</span>
              </div>
              {cart.discount_total > 0 && (
                <div className="flex justify-between text-emerald-600">
                  <span className="flex items-center gap-1">
                    <Tag className="h-3.5 w-3.5" aria-hidden />
                    {cart.coupon?.code}
                    <button onClick={() => removeCoupon.mutate()} className="ml-1 text-xs underline hover:no-underline" aria-label="Remove coupon">
                      remove
                    </button>
                  </span>
                  <span className="font-medium">−{formatCurrency(cart.discount_total)}</span>
                </div>
              )}
              <div className="flex justify-between text-brand-600">
                <span>Shipping</span>
                <span className="font-medium">{cart.shipping_fee === 0 ? "Free" : formatCurrency(cart.shipping_fee)}</span>
              </div>
              {cart.tax_total > 0 && (
                <div className="flex justify-between text-brand-600">
                  <span>Tax</span>
                  <span className="font-medium">{formatCurrency(cart.tax_total)}</span>
                </div>
              )}
              <div className="flex justify-between border-t border-brand-100 pt-3 text-base font-bold text-brand-950">
                <span>Total</span>
                <span>{formatCurrency(cart.total)}</span>
              </div>

              {!cart.coupon && (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (couponCode.trim()) applyCoupon.mutate();
                  }}
                  className="flex gap-2 pt-2"
                >
                  <input
                    value={couponCode}
                    onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                    placeholder="Coupon code"
                    className="h-9 flex-1 rounded-lg border border-brand-200 px-3 text-sm uppercase focus:outline-none focus:ring-2 focus:ring-brand-500/30"
                    aria-label="Coupon code"
                  />
                  <Button type="submit" variant="outline" size="sm" loading={applyCoupon.isPending}>
                    Apply
                  </Button>
                </form>
              )}

              <Button
                className="w-full"
                size="lg"
                disabled={outOfStockItems.length > 0}
                onClick={() => navigate("/checkout")}
              >
                Proceed to checkout
              </Button>
              <Link to="/books" className="block text-center text-xs text-brand-400 hover:text-brand-700">
                Continue shopping
              </Link>
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------- guest */

function GuestCartContent({ navigate }: { navigate: NavigateFunction }) {
  const items = useGuestCart((s) => s.items);
  const setQuantity = useGuestCart((s) => s.setQuantity);
  const removeItem = useGuestCart((s) => s.removeItem);

  // Product details for the locally stored ids; the catalog is small enough
  // that one cached page covers it.
  const { data: books, isLoading } = useQuery({
    queryKey: ["books", "guest-cart"],
    queryFn: () => catalogApi.books({ page_size: 60 }).then((r) => r.data.items),
    enabled: items.length > 0,
    staleTime: 5 * 60 * 1000,
  });

  if (items.length === 0) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16">
        <EmptyState
          icon={<ShoppingBag className="h-10 w-10" aria-hidden />}
          title="Your cart is empty"
          description="Browse the shelves and add some books you love."
          action={<Button onClick={() => navigate("/books")}>Browse books</Button>}
        />
      </div>
    );
  }

  const rows = items
    .map((i) => ({ item: i, book: books?.find((b) => b.id === i.book_id) }))
    .filter((r): r is { item: typeof items[number]; book: Book } => !!r.book);
  const subtotal = rows.reduce((acc, r) => acc + r.book.effective_price * r.item.quantity, 0);
  const totalQuantity = rows.reduce((acc, r) => acc + r.item.quantity, 0);

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <h1 className="font-serif text-2xl font-bold text-brand-900 sm:text-3xl">Your cart</h1>
      <p className="mt-1 text-sm text-brand-400">
        {totalQuantity} item{totalQuantity === 1 ? "" : "s"} in your cart · saved on this device
      </p>

      {isLoading ? (
        <PageLoader label="Loading your cart…" />
      ) : (
        <div className="mt-6 grid gap-8 lg:grid-cols-[1fr_360px]">
          <div className="space-y-4">
            {rows.map(({ item, book }) => (
              <Card key={item.book_id} className="flex gap-4 p-4">
                <Link to={`/books/${book.slug}`} className="shrink-0">
                  <BookCover src={book.cover_image} alt={book.title} className="h-28 w-20 rounded-lg" />
                </Link>
                <div className="flex min-w-0 flex-1 flex-col">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <Link to={`/books/${book.slug}`} className="line-clamp-1 font-semibold text-brand-900 hover:text-brand-600">
                        {book.title}
                      </Link>
                      <p className="mt-0.5 text-sm text-brand-400">{book.authors.map((a) => a.name).join(", ")}</p>
                    </div>
                    <button
                      onClick={() => removeItem(item.book_id)}
                      className="rounded-lg p-1.5 text-brand-300 hover:bg-red-50 hover:text-red-600"
                      aria-label={`Remove ${book.title} from cart`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="mt-auto flex flex-wrap items-center justify-between gap-3 pt-3">
                    <QuantityStepper
                      value={item.quantity}
                      max={Math.max(book.available_quantity, 1)}
                      onChange={(qty) => setQuantity(item.book_id, qty)}
                    />
                    <div className="text-right">
                      <p className="font-bold text-brand-900">{formatCurrency(book.effective_price * item.quantity)}</p>
                      {book.discount_percent > 0 && (
                        <p className="text-xs text-brand-300 line-through">{formatCurrency(book.price * item.quantity)}</p>
                      )}
                      {book.available_quantity <= 0 && <p className="text-xs font-medium text-red-600">Out of stock</p>}
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          <div>
            <Card>
              <CardHeader title="Order summary" />
              <CardBody className="space-y-3 text-sm">
                <div className="flex justify-between text-brand-600">
                  <span>Estimated subtotal</span>
                  <span className="font-medium">{formatCurrency(subtotal)}</span>
                </div>
                <p className="text-xs text-brand-400">
                  Coupons, shipping and taxes are calculated at checkout once you sign in.
                </p>
                <Button className="w-full" size="lg" onClick={() => navigate("/login", { state: { from: "/cart" } })}>
                  Sign in to check out
                </Button>
                <p className="text-center text-xs text-brand-400">Your cart will be waiting in your account.</p>
                <Link to="/books" className="block text-center text-xs text-brand-400 hover:text-brand-700">
                  Continue shopping
                </Link>
              </CardBody>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
