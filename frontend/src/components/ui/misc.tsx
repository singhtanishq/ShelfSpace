import { ChevronLeft, ChevronRight, Star, StarHalf } from "lucide-react";
import { cn } from "@/utils";

export function StarRating({
  rating,
  count,
  size = "sm",
}: {
  rating: number;
  count?: number;
  size?: "sm" | "md";
}) {
  const dimension = size === "sm" ? "h-3.5 w-3.5" : "h-5 w-5";
  const full = Math.floor(rating);
  const half = rating - full >= 0.25 && rating - full < 0.75;
  const rounded = half ? full + 0.5 : Math.round(rating);

  return (
    <span className="inline-flex items-center gap-1" aria-label={`Rated ${rounded} out of 5${count !== undefined ? ` by ${count} readers` : ""}`}>
      <span className="flex text-accent-500">
        {[1, 2, 3, 4, 5].map((i) => {
          if (i <= full) return <Star key={i} className={cn(dimension, "fill-accent-500")} />;
          if (half && i === full + 1) return <StarHalf key={i} className={cn(dimension, "fill-accent-500")} />;
          return <Star key={i} className={cn(dimension, "text-brand-200")} />;
        })}
      </span>
      {count !== undefined && <span className="text-xs text-brand-400">({count})</span>}
    </span>
  );
}

export function Pagination({
  page,
  pages,
  onChange,
  className,
}: {
  page: number;
  pages: number;
  onChange: (page: number) => void;
  className?: string;
}) {
  if (pages <= 1) return null;
  const window = 2;
  const items: (number | "…")[] = [];
  for (let i = 1; i <= pages; i++) {
    if (i === 1 || i === pages || (i >= page - window && i <= page + window)) {
      items.push(i);
    } else if (items[items.length - 1] !== "…") {
      items.push("…");
    }
  }

  return (
    <nav className={cn("flex items-center justify-center gap-1", className)} aria-label="Pagination">
      <button
        className="rounded-lg p-2 text-brand-600 hover:bg-brand-50 disabled:opacity-40"
        onClick={() => onChange(page - 1)}
        disabled={page <= 1}
        aria-label="Previous page"
      >
        <ChevronLeft className="h-4 w-4" />
      </button>
      {items.map((item, idx) =>
        item === "…" ? (
          <span key={`gap-${idx}`} className="px-1 text-brand-300">
            …
          </span>
        ) : (
          <button
            key={item}
            onClick={() => onChange(item)}
            aria-current={item === page ? "page" : undefined}
            className={cn(
              "h-8 w-8 rounded-lg text-sm font-medium",
              item === page ? "bg-brand-700 text-white" : "text-brand-700 hover:bg-brand-50"
            )}
          >
            {item}
          </button>
        )
      )}
      <button
        className="rounded-lg p-2 text-brand-600 hover:bg-brand-50 disabled:opacity-40"
        onClick={() => onChange(page + 1)}
        disabled={page >= pages}
        aria-label="Next page"
      >
        <ChevronRight className="h-4 w-4" />
      </button>
    </nav>
  );
}

export function QuantityStepper({
  value,
  onChange,
  max = 99,
  disabled,
}: {
  value: number;
  onChange: (value: number) => void;
  max?: number;
  disabled?: boolean;
}) {
  return (
    <div className="inline-flex items-center rounded-lg border border-brand-200" role="group" aria-label="Quantity">
      <button
        className="h-8 w-8 text-brand-600 hover:bg-brand-50 disabled:opacity-40"
        onClick={() => onChange(Math.max(1, value - 1))}
        disabled={disabled || value <= 1}
        aria-label="Decrease quantity"
      >
        −
      </button>
      <span className="w-8 text-center text-sm font-medium tabular-nums">{value}</span>
      <button
        className="h-8 w-8 text-brand-600 hover:bg-brand-50 disabled:opacity-40"
        onClick={() => onChange(Math.min(max, value + 1))}
        disabled={disabled || value >= max}
        aria-label="Increase quantity"
      >
        +
      </button>
    </div>
  );
}
