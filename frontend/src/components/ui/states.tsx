import type { ReactNode } from "react";
import { Loader2, PackageOpen, RefreshCw } from "lucide-react";
import { Button } from "./Button";
import { cn } from "@/utils";

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn("h-5 w-5 animate-spin text-brand-500", className)} aria-label="Loading" />;
}

export function PageLoader({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-24 text-brand-400">
      <Loader2 className="h-8 w-8 animate-spin" aria-hidden />
      <p className="text-sm">{label}</p>
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-lg bg-brand-100/70", className)} aria-hidden />;
}

export function BookCardSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="aspect-[2/3] w-full" />
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-4 w-1/2" />
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-brand-200 bg-brand-50/40 px-6 py-16 text-center">
      <div className="text-brand-300">{icon ?? <PackageOpen className="h-10 w-10" aria-hidden />}</div>
      <h3 className="text-base font-semibold text-brand-800">{title}</h3>
      {description && <p className="max-w-sm text-sm text-brand-400">{description}</p>}
      {action}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-red-100 bg-red-50/60 px-6 py-14 text-center">
      <h3 className="text-base font-semibold text-red-800">Something went wrong</h3>
      <p className="max-w-sm text-sm text-red-600">{message}</p>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          <RefreshCw className="h-4 w-4" aria-hidden /> Try again
        </Button>
      )}
    </div>
  );
}
