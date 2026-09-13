import { useEffect, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import { cn } from "@/utils";

export function Modal({
  open,
  onClose,
  title,
  children,
  size = "md",
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  size?: "md" | "lg";
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center" role="dialog" aria-modal="true" aria-label={title}>
      <div className="absolute inset-0 bg-brand-950/40 backdrop-blur-sm" onClick={onClose} aria-hidden />
      <div
        className={cn(
          "relative max-h-[90vh] w-full overflow-y-auto rounded-t-2xl bg-white shadow-xl animate-fade-in-up sm:rounded-2xl",
          size === "md" ? "sm:max-w-lg" : "sm:max-w-2xl"
        )}
      >
        <div className="sticky top-0 flex items-center justify-between border-b border-brand-50 bg-white px-5 py-4">
          <h2 className="text-base font-semibold text-brand-900">{title}</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-brand-400 hover:bg-brand-50 hover:text-brand-700"
            aria-label="Close dialog"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="px-5 py-4">{children}</div>
      </div>
    </div>,
    document.body
  );
}
