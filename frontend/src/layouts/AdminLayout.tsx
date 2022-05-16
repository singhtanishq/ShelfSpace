import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard, BookOpen, Boxes, Tags, ClipboardList, RefreshCcw,
  Users, Ticket, MessageSquare, Settings, ScrollText, ArrowLeft,
} from "lucide-react";
import { cn } from "@/utils";

const LINKS = [
  { to: "/admin", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/admin/orders", label: "Orders", icon: ClipboardList },
  { to: "/admin/returns", label: "Returns", icon: RefreshCcw },
  { to: "/admin/books", label: "Books", icon: BookOpen },
  { to: "/admin/inventory", label: "Inventory", icon: Boxes },
  { to: "/admin/terms", label: "Taxonomy", icon: Tags },
  { to: "/admin/users", label: "Users", icon: Users },
  { to: "/admin/coupons", label: "Coupons", icon: Ticket },
  { to: "/admin/reviews", label: "Reviews", icon: MessageSquare },
  { to: "/admin/settings", label: "Settings", icon: Settings },
  { to: "/admin/audit", label: "Audit log", icon: ScrollText },
];

export function AdminLayout() {
  return (
    <div className="flex min-h-screen bg-brand-50/50">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r border-brand-100 bg-white lg:flex">
        <div className="flex h-16 items-center gap-2 border-b border-brand-100 px-5">
          <span className="font-serif text-lg font-bold text-brand-800">ShelfSpace</span>
          <span className="rounded bg-brand-700 px-1.5 py-0.5 text-[10px] font-bold uppercase text-white">Admin</span>
        </div>
        <nav className="flex-1 space-y-0.5 overflow-y-auto p-3" aria-label="Admin">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={"end" in link ? (link.end as boolean) : false}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive ? "bg-brand-700 text-white" : "text-brand-600 hover:bg-brand-50"
                )
              }
            >
              <link.icon className="h-4 w-4 shrink-0" aria-hidden />
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-brand-100 p-3">
          <NavLink
            to="/"
            className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-brand-500 hover:bg-brand-50"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden /> Back to store
          </NavLink>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col lg:pl-60">
        {/* Mobile nav */}
        <div className="sticky top-0 z-30 flex gap-1.5 overflow-x-auto border-b border-brand-100 bg-white px-4 py-2.5 lg:hidden">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={"end" in link ? (link.end as boolean) : false}
              className={({ isActive }) =>
                cn(
                  "whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-medium",
                  isActive ? "bg-brand-700 text-white" : "bg-brand-50 text-brand-600"
                )
              }
            >
              {link.label}
            </NavLink>
          ))}
        </div>
        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
