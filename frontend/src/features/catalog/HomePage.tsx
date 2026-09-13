import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ArrowRight, BookOpen, ShieldCheck, Truck, RefreshCcw, Sparkles } from "lucide-react";
import { catalogApi } from "@/api/endpoints";
import { BookGrid, SectionHeader } from "@/components/books/BookCard";
import { Button } from "@/components/ui/Button";
import { PageLoader } from "@/components/ui/states";

const PERKS = [
  { icon: Truck, title: "Free delivery", text: "On eligible orders across India" },
  { icon: ShieldCheck, title: "Genuine copies", text: "Sourced from authorised distributors" },
  { icon: RefreshCcw, title: "14-day returns", text: "Hassle-free returns & replacements" },
  { icon: BookOpen, title: "Curated shelves", text: "Hand-picked by real readers" },
];

export function HomePage() {
  const { data, isLoading } = useQuery({ queryKey: ["home"], queryFn: () => catalogApi.home().then((r) => r.data) });

  if (isLoading || !data) return <PageLoader label="Opening the shop…" />;

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden bg-brand-950 text-white">
        <div className="absolute inset-0 opacity-20" aria-hidden>
          <div className="absolute -left-20 -top-20 h-96 w-96 rounded-full bg-brand-500 blur-3xl" />
          <div className="absolute -right-20 bottom-0 h-96 w-96 rounded-full bg-accent-600 blur-3xl" />
        </div>
        <div className="relative mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-28">
          <div className="max-w-2xl">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-accent-300">
              <Sparkles className="h-3.5 w-3.5" aria-hidden /> Over 10,000 happy readers
            </span>
            <h1 className="mt-5 font-serif text-4xl font-bold leading-tight sm:text-6xl">
              Every great story <span className="text-accent-400">finds its reader.</span>
            </h1>
            <p className="mt-5 max-w-xl text-base leading-relaxed text-brand-200 sm:text-lg">
              ShelfSpace brings a carefully curated bookstore to your screen — bestsellers, hidden gems and
              timeless classics, delivered to your door with genuine care.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button size="lg" variant="secondary" onClick={() => (window.location.href = "/books")}>
                Browse the shelves <ArrowRight className="h-4 w-4" aria-hidden />
              </Button>
              <Button size="lg" variant="outline" className="border-white/30 bg-transparent text-white hover:bg-white/10" onClick={() => (window.location.href = "/books?sort=rating")}>
                Top rated books
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Perks */}
      <section className="border-b border-brand-100 bg-white">
        <div className="mx-auto grid max-w-7xl grid-cols-2 gap-6 px-4 py-8 sm:px-6 lg:grid-cols-4">
          {PERKS.map((perk) => (
            <div key={perk.title} className="flex items-start gap-3">
              <div className="rounded-lg bg-brand-50 p-2.5 text-brand-700">
                <perk.icon className="h-5 w-5" aria-hidden />
              </div>
              <div>
                <p className="text-sm font-semibold text-brand-900">{perk.title}</p>
                <p className="text-xs text-brand-400">{perk.text}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <div className="mx-auto max-w-7xl space-y-14 px-4 py-12 sm:px-6">
        {/* Categories */}
        <section>
          <SectionHeader title="Browse by category" subtitle="Find the shelf that fits your mood" />
          <div className="flex flex-wrap gap-2.5">
            {data.categories.map((cat) => (
              <Link
                key={cat.id}
                to={`/books?category=${cat.slug}`}
                className="rounded-full border border-brand-200 bg-white px-4 py-2 text-sm font-medium text-brand-700 shadow-sm transition-all hover:-translate-y-0.5 hover:border-brand-400 hover:shadow"
              >
                {cat.name}
              </Link>
            ))}
          </div>
        </section>

        {/* Featured */}
        {data.featured.length > 0 && (
          <section>
            <SectionHeader
              title="Featured this week"
              subtitle="Hand-picked highlights from our shelves"
              action={
                <Link to="/books" className="hidden items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-800 sm:flex">
                  View all <ArrowRight className="h-4 w-4" aria-hidden />
                </Link>
              }
            />
            <BookGrid books={data.featured.slice(0, 5)} />
          </section>
        )}

        {/* Best sellers */}
        <section>
          <SectionHeader
            title="Best sellers"
            subtitle="The books everyone is talking about"
            action={
              <Link to="/books?sort=popularity" className="hidden items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-800 sm:flex">
                View all <ArrowRight className="h-4 w-4" aria-hidden />
              </Link>
            }
          />
          <BookGrid books={data.best_sellers.slice(0, 5)} />
        </section>

        {/* Promo */}
        <section className="overflow-hidden rounded-2xl bg-gradient-to-r from-brand-800 to-brand-600 px-6 py-10 text-white sm:px-12">
          <div className="flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-center">
            <div>
              <h2 className="font-serif text-2xl font-bold sm:text-3xl">First order? Take 10% off.</h2>
              <p className="mt-2 max-w-md text-sm text-brand-100">
                Use code <span className="rounded bg-white/15 px-2 py-0.5 font-mono font-bold text-accent-300">WELCOME10</span> at
                checkout on orders above ₹500 and start your collection today.
              </p>
            </div>
            <Button size="lg" variant="secondary" onClick={() => (window.location.href = "/books")}>
              Start shopping
            </Button>
          </div>
        </section>

        {/* New arrivals */}
        <section>
          <SectionHeader
            title="New arrivals"
            subtitle="Fresh on the shelves"
            action={
              <Link to="/books?sort=newest" className="hidden items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-800 sm:flex">
                View all <ArrowRight className="h-4 w-4" aria-hidden />
              </Link>
            }
          />
          <BookGrid books={data.new_arrivals.slice(0, 5)} />
        </section>
      </div>
    </div>
  );
}
