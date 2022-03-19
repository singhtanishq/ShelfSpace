import { useMemo, useState } from "react";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { SearchX, SlidersHorizontal, X } from "lucide-react";
import { catalogApi, type BookQuery } from "@/api/endpoints";
import { BookGrid } from "@/components/books/BookCard";
import { Pagination } from "@/components/ui/misc";
import { EmptyState, ErrorState } from "@/components/ui/states";
import { Button } from "@/components/ui/Button";
import { formatCurrency } from "@/utils";
import type { Facets } from "@/types/api";
import { cn } from "@/utils";

const SORTS = [
  { value: "popularity", label: "Most popular" },
  { value: "newest", label: "Newest first" },
  { value: "price_asc", label: "Price: low to high" },
  { value: "price_desc", label: "Price: high to low" },
  { value: "rating", label: "Highest rated" },
  { value: "title", label: "Title A–Z" },
];

export function CatalogPage() {
  const [params, setParams] = useSearchParams();
  const [showFilters, setShowFilters] = useState(false);

  const query: BookQuery = useMemo(
    () => ({
      q: params.get("q") ?? undefined,
      category: params.get("category") ?? undefined,
      author: params.get("author") ?? undefined,
      language: params.get("language") ?? undefined,
      min_price: params.get("min_price") ? Number(params.get("min_price")) : undefined,
      max_price: params.get("max_price") ? Number(params.get("max_price")) : undefined,
      min_rating: params.get("min_rating") ? Number(params.get("min_rating")) : undefined,
      in_stock: params.get("in_stock") === "1" || undefined,
      sort: params.get("sort") ?? "popularity",
      page: params.get("page") ? Number(params.get("page")) : 1,
      page_size: 12,
    }),
    [params]
  );

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["books", query],
    queryFn: () => catalogApi.books(query).then((r) => r.data),
    placeholderData: keepPreviousData,
  });

  const { data: facets } = useQuery({
    queryKey: ["facets"],
    queryFn: () => catalogApi.facets().then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  });

  const setParam = (key: string, value?: string) => {
    const next = new URLSearchParams(params);
    if (value === undefined || value === "") next.delete(key);
    else next.set(key, value);
    if (key !== "page") next.delete("page");
    setParams(next);
  };

  const activeFilters = ["category", "author", "language", "min_price", "max_price", "min_rating", "in_stock", "q"]
    .filter((k) => params.get(k))
    .map((k) => ({ key: k, value: params.get(k)! }));

  const activeCategory = facets?.categories.find((c) => c.slug === params.get("category"));
  const activeAuthor = facets?.authors.find((a) => a.slug === params.get("author"));

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-serif text-2xl font-bold text-brand-900 sm:text-3xl">
            {params.get("q") ? `Results for “${params.get("q")}”` : activeCategory ? activeCategory.name : activeAuthor ? activeAuthor.name : "All books"}
          </h1>
          {data && <p className="mt-1 text-sm text-brand-400">{data.total} titles available</p>}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="lg:hidden" onClick={() => setShowFilters(!showFilters)}>
            <SlidersHorizontal className="h-4 w-4" aria-hidden /> Filters
          </Button>
          <select
            value={query.sort}
            onChange={(e) => setParam("sort", e.target.value)}
            className="h-9 rounded-lg border border-brand-200 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
            aria-label="Sort books"
          >
            {SORTS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {activeFilters.length > 0 && (
        <div className="mb-4 flex flex-wrap items-center gap-2">
          {activeFilters.map((f) => (
            <button
              key={f.key}
              onClick={() => setParam(f.key)}
              className="inline-flex items-center gap-1 rounded-full bg-brand-100 px-3 py-1 text-xs font-medium text-brand-800 hover:bg-brand-200"
            >
              {f.key === "in_stock" ? "In stock only" : `${f.key.replace("_", " ")}: ${f.value}`}
              <X className="h-3 w-3" aria-hidden />
            </button>
          ))}
          <button onClick={() => setParams(new URLSearchParams())} className="text-xs font-medium text-brand-500 underline hover:text-brand-800">
            Clear all
          </button>
        </div>
      )}

      <div className="flex gap-8">
        {/* Filters sidebar */}
        <aside className={cn("w-64 shrink-0 space-y-6", showFilters ? "block" : "hidden lg:block")}>
          <FilterSection title="Category">
            <ul className="space-y-1.5">
              <li>
                <button onClick={() => setParam("category")} className={cn("text-sm", !query.category ? "font-semibold text-brand-800" : "text-brand-500 hover:text-brand-800")}>
                  All categories
                </button>
              </li>
              {facets?.categories.map((cat) => (
                <li key={cat.id}>
                  <button
                    onClick={() => setParam("category", cat.slug)}
                    className={cn("text-left text-sm", query.category === cat.slug ? "font-semibold text-brand-800" : "text-brand-500 hover:text-brand-800")}
                  >
                    {cat.name}
                  </button>
                </li>
              ))}
            </ul>
          </FilterSection>

          <FilterSection title="Author">
            <AuthorFilter facets={facets} value={query.author} onChange={(v) => setParam("author", v)} />
          </FilterSection>

          <FilterSection title="Price">
            <div className="flex items-center gap-2">
              <input
                type="number"
                placeholder="Min"
                value={params.get("min_price") ?? ""}
                onChange={(e) => setParam("min_price", e.target.value)}
                className="h-9 w-full rounded-lg border border-brand-200 px-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
                aria-label="Minimum price"
              />
              <span className="text-brand-300">–</span>
              <input
                type="number"
                placeholder="Max"
                value={params.get("max_price") ?? ""}
                onChange={(e) => setParam("max_price", e.target.value)}
                className="h-9 w-full rounded-lg border border-brand-200 px-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
                aria-label="Maximum price"
              />
            </div>
            {facets && (
              <p className="mt-2 text-xs text-brand-400">
                Catalog range: {formatCurrency(facets.price_min)} – {formatCurrency(facets.price_max)}
              </p>
            )}
          </FilterSection>

          <FilterSection title="Rating">
            {[4, 3, 2].map((r) => (
              <button
                key={r}
                onClick={() => setParam("min_rating", query.min_rating === r ? undefined : String(r))}
                className={cn("block text-sm", query.min_rating === r ? "font-semibold text-brand-800" : "text-brand-500 hover:text-brand-800")}
              >
                {"★".repeat(r)}{"☆".repeat(5 - r)} & up
              </button>
            ))}
          </FilterSection>

          <FilterSection title="Availability">
            <label className="flex items-center gap-2 text-sm text-brand-600">
              <input
                type="checkbox"
                checked={query.in_stock === true}
                onChange={(e) => setParam("in_stock", e.target.checked ? "1" : undefined)}
                className="h-4 w-4 rounded border-brand-300 text-brand-700 focus:ring-brand-500"
              />
              In stock only
            </label>
          </FilterSection>
        </aside>

        {/* Results */}
        <div className="min-w-0 flex-1">
          {isError ? (
            <ErrorState message="We couldn't load the catalog. Please try again." onRetry={() => refetch()} />
          ) : isLoading ? (
            <BookGrid loading skeletonCount={10} />
          ) : !data || data.items.length === 0 ? (
            <EmptyState
              icon={<SearchX className="h-10 w-10" aria-hidden />}
              title="No books match your filters"
              description="Try adjusting your search or clearing some filters to see more results."
              action={
                <Button variant="outline" size="sm" onClick={() => setParams(new URLSearchParams())}>
                  Clear filters
                </Button>
              }
            />
          ) : (
            <>
              <BookGrid books={data.items} />
              <Pagination page={data.page} pages={data.pages} onChange={(p) => setParam("page", String(p))} className="mt-10" />
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function FilterSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-brand-400">{title}</h3>
      {children}
    </div>
  );
}

function AuthorFilter({ facets, value, onChange }: { facets?: Facets; value?: string; onChange: (v?: string) => void }) {
  const [term, setTerm] = useState("");
  const authors = facets?.authors.filter((a) => a.name.toLowerCase().includes(term.toLowerCase())).slice(0, 8) ?? [];
  return (
    <div className="space-y-2">
      <input
        value={term}
        onChange={(e) => setTerm(e.target.value)}
        placeholder="Find author…"
        className="h-9 w-full rounded-lg border border-brand-200 px-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
        aria-label="Filter by author"
      />
      <ul className="space-y-1.5">
        <li>
          <button onClick={() => onChange(undefined)} className={cn("text-sm", !value ? "font-semibold text-brand-800" : "text-brand-500 hover:text-brand-800")}>
            All authors
          </button>
        </li>
        {authors.map((a) => (
          <li key={a.id}>
            <button
              onClick={() => onChange(a.slug === value ? undefined : a.slug)}
              className={cn("text-left text-sm", value === a.slug ? "font-semibold text-brand-800" : "text-brand-500 hover:text-brand-800")}
            >
              {a.name}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
