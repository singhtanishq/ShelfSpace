import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Heart, ShoppingBag, CheckCircle2, Truck, RotateCcw } from "lucide-react";
import { toast } from "sonner";
import { catalogApi, cartApi, wishlistApi } from "@/api/endpoints";
import { BookGrid, BookCover } from "@/components/books/BookCard";
import { StarRating, QuantityStepper, Pagination } from "@/components/ui/misc";
import { SectionHeader } from "@/components/books/BookCard";
import { Badge } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { EmptyState, PageLoader } from "@/components/ui/states";
import { useAuthStore } from "@/stores/auth";
import { useGuestCart } from "@/stores/guestCart";
import { formatCurrency, formatDate } from "@/utils";
import type { Review } from "@/types/api";

export function BookDetailPage() {
  const { slug = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user, accessToken } = useAuthStore();
  const addItem = useGuestCart((s) => s.addItem);
  const [quantity, setQuantity] = useState(1);
  const [reviewsPage, setReviewsPage] = useState(1);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewTitle, setReviewTitle] = useState("");
  const [reviewContent, setReviewContent] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const { data: book, isLoading, isError } = useQuery({
    queryKey: ["book", slug],
    queryFn: () => catalogApi.book(slug).then((r) => r.data),
  });

  const { data: related } = useQuery({
    queryKey: ["book-related", slug],
    queryFn: () => catalogApi.related(slug).then((r) => r.data),
    enabled: !!book,
  });

  const { data: reviews } = useQuery({
    queryKey: ["book-reviews", slug, reviewsPage],
    queryFn: () => catalogApi.reviews(slug, { page: reviewsPage }).then((r) => r.data),
    enabled: !!book,
  });

  const { data: wishlist } = useQuery({
    queryKey: ["wishlist"],
    queryFn: () => wishlistApi.list().then((r) => r.data),
    enabled: !!accessToken,
  });

  if (isLoading) return <PageLoader label="Fetching the book…" />;
  if (isError || !book)
    return (
      <div className="mx-auto max-w-3xl px-4 py-16">
        <EmptyState
          title="Book not found"
          description="It may have been removed from the catalog."
          action={<Button onClick={() => navigate("/books")}>Back to browse</Button>}
        />
      </div>
    );

  const outOfStock = book.available_quantity <= 0;
  const inWishlist = wishlist?.some((w) => w.book_id === book.id);
  const relatedBooks = [...(related?.related ?? []), ...(related?.by_same_author ?? [])].slice(0, 5);
  const myReview = reviews?.items.find((r) => r.user_id === user?.id);

  const onAddToCart = async () => {
    if (!accessToken) {
      for (let i = 0; i < quantity; i++) addItem(book.id, 1);
      toast.success(`Added ${quantity} copy to your cart`);
      return;
    }
    try {
      await cartApi.addItem(book.id, quantity);
      toast.success(`Added ${quantity} copy to your cart`);
      queryClient.invalidateQueries({ queryKey: ["cart"] });
    } catch (err: any) {
      toast.error(err?.response?.data?.error?.message ?? "Could not add to cart");
    }
  };

  const onToggleWishlist = async () => {
    if (!accessToken) {
      toast.info("Sign in to save books to your wishlist");
      navigate("/login", { state: { from: `/books/${slug}` } });
      return;
    }
    try {
      if (inWishlist) {
        await wishlistApi.remove(book.id);
        toast.success("Removed from wishlist");
      } else {
        await wishlistApi.add(book.id);
        toast.success("Saved to wishlist");
      }
      queryClient.invalidateQueries({ queryKey: ["wishlist"] });
    } catch (err: any) {
      toast.error(err?.response?.data?.error?.message ?? "Could not update wishlist");
    }
  };

  const submitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (myReview) {
        await catalogApi.updateReview(myReview.id, { rating: reviewRating, title: reviewTitle, content: reviewContent });
        toast.success("Your review has been updated");
      } else {
        await catalogApi.createReview(slug, { rating: reviewRating, title: reviewTitle, content: reviewContent });
        toast.success("Thanks for sharing your thoughts!");
      }
      setShowReviewForm(false);
      queryClient.invalidateQueries({ queryKey: ["book-reviews", slug] });
      queryClient.invalidateQueries({ queryKey: ["book", slug] });
    } catch (err: any) {
      toast.error(err?.response?.data?.error?.message ?? "Could not submit review");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      {/* Breadcrumb */}
      <nav className="mb-6 text-sm text-brand-400" aria-label="Breadcrumb">
        <Link to="/books" className="hover:text-brand-700">Books</Link>
        {book.categories[0] && (
          <>
            <span className="mx-2">/</span>
            <Link to={`/books?category=${book.categories[0].slug}`} className="hover:text-brand-700">
              {book.categories[0].name}
            </Link>
          </>
        )}
        <span className="mx-2">/</span>
        <span className="text-brand-700">{book.title}</span>
      </nav>

      <div className="grid gap-10 lg:grid-cols-[380px_1fr]">
        {/* Cover */}
        <div className="mx-auto w-full max-w-sm">
          <div className="overflow-hidden rounded-2xl shadow-card-hover">
            <BookCover src={book.cover_image} alt={book.title} className="aspect-[2/3] w-full" />
          </div>
        </div>

        {/* Info */}
        <div>
          <div className="flex flex-wrap gap-2">
            {book.categories.map((c) => (
              <Link key={c.id} to={`/books?category=${c.slug}`}>
                <Badge tone="info">{c.name}</Badge>
              </Link>
            ))}
          </div>
          <h1 className="mt-3 font-serif text-3xl font-bold text-brand-950 sm:text-4xl">{book.title}</h1>
          <p className="mt-2 text-lg text-brand-500">
            by{" "}
            {book.authors.map((a, i) => (
              <span key={a.id}>
                {i > 0 && ", "}
                <Link to={`/books?author=${a.slug}`} className="font-medium text-brand-700 hover:text-brand-900 hover:underline">
                  {a.name}
                </Link>
              </span>
            ))}
          </p>
          <div className="mt-3">
            <StarRating rating={book.rating_avg} count={book.rating_count} size="md" />
          </div>

          <div className="mt-5 flex items-baseline gap-3">
            <span className="text-3xl font-bold text-brand-950">{formatCurrency(book.effective_price)}</span>
            {book.discount_percent > 0 && (
              <>
                <span className="text-lg text-brand-300 line-through">{formatCurrency(book.price)}</span>
                <Badge tone="danger">Save {Math.round(book.discount_percent)}%</Badge>
              </>
            )}
          </div>

          <div className="mt-2 text-sm">
            {outOfStock ? (
              <span className="font-medium text-red-600">Currently out of stock</span>
            ) : book.available_quantity <= 5 ? (
              <span className="font-medium text-amber-600">Only {book.available_quantity} left in stock — order soon</span>
            ) : (
              <span className="inline-flex items-center gap-1.5 font-medium text-emerald-600">
                <CheckCircle2 className="h-4 w-4" aria-hidden /> In stock, ready to ship
              </span>
            )}
          </div>

          {/* Actions */}
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <QuantityStepper value={quantity} onChange={setQuantity} max={Math.max(1, book.available_quantity)} disabled={outOfStock} />
            <Button size="lg" onClick={onAddToCart} loading={false} disabled={outOfStock}>
              <ShoppingBag className="h-5 w-5" aria-hidden /> Add to cart
            </Button>
            <Button size="lg" variant="outline" onClick={onToggleWishlist} aria-pressed={inWishlist}>
              <Heart className={`h-5 w-5 ${inWishlist ? "fill-red-500 text-red-500" : ""}`} aria-hidden />
              {inWishlist ? "Wishlisted" : "Wishlist"}
            </Button>
          </div>

          {/* Assurances */}
          <div className="mt-6 grid gap-3 rounded-xl border border-brand-100 bg-white p-4 text-sm text-brand-600 sm:grid-cols-3">
            <span className="flex items-center gap-2"><Truck className="h-4 w-4 text-brand-400" aria-hidden /> Delivered in 3–7 days</span>
            <span className="flex items-center gap-2"><RotateCcw className="h-4 w-4 text-brand-400" aria-hidden /> 14-day easy returns</span>
            <span className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-brand-400" aria-hidden /> 100% genuine copies</span>
          </div>

          {/* Meta */}
          <dl className="mt-6 space-y-2 border-t border-brand-100 pt-5 text-sm">
            {book.publisher && (
              <div className="flex gap-2">
                <dt className="w-32 shrink-0 text-brand-400">Publisher</dt>
                <dd className="text-brand-800">{book.publisher.name}</dd>
              </div>
            )}
            {"isbn" in book && (book as any).isbn && (
              <div className="flex gap-2">
                <dt className="w-32 shrink-0 text-brand-400">ISBN</dt>
                <dd className="text-brand-800">{(book as any).isbn}</dd>
              </div>
            )}
            {(book as any).published_year && (
              <div className="flex gap-2">
                <dt className="w-32 shrink-0 text-brand-400">Published</dt>
                <dd className="text-brand-800">{(book as any).published_year}</dd>
              </div>
            )}
            {(book as any).pages && (
              <div className="flex gap-2">
                <dt className="w-32 shrink-0 text-brand-400">Pages</dt>
                <dd className="text-brand-800">{(book as any).pages}</dd>
              </div>
            )}
            {(book as any).language && (
              <div className="flex gap-2">
                <dt className="w-32 shrink-0 text-brand-400">Language</dt>
                <dd className="text-brand-800">{(book as any).language}</dd>
              </div>
            )}
          </dl>

          {(book as any).description && (
            <div className="mt-6 border-t border-brand-100 pt-5">
              <h2 className="font-serif text-lg font-bold text-brand-900">About this book</h2>
              <p className="mt-2 leading-relaxed text-brand-600">{(book as any).description}</p>
            </div>
          )}
        </div>
      </div>

      {/* Reviews */}
      <section className="mt-14">
        <SectionHeader
          title="Reader reviews"
          subtitle={reviews ? `${reviews.total} review${reviews.total === 1 ? "" : "s"}` : undefined}
          action={
            accessToken &&
            (myReview ? (
              <Button variant="outline" size="sm" onClick={() => {
                setReviewRating(myReview.rating);
                setReviewTitle(myReview.title ?? "");
                setReviewContent(myReview.content);
                setShowReviewForm(true);
              }}>
                Edit your review
              </Button>
            ) : (
              <Button size="sm" onClick={() => setShowReviewForm(true)}>
                Write a review
              </Button>
            ))
          }
        />

        {showReviewForm && (
          <form onSubmit={submitReview} className="mb-8 space-y-4 rounded-xl border border-brand-100 bg-white p-5 shadow-card">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-brand-900">Your rating</label>
              <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setReviewRating(star)}
                    className={`text-2xl leading-none transition-transform hover:scale-110 ${star <= reviewRating ? "text-accent-500" : "text-brand-200"}`}
                    aria-label={`${star} star${star > 1 ? "s" : ""}`}
                  >
                    ★
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-brand-900">Headline <span className="text-brand-300">(optional)</span></label>
              <input
                value={reviewTitle}
                onChange={(e) => setReviewTitle(e.target.value)}
                className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
                placeholder="Sum up your experience"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-brand-900">Your review</label>
              <textarea
                value={reviewContent}
                onChange={(e) => setReviewContent(e.target.value)}
                required
                minLength={3}
                rows={4}
                className="w-full rounded-lg border border-brand-200 p-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
                placeholder="What did you think of the book?"
              />
            </div>
            <div className="flex gap-2">
              <Button type="submit" loading={submitting}>{myReview ? "Update review" : "Submit review"}</Button>
              <Button type="button" variant="ghost" onClick={() => setShowReviewForm(false)}>Cancel</Button>
            </div>
          </form>
        )}

        {reviews && reviews.items.length === 0 ? (
          <EmptyState title="No reviews yet" description="Be the first to share your thoughts on this book." />
        ) : (
          <div className="space-y-5">
            {reviews?.items.map((review) => <ReviewCard key={review.id} review={review} />)}
            {reviews && reviews.pages > 1 && (
              <Pagination page={reviews.page} pages={reviews.pages} onChange={setReviewsPage} />
            )}
          </div>
        )}
      </section>

      {/* Related */}
      {relatedBooks.length > 0 && (
        <section className="mt-14">
          <SectionHeader title="You might also like" />
          <BookGrid books={relatedBooks} />
        </section>
      )}
    </div>
  );
}

function ReviewCard({ review }: { review: Review }) {
  return (
    <article className="rounded-xl border border-brand-100 bg-white p-5 shadow-card">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 text-sm font-semibold text-brand-700">
              {review.author_name.charAt(0)}
            </span>
            <div>
              <p className="text-sm font-semibold text-brand-900">{review.author_name}</p>
              <p className="text-xs text-brand-400">{formatDate(review.created_at)}</p>
            </div>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <StarRating rating={review.rating} />
          {review.is_verified_purchase && (
            <Badge tone="success">
              <CheckCircle2 className="h-3 w-3" aria-hidden /> Verified purchase
            </Badge>
          )}
        </div>
      </div>
      {review.title && <h3 className="mt-3 text-sm font-semibold text-brand-900">{review.title}</h3>}
      <p className="mt-1.5 text-sm leading-relaxed text-brand-600">{review.content}</p>
    </article>
  );
}
