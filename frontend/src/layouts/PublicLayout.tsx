import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { Menu, Search, ShoppingCart, Heart, Bell, LogOut, LayoutDashboard, X, Library } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { useAuthStore } from "@/stores/auth";
import { useGuestCart } from "@/stores/guestCart";
import { authApi, cartApi, notificationsApi } from "@/api/endpoints";
import { Button } from "@/components/ui/Button";

const NAV_LINKS = [
  { to: "/", label: "Home" },
  { to: "/books", label: "Browse" },
  { to: "/about", label: "About" },
  { to: "/contact", label: "Contact" },
];

export function PublicLayout() {
  const navigate = useNavigate();
  const { user, accessToken, clearSession, getRefreshToken } = useAuthStore();
  const addItem = useGuestCart((s) => s.addItem);
  const guestItems = useGuestCart((s) => s.items);
  const [cartCount, setCartCount] = useState(0);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [search, setSearch] = useState("");

  // Server cart count for signed-in users; guest count otherwise.
  const { data: cart } = useQuery({
    queryKey: ["cart"],
    queryFn: () => cartApi.get().then((r) => r.data),
    enabled: !!accessToken,
  });
  const { data: unread } = useQuery({
    queryKey: ["notifications", "unread"],
    queryFn: () => notificationsApi.unreadCount().then((r) => r.data.count),
    enabled: !!accessToken,
    refetchInterval: 30000,
  });

  // Merge guest cart into the server cart after sign-in.
  useEffect(() => {
    if (accessToken && guestItems.length > 0) {
      cartApi
        .merge(guestItems)
        .then(() => useGuestCart.getState().clear())
        .catch(() => undefined);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken]);

  useEffect(() => {
    setCartCount(accessToken ? (cart?.total_quantity ?? 0) : guestItems.reduce((acc, i) => acc + i.quantity, 0));
  }, [accessToken, cart, guestItems]);

  const onLogout = async () => {
    try {
      const refresh = getRefreshToken();
      if (refresh) await authApi.logout(refresh);
    } catch {
      /* ignore */
    }
    clearSession();
    toast.success("Signed out. See you soon!");
    navigate("/");
  };

  const onSearch = (e: React.FormEvent) => {
    e.preventDefault();
    navigate(`/books?q=${encodeURIComponent(search)}`);
  };

  return (
    <div className="flex min-h-screen flex-col bg-brand-50/40">
      <header className="sticky top-0 z-40 border-b border-brand-100 bg-white/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center gap-4 px-4 sm:px-6">
          <button className="rounded-lg p-2 text-brand-700 hover:bg-brand-50 lg:hidden" onClick={() => setMobileOpen(!mobileOpen)} aria-label="Toggle menu">
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>

          <Link to="/" className="flex items-center gap-2">
            <Library className="h-7 w-7 text-brand-700" aria-hidden />
            <span className="font-serif text-xl font-bold text-brand-800">ShelfSpace</span>
          </Link>

          <nav className="ml-6 hidden items-center gap-1 lg:flex" aria-label="Main">
            {NAV_LINKS.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.to === "/"}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                    isActive ? "bg-brand-50 text-brand-800" : "text-brand-500 hover:bg-brand-50 hover:text-brand-800"
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>

          <form onSubmit={onSearch} className="ml-auto hidden max-w-xs flex-1 md:block" role="search">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-brand-300" aria-hidden />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search books, authors, ISBN…"
                className="h-9 w-full rounded-full border border-brand-200 bg-brand-50/60 pl-9 pr-3 text-sm placeholder:text-brand-300 focus:border-brand-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/30"
                aria-label="Search books"
              />
            </div>
          </form>

          <div className="ml-auto flex items-center gap-1 md:ml-2">
            {user?.role === "admin" && (
              <Link to="/admin" className="hidden rounded-lg p-2 text-brand-600 hover:bg-brand-50 sm:block" aria-label="Admin dashboard">
                <LayoutDashboard className="h-5 w-5" />
              </Link>
            )}
            {accessToken && (
              <Link to="/account/notifications" className="relative hidden rounded-lg p-2 text-brand-600 hover:bg-brand-50 sm:block" aria-label="Notifications">
                <Bell className="h-5 w-5" />
                {!!unread && unread > 0 && (
                  <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-red-500" aria-hidden />
                )}
              </Link>
            )}
            {accessToken && (
              <Link to="/wishlist" className="hidden rounded-lg p-2 text-brand-600 hover:bg-brand-50 sm:block" aria-label="Wishlist">
                <Heart className="h-5 w-5" />
              </Link>
            )}
            <Link to="/cart" className="relative rounded-lg p-2 text-brand-600 hover:bg-brand-50" aria-label={`Cart with ${cartCount} items`}>
              <ShoppingCart className="h-5 w-5" />
              {cartCount > 0 && (
                <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-accent-500 px-1 text-[10px] font-bold text-brand-950">
                  {cartCount}
                </span>
              )}
            </Link>

            {accessToken ? (
              <div className="relative ml-1 hidden sm:block">
                <Menu as="div">
                  <details className="group">
                    <summary className="flex h-9 w-9 cursor-pointer list-none items-center justify-center rounded-full bg-brand-700 text-sm font-semibold text-white">
                      {user?.full_name?.charAt(0).toUpperCase() ?? "U"}
                    </summary>
                    <div className="absolute right-0 z-50 mt-2 w-48 rounded-xl border border-brand-100 bg-white py-1 shadow-lg">
                      <Link to="/account" className="block px-4 py-2 text-sm text-brand-700 hover:bg-brand-50">
                        My account
                      </Link>
                      <Link to="/account/orders" className="block px-4 py-2 text-sm text-brand-700 hover:bg-brand-50">
                        My orders
                      </Link>
                      {user?.role === "admin" && (
                        <Link to="/admin" className="block px-4 py-2 text-sm text-brand-700 hover:bg-brand-50">
                          Admin dashboard
                        </Link>
                      )}
                      <button
                        onClick={onLogout}
                        className="flex w-full items-center gap-2 px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50"
                      >
                        <LogOut className="h-4 w-4" /> Sign out
                      </button>
                    </div>
                  </details>
                </Menu>
              </div>
            ) : (
              <div className="ml-2 hidden items-center gap-2 sm:flex">
                <Button variant="ghost" size="sm" onClick={() => navigate("/login")}>
                  Sign in
                </Button>
                <Button size="sm" onClick={() => navigate("/register")}>
                  Sign up
                </Button>
              </div>
            )}
          </div>
        </div>

        {mobileOpen && (
          <div className="border-t border-brand-100 bg-white px-4 pb-4 pt-2 lg:hidden">
            <form onSubmit={onSearch} className="mb-3 md:hidden" role="search">
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search books…"
                className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
                aria-label="Search books"
              />
            </form>
            {NAV_LINKS.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.to === "/"}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  `block rounded-lg px-3 py-2.5 text-sm font-medium ${isActive ? "bg-brand-50 text-brand-800" : "text-brand-600"}`
                }
              >
                {link.label}
              </NavLink>
            ))}
            <div className="mt-3 flex flex-col gap-2 border-t border-brand-50 pt-3">
              {accessToken ? (
                <>
                  <Link to="/account" onClick={() => setMobileOpen(false)} className="rounded-lg px-3 py-2.5 text-sm text-brand-700">
                    My account
                  </Link>
                  {user?.role === "admin" && (
                    <Link to="/admin" onClick={() => setMobileOpen(false)} className="rounded-lg px-3 py-2.5 text-sm text-brand-700">
                      Admin dashboard
                    </Link>
                  )}
                  <button onClick={onLogout} className="rounded-lg px-3 py-2.5 text-left text-sm text-red-600">
                    Sign out
                  </button>
                </>
              ) : (
                <div className="flex gap-2">
                  <Button variant="outline" className="flex-1" onClick={() => navigate("/login")}>
                    Sign in
                  </Button>
                  <Button className="flex-1" onClick={() => navigate("/register")}>
                    Sign up
                  </Button>
                </div>
              )}
            </div>
          </div>
        )}
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="mt-16 border-t border-brand-100 bg-brand-950 text-brand-200">
        <div className="mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:px-6 md:grid-cols-4">
          <div>
            <div className="flex items-center gap-2">
              <Library className="h-6 w-6 text-accent-400" aria-hidden />
              <span className="font-serif text-lg font-bold text-white">ShelfSpace</span>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-brand-300">
              A modern bookstore built for people who love the printed word. Curated titles, fair prices, real service.
            </p>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Shop</h3>
            <ul className="mt-3 space-y-2 text-sm">
              <li><Link to="/books" className="hover:text-white">All books</Link></li>
              <li><Link to="/books?sort=newest" className="hover:text-white">New arrivals</Link></li>
              <li><Link to="/books?sort=rating" className="hover:text-white">Top rated</Link></li>
              <li><Link to="/wishlist" className="hover:text-white">Wishlist</Link></li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Account</h3>
            <ul className="mt-3 space-y-2 text-sm">
              <li><Link to="/account" className="hover:text-white">Profile</Link></li>
              <li><Link to="/account/orders" className="hover:text-white">Orders</Link></li>
              <li><Link to="/account/addresses" className="hover:text-white">Addresses</Link></li>
              <li><Link to="/account/security" className="hover:text-white">Security</Link></li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Company</h3>
            <ul className="mt-3 space-y-2 text-sm">
              <li><Link to="/about" className="hover:text-white">About us</Link></li>
              <li><Link to="/contact" className="hover:text-white">Contact</Link></li>
            </ul>
          </div>
        </div>
        <div className="border-t border-brand-800/60 py-4 text-center text-xs text-brand-400">
          © {new Date().getFullYear()} ShelfSpace. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
