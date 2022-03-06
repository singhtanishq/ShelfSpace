import { Link } from "react-router-dom";
import { Heart, ShoppingBag, BookOpen } from "lucide-react";
import type { Book } from "@/types/api";
import { Badge } from "@/components/ui/Card";
import { StarRating } from "@/components/ui/misc";
import { useGuestCart } from "@/stores/guestCart";
import { useAuthStore } from "@/stores/auth";
import { cartApi, wishlistApi } from "@/api/endpoints";
import { formatCurrency, mediaUrl } from "@/utils";
import { toast } from "sonner";
import { useState } from "react";

export function BookCover({ src, alt, className }: { src?: string | null; alt: string; className?: string }) {
  const [failed, setFailed] = useState(false);
  if (!src || failed) {
    return (
      <div className={`flex items-center justify-center bg-gradient-to-br from-brand-700 to-brand-900 ${className ?? ""}`}>
        <BookOpen className="h-10 w-10 text-white/40" aria-hidden />
      </div>
    );
  }
  return (
    <img
      src={mediaUrl(src)}
      alt={alt}
      loading="lazy"
      onError={() => setFailed(true)}
      className={`object-cover ${className ?? ""}`}
    />
  );
}

export function BookCard({ book }: { book: Book }) {
  const { accessToken } = useAuthStore();
  const addItem = useGuestCart((s) => s.addItem);
  const [busy, setBusy] = useState(false);

  const onAdd = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!accessToken) {
      addItem(book.id, 1);
      toast.success(`Added "${book.title}" to your cart`);
      return;
    }
    setBusy(true);
    try {
      await cartApi.addItem(book.id, 1);
      toast.success(`Added "${book.title}" to your cart`);
    } catch (err: any) {
      toast.error(err?.response?.data?.error?.message ?? "Could not add to cart");
    } finally {
      setBusy(false);
    }
  };

  const onWishlist = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!accessToken) {
      toast.info("Sign in to save books to your wishlist");
      return;
    }
    try {
      await wishlistApi.add(book.id);
      toast.success("Saved to wishlist");
    } catch (err: any) {
      toast.error(err?.response?.data?.error?.message ?? "Could not update wishlist");
    }
  };

  const outOfStock = book.available_quantity <= 0;

  return (
    <Link
      to={`/books/${book.slug}`}
      className="group flex flex-col overflow-hidden rounded-xl border border-brand-100 bg-white shadow-card transition-all hover:-translate-y-0.5 hover:shadow-card-hover"
    >
      <div className="relative aspect-[2/3] overflow-hidden bg-brand-50">
        <BookCover src={book.cover_image} alt={book.title} className="h-full w-full transition-transform duration-300 group-hover:scale-105" />
        {book.discount_percent > 0 && (
          <span className="absolute left-2 top-2 rounded-full bg-red-600 px-2 py-0.5 text-xs font-bold text-white">
            −{Math.round(book.discount_percent)}%
          </span>
        )}
        <button
          onClick={onWishlist}
          className="absolute right-2 top-2 rounded-full bg-white/90 p-2 text-brand-500 opacity-0 shadow-sm transition-opacity hover:text-red-500 focus:opacity-100 group-hover:opacity-100"
          aria-label={`Save ${book.title} to wishlist`}
        >
          <Heart className="h-4 w-4" />
        </button>
        {outOfStock && (
          <div className="absolute inset-x-0 bottom-0 bg-brand-950/70 py-1.5 text-center text-xs font-medium text-white">
            Out of stock
          </div>
        )}
      </div>
      <div className="flex flex-1 flex-col gap-1.5 p-3.5">
        <h3 className="line-clamp-2 text-sm font-semibold leading-snug text-brand-900 group-hover:text-brand-600">
          {book.title}
        </h3>
        <p className="line-clamp-1 text-xs text-brand-400">{book.authors.map((a) => a.name).join(", ")}</p>
        <StarRating rating={book.rating_avg} count={book.rating_count} />
        <div className="mt-auto flex items-center justify-between pt-1.5">
          <div className="flex items-baseline gap-1.5">
            <span className="text-sm font-bold text-brand-900">{formatCurrency(book.effective_price)}</span>
            {book.discount_percent > 0 && (
              <span className="text-xs text-brand-300 line-through">{formatCurrency(book.price)}</span>
            )}
          </div>
          <button
            onClick={onAdd}
            disabled={busy || outOfStock}
            className="rounded-lg bg-brand-700 p-2 text-white transition-colors hover:bg-brand-600 disabled:opacity-40"
            aria-label={`Add ${book.title} to cart`}
          >
            <ShoppingBag className="h-4 w-4" />
          </button>
        </div>
      </div>
    </Link>
  );
}

export function BookGrid({ books, loading, skeletonCount = 8 }: { books?: Book[]; loading?: boolean; skeletonCount?: number }) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
        {Array.from({ length: skeletonCount }).map((_, i) => (
          <div key={i} className="space-y-3">
            <div className="aspect-[2/3] w-full animate-pulse rounded-xl bg-brand-100/70" />
            <div className="h-4 w-3/4 animate-pulse rounded bg-brand-100/70" />
            <div className="h-4 w-1/2 animate-pulse rounded bg-brand-100/70" />
          </div>
        ))}
      </div>
    );
  }
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
      {books?.map((book) => <BookCard key={book.id} book={book} />)}
    </div>
  );
}

export function SectionHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: React.ReactNode }) {
  return (
    <div className="mb-5 flex items-end justify-between gap-4">
      <div>
        <h2 className="font-serif text-xl font-bold text-brand-900 sm:text-2xl">{title}</h2>
        {subtitle && <p className="mt-1 text-sm text-brand-400">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

export function DiscountBadge({ percent }: { percent: number }) {
  if (percent <= 0) return null;
  return <Badge tone="danger">−{Math.round(percent)}%</Badge>;
}
