import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/utils";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("rounded-xl border border-brand-100 bg-white shadow-card", className)}
      {...props}
    />
  );
}

export function CardHeader({ title, description, action }: { title: ReactNode; description?: ReactNode; action?: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-brand-50 px-5 py-4">
      <div>
        <h3 className="text-sm font-semibold text-brand-900">{title}</h3>
        {description && <p className="mt-0.5 text-xs text-brand-400">{description}</p>}
      </div>
      {action}
    </div>
  );
}

export function CardBody({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-5 py-4", className)} {...props} />;
}

type BadgeTone = "neutral" | "info" | "success" | "warning" | "danger" | "accent";

const tones: Record<BadgeTone, string> = {
  neutral: "bg-brand-50 text-brand-700 ring-brand-100",
  info: "bg-sky-50 text-sky-700 ring-sky-100",
  success: "bg-emerald-50 text-emerald-700 ring-emerald-100",
  warning: "bg-amber-50 text-amber-800 ring-amber-100",
  danger: "bg-red-50 text-red-700 ring-red-100",
  accent: "bg-accent-50 text-accent-700 ring-accent-200",
};

export function Badge({
  tone = "neutral",
  className,
  children,
}: {
  tone?: BadgeTone;
  className?: string;
  children: ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset",
        tones[tone],
        className
      )}
    >
      {children}
    </span>
  );
}

const STATUS_TONES: Record<string, BadgeTone> = {
  pending: "warning",
  confirmed: "info",
  processing: "info",
  shipped: "info",
  out_for_delivery: "info",
  delivered: "success",
  cancelled: "danger",
  returned: "neutral",
  requested: "warning",
  approved: "info",
  rejected: "danger",
  completed: "success",
  paid: "success",
  failed: "danger",
  refunded: "neutral",
  cod: "neutral",
  card: "info",
  upi: "accent",
  return: "warning",
  replacement: "accent",
};

export function StatusBadge({ status, className }: { status: string; className?: string }) {
  const tone = STATUS_TONES[status] ?? "neutral";
  const label = status.replaceAll("_", " ");
  return (
    <Badge tone={tone} className={cn("capitalize", className)}>
      {label}
    </Badge>
  );
}
