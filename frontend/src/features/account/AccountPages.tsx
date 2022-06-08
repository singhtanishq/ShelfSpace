import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, NavLink, Outlet, useLocation, useParams } from "react-router-dom";
import { Package, MapPin, KeyRound, ClipboardList, Heart, Bell, User as UserIcon, FileDown, RotateCcw, XCircle, Star, Trash2, Plus, Pencil, LogIn , CheckCircle2}
import { toast } from "sonner";
import { addressApi, authApi, cartApi, notificationsApi, ordersApi, wishlistApi, accountApi, catalogApi } from "@/api/endpoints";
import { useAuthStore } from "@/stores/auth";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, StatusBadge } from "@/components/ui/Card";
import { Input, Field, Select, Textarea } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { EmptyState, PageLoader, ErrorState } from "@/components/ui/states";
import { Pagination } from "@/components/ui/misc";
import { BookCover } from "@/components/books/BookCard";
import { formatCurrency, formatDate, formatDateTime } from "@/utils";
import type { Address, Order } from "@/types/api";

/* ------------------------------------------------- layout + navigation */

const NAV = [
  { to: "/account", label: "Profile", icon: UserIcon, end: true },
  { to: "/account/orders", label: "Orders", icon: ClipboardList },
  { to: "/account/addresses", label: "Addresses", icon: MapPin },
  { to: "/account/reviews", label: "My reviews", icon: Star },
  { to: "/account/notifications", label: "Notifications", icon: Bell },
  { to: "/account/security", label: "Security", icon: KeyRound },
];

export function AccountLayout() {
  const user = useAuthStore((s) => s.user);
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      <h1 className="font-serif text-2xl font-bold text-brand-900">My account</h1>
      <p className="mt-1 text-sm text-brand-400">Signed in as {user?.email}</p>
      <div className="mt-6 grid gap-8 lg:grid-cols-[220px_1fr]">
        <nav className="flex gap-2 overflow-x-auto lg:flex-col" aria-label="Account">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={"end" in item ? (item.end as boolean) : false}
              className={({ isActive }) =>
                `flex items-center gap-2.5 whitespace-nowrap rounded-lg px-3.5 py-2.5 text-sm font-medium transition-colors ${
                  isActive ? "bg-brand-700 text-white" : "text-brand-600 hover:bg-brand-100/70"
                }`
              }
            >
              <item.icon className="h-4 w-4" aria-hidden />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="min-w-0">
          <Outlet />
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------- profile */

export function ProfilePage() {
  const { user, setUser } = useAuthStore();
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [phone, setPhone] = useState(user?.phone ?? "");
  const [busy, setBusy] = useState(false);

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      const resp = await authApi.updateProfile({ full_name: fullName, phone: phone || null });
      setUser(resp.data);
      toast.success("Profile updated");
    } catch (err: any) {
      toast.error(err?.response?.data?.error?.message ?? "Could not update profile");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card className="max-w-xl">
      <CardHeader title="Profile details" description="Your name and contact information" />
      <CardBody>
        <form onSubmit={save} className="space-y-4">
          <Field label="Full name" required>
            <Input value={fullName} onChange={(e) => setFullName(e.target.value)} required minLength={2} />
          </Field>
          <Field label="Email" hint="Email changes require contacting support">
            <Input value={user?.email ?? ""} disabled />
          </Field>
          <Field label="Username">
            <Input value={user?.username ?? ""} disabled />
          </Field>
          <Field label="Phone">
            <Input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+91 …" />
          </Field>
          {!user?.is_verified && (
            <div className="rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800">
              Your email is not verified yet. Check your inbox for the verification link.
            </div>
          )}
          <Button type="submit" loading={busy}>Save changes</Button>
        </form>
      </CardBody>
    </Card>
  );
}

/* ------------------------------------------------- orders list */

export function OrdersPage() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["orders", page, status],
    queryFn: () => ordersApi.list({ page, page_size: 8, status: status || undefined }).then((r) => r.data),
  });

  if (isError) return <ErrorState message="Could not load your orders." onRetry={() => refetch()} />;
  if (isLoading) return <PageLoader label="Loading your orders…" />;
  if (!data || data.items.length === 0) {
    return (
      <EmptyState
        icon={<Package className="h-10 w-10" aria-hidden />}
        title="No orders yet"
        description="When you place your first order, it will show up here."
        action={<Button onClick={() => (window.location.href = "/books")}>Browse books</Button>}
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} className="w-48" aria-label="Filter by status">
          <option value="">All orders</option>
          {["pending", "confirmed", "processing", "shipped", "out_for_delivery", "delivered", "cancelled", "returned"].map((s) => (
            <option key={s} value={s}>{s.replaceAll("_", " ")}</option>
          ))}
        </Select>
      </div>
      {data.items.map((order) => (
        <Card key={order.id} className="p-4 transition-shadow hover:shadow-card-hover">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <Link to={`/account/orders/${order.order_number}`} className="font-semibold text-brand-900 hover:text-brand-600">
                {order.order_number}
              </Link>
              <p className="text-xs text-brand-400">Placed {formatDate(order.placed_at)}</p>
            </div>
            <StatusBadge status={order.status} />
            <StatusBadge status={order.payment_status} />
            <div className="ml-auto text-right">
              <p className="font-bold text-brand-900">{formatCurrency(order.total)}</p>
              <p className="text-xs text-brand-400">{order.items.length} item{order.items.length === 1 ? "" : "s"}</p>
            </div>
          </div>
          <div className="mt-3 flex items-center gap-2 overflow-x-auto">
            {order.items.slice(0, 5).map((item) => (
              <BookCover key={item.id} src={item.cover_image} alt={item.title} className="h-16 w-11 shrink-0 rounded" />
            ))}
            {order.items.length > 5 && (
              <span className="text-xs text-brand-400">+{order.items.length - 5} more</span>
            )}
            <Link to={`/account/orders/${order.order_number}`} className="ml-auto shrink-0 text-sm font-medium text-brand-600 hover:text-brand-800">
              View details →
            </Link>
          </div>
        </Card>
      ))}
      <Pagination page={data.page} pages={data.pages} onChange={setPage} />
    </div>
  );
}

/* ------------------------------------------------- order detail */

const STATUS_STEPS = ["pending", "confirmed", "processing", "shipped", "out_for_delivery", "delivered"] as const;

export function OrderDetailPage({ adminMode = false }: { adminMode?: boolean }) {
  const { orderNumber = "" } = useParams();
  const location = useLocation();
  const queryClient = useQueryClient();
  const [cancelOpen, setCancelOpen] = useState(false);
  const [returnModal, setReturnModal] = useState(false);
  const justOrdered = !!(location.state as any)?.justOrdered;

  const downloadInvoice = async () => {
    try {
      const resp = await ordersApi.invoice(orderNumber);
      const url = window.URL.createObjectURL(new Blob([resp.data as any], { type: "application/pdf" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = `invoice-${orderNumber}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      toast.error("Could not download the invoice");
    }
  };

  const { data: order, isLoading, isError } = useQuery({
    queryKey: ["order", orderNumber],
    queryFn: () => ordersApi.detail(orderNumber).then((r) => r.data),
  });

  if (isLoading) return <PageLoader label="Loading order…" />;
  if (isError || !order) {
    return <EmptyState title="Order not found" description="Check the order number and try again." action={<Button onClick={() => history.back()}>Go back</Button>} />;
  }

  const currentStep = STATUS_STEPS.indexOf(order.status as any);
  const activeReturn = order.returns.find((r) => ["requested", "approved"].includes(r.status));
  const allReturned = order.returns.filter((r) => r.status === "completed").flatMap((r) => r.items);
  const cancellable = ["pending", "confirmed", "processing"].includes(order.status) && !adminMode;
  const returnEligible = order.status === "delivered" && !activeReturn && order.returns.every((r) => r.status !== "completed");

  return (
    <div className="space-y-6">
      {adminMode && (
        <Link to="/admin/orders" className="inline-block text-sm text-brand-500 hover:text-brand-800">← Back to all orders</Link>
      )}

      {/* Success banner */}
      {justOrdered && !adminMode && (
        <div className="flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800 animate-fade-in-up">
          <CheckCircle2 className="h-5 w-5" aria-hidden />
          Thank you! Your order has been placed. A confirmation email is on its way.
        </div>
      )}

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-serif text-xl font-bold text-brand-900">{order.order_number}</h2>
          <p className="text-sm text-brand-400">Placed {formatDateTime(order.placed_at)}</p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={order.status} />
          <StatusBadge status={order.payment_status} />
        </div>
      </div>

      {/* Tracking timeline */}
      {order.status !== "cancelled" && order.status !== "returned" && (
        <Card>
          <CardHeader title="Tracking" />
          <CardBody>
            <ol className="flex flex-col gap-0 sm:flex-row sm:items-start">
              {STATUS_STEPS.map((step, i) => {
                const reached = i <= currentStep;
                return (
                  <li key={step} className="flex flex-1 gap-3 sm:flex-col sm:gap-2">
                    <div className="flex flex-col items-center sm:contents">
                      <div className="flex flex-col items-center">
                        <span className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${reached ? "bg-brand-700 text-white" : "bg-brand-100 text-brand-400"}`}>
                          {i + 1}
                        </span>
                        {i < STATUS_STEPS.length - 1 && (
                          <span className={`h-8 w-0.5 sm:h-0.5 sm:w-full ${i < currentStep ? "bg-brand-700" : "bg-brand-100"}`} aria-hidden />
                        )}
                      </div>
                    </div>
                    <span className={`pb-6 text-xs capitalize sm:text-center ${reached ? "font-semibold text-brand-800" : "text-brand-300"}`}>
                      {step.replaceAll("_", " ")}
                    </span>
                  </li>
                );
              })}
            </ol>
            {order.delivered_at && (
              <p className="text-xs text-emerald-600">Delivered on {formatDate(order.delivered_at)}</p>
            )}
          </CardBody>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        {/* Items */}
        <Card>
          <CardHeader title="Items" action={
            !adminMode ? (
              <Button variant="outline" size="sm" onClick={downloadInvoice}>
                <FileDown className="h-4 w-4" aria-hidden /> Invoice
              </Button>
            ) : undefined
          } />
          <CardBody className="space-y-4">
            {order.items.map((item) => {
              const returnedQty = allReturned.filter((ri) => ri.order_item_id === item.id).reduce((acc, ri) => acc + ri.quantity, 0);
              return (
                <div key={item.id} className="flex gap-4">
                  <BookCover src={item.cover_image} alt={item.title} className="h-20 w-14 shrink-0 rounded-lg" />
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-brand-900">{item.title}</p>
                    <p className="text-sm text-brand-400">{item.author_names}</p>
                    <p className="mt-1 text-sm text-brand-500">
                      {formatCurrency(item.unit_price)} × {item.quantity}
                    </p>
                    {returnedQty >= item.quantity && <p className="text-xs font-medium text-brand-400">Fully returned</p>}
                    {item.book_id && ["delivered", "returned"].includes(order.status) && (
                      <Link to={`/books?q=${encodeURIComponent(item.title)}`} className="mt-1 inline-flex items-center gap-1 text-xs font-medium text-brand-600 hover:text-brand-800">
                        <Star className="h-3 w-3" aria-hidden /> Rate & review
                      </Link>
                    )}
                  </div>
                  <p className="font-bold text-brand-900">{formatCurrency(item.line_total)}</p>
                </div>
              );
            })}
            <div className="space-y-1.5 border-t border-brand-100 pt-4 text-sm">
              <Row label="Subtotal" value={formatCurrency(order.subtotal)} />
              {order.discount_total > 0 && <Row label={`Discount ${order.coupon_code ? `(${order.coupon_code})` : ""}`} value={`−${formatCurrency(order.discount_total)}`} highlight />}
              <Row label="Shipping" value={order.shipping_fee === 0 ? "Free" : formatCurrency(order.shipping_fee)} />
              {order.tax_total > 0 && <Row label="Tax" value={formatCurrency(order.tax_total)} />}
              <Row label="Total" value={formatCurrency(order.total)} bold />
            </div>
          </CardBody>
        </Card>

        {/* Address + actions */}
        <div className="space-y-6">
          <Card>
            <CardHeader title="Delivery address" />
            <CardBody className="text-sm text-brand-600">
              <p className="font-medium text-brand-900">{order.shipping_address.full_name}</p>
              <p className="mt-1">{order.shipping_address.line1}{order.shipping_address.line2 ? `, ${order.shipping_address.line2}` : ""}</p>
              <p>{order.shipping_address.city}, {order.shipping_address.state} {order.shipping_address.postal_code}</p>
              <p>{order.shipping_address.country}</p>
              <p className="mt-1">{order.shipping_address.phone}</p>
              {order.notes && <p className="mt-3 rounded-lg bg-brand-50 p-2 text-xs text-brand-500">Note: {order.notes}</p>}
            </CardBody>
          </Card>

          {!adminMode && (
            <Card>
              <CardHeader title="Actions" />
              <CardBody className="flex flex-col gap-2">
                <Button variant="outline" disabled={!cancellable} onClick={() => setCancelOpen(true)}>
                  <XCircle className="h-4 w-4" aria-hidden /> Cancel order
                </Button>
                <Button variant="outline" disabled={!returnEligible} onClick={() => setReturnModal(true)}>
                  <RotateCcw className="h-4 w-4" aria-hidden /> Return or replace
                </Button>
                {!cancellable && !returnEligible && (
                  <p className="text-xs text-brand-400">
                    {activeReturn
                      ? `A ${activeReturn.type} request (${activeReturn.return_number}) is already ${activeReturn.status}.`
                      : "This order is no longer eligible for cancellation or returns."}
                  </p>
                )}
              </CardBody>
            </Card>
          )}

          {/* Return requests */}
          {order.returns.length > 0 && (
            <Card>
              <CardHeader title="Return requests" />
              <CardBody className="space-y-3">
                {order.returns.map((r) => (
                  <div key={r.id} className="rounded-lg border border-brand-100 p-3 text-sm">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold text-brand-900">{r.return_number}</span>
                      <StatusBadge status={r.status} />
                    </div>
                    <p className="mt-1 capitalize text-brand-500">{r.type} · {r.reason.replaceAll("_", " ")}</p>
                    {r.refund_amount != null && <p className="text-brand-500">Refund: {formatCurrency(r.refund_amount)} ({r.refund_status})</p>}
                    {r.admin_note && <p className="mt-1 text-xs text-brand-400">“{r.admin_note}”</p>}
                  </div>
                ))}
              </CardBody>
            </Card>
          )}
        </div>
      </div>

      {/* Status history */}
      <Card>
        <CardHeader title="Order history" />
        <CardBody>
          <ol className="space-y-3">
            {[...order.status_history].reverse().map((h, i) => (
              <li key={i} className="flex items-center gap-3 text-sm">
                <span className="h-2 w-2 rounded-full bg-brand-300" aria-hidden />
                <StatusBadge status={h.to_status} />
                <span className="text-brand-400">{formatDateTime(h.created_at)}</span>
                {h.note && <span className="text-brand-500">— {h.note}</span>}
              </li>
            ))}
          </ol>
        </CardBody>
      </Card>

      <CancelDialog order={order} open={cancelOpen} onClose={() => setCancelOpen(false)} onDone={() => queryClient.invalidateQueries({ queryKey: ["order", orderNumber] })} />
      <ReturnModal order={order} open={returnModal} onClose={() => setReturnModal(false)} onDone={() => queryClient.invalidateQueries({ queryKey: ["order", orderNumber] })} />
    </div>
  );
}

function Row({ label, value, bold, highlight }: { label: string; value: string; bold?: boolean; highlight?: boolean }) {
  return (
    <div className={`flex justify-between ${bold ? "text-base font-bold text-brand-950" : highlight ? "text-emerald-600" : "text-brand-600"}`}>
      <span>{label}</span>
      <span className="tabular-nums">{value}</span>
    </div>
  );
}

function CancelDialog({ order, open, onClose, onDone }: { order: Order; open: boolean; onClose: () => void; onDone: () => void }) {
  const [note, setNote] = useState("");
  const cancel = useMutation({
    mutationFn: () => ordersApi.cancel(order.order_number, note || undefined),
    onSuccess: () => {
      toast.success("Order cancelled. Any payment will be refunded.");
      onDone();
      onClose();
    },
    onError: (err: any) => toast.error(err?.response?.data?.error?.message ?? "Could not cancel order"),
  });
  return (
    <Modal open={open} onClose={onClose} title="Cancel this order?">
      <p className="text-sm text-brand-600">
        Your items will be returned to stock and any paid amount refunded to the original payment method. This cannot be undone.
      </p>
      <div className="mt-4">
        <Field label="Reason (optional)">
          <Textarea value={note} onChange={(e) => setNote(e.target.value)} rows={2} placeholder="Why are you cancelling?" />
        </Field>
      </div>
      <div className="mt-5 flex justify-end gap-2">
        <Button variant="ghost" onClick={onClose}>Keep order</Button>
        <Button variant="danger" loading={cancel.isPending} onClick={() => cancel.mutate()}>Yes, cancel it</Button>
      </div>
    </Modal>
  );
}

function ReturnModal({ order, open, onClose, onDone }: { order: Order; open: boolean; onClose: () => void; onDone: () => void }) {
  const [type, setType] = useState<"return" | "replacement">("return");
  const [reason, setReason] = useState("damaged");
  const [description, setDescription] = useState("");
  const [quantities, setQuantities] = useState<Record<number, number>>({});

  const submit = useMutation({
    mutationFn: () => {
      const items = order.items
        .map((i) => ({ order_item_id: i.id, quantity: quantities[i.id] ?? 0 }))
        .filter((i) => i.quantity > 0);
      return ordersApi.createReturn(order.order_number, { type, reason, description: description || undefined, items });
    },
    onSuccess: () => {
      toast.success("Request submitted! We'll review it shortly.");
      onDone();
      onClose();
    },
    onError: (err: any) => toast.error(err?.response?.data?.error?.message ?? "Could not submit request"),
  });

  const anySelected = Object.values(quantities).some((q) => q > 0);

  return (
    <Modal open={open} onClose={onClose} title="Return or replace items" size="lg">
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          {(["return", "replacement"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setType(t)}
              className={`rounded-xl border p-3 text-left text-sm transition-colors ${type === t ? "border-brand-600 bg-brand-50/60 ring-1 ring-brand-600" : "border-brand-100 hover:border-brand-300"}`}
              role="radio"
              aria-checked={type === t}
            >
              <span className="font-semibold capitalize text-brand-900">{t}</span>
              <p className="text-xs text-brand-400">{t === "return" ? "Send items back for a refund" : "Get a fresh copy of the item"}</p>
            </button>
          ))}
        </div>

        <div className="space-y-2">
          {order.items.map((item) => (
            <div key={item.id} className="flex items-center justify-between gap-3 rounded-lg border border-brand-100 p-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-brand-900">{item.title}</p>
                <p className="text-xs text-brand-400">Purchased × {item.quantity}</p>
              </div>
              <Select
                className="w-28"
                value={String(quantities[item.id] ?? 0)}
                onChange={(e) => setQuantities({ ...quantities, [item.id]: Number(e.target.value) })}
                aria-label={`Quantity to ${type} for ${item.title}`}
              >
                <option value="0">None</option>
                {Array.from({ length: item.quantity }).map((_, q) => (
                  <option key={q + 1} value={q + 1}>{q + 1}</option>
                ))}
              </Select>
            </div>
          ))}
        </div>

        <Field label="Reason">
          <Select value={reason} onChange={(e) => setReason(e.target.value)}>
            {["damaged", "defective", "wrong_item", "not_as_described", "changed_mind", "other"].map((r) => (
              <option key={r} value={r}>{r.replaceAll("_", " ")}</option>
            ))}
          </Select>
        </Field>
        <Field label="Describe the issue (optional)">
          <Textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} maxLength={2000} />
        </Field>
      </div>
      <div className="mt-5 flex justify-end gap-2">
        <Button variant="ghost" onClick={onClose}>Cancel</Button>
        <Button onClick={() => submit.mutate()} loading={submit.isPending} disabled={!anySelected}>
          Submit {type} request
        </Button>
      </div>
    </Modal>
  );
}

/* ------------------------------------------------- addresses */

const EMPTY_ADDR = { label: "Home", full_name: "", phone: "", line1: "", line2: "", city: "", state: "", postal_code: "", country: "India" };

export function AddressesPage() {
  const queryClient = useQueryClient();
  const [modal, setModal] = useState(false);
  const [editing, setEditing] = useState<number | null>(null);
  const [form, setForm] = useState({ ...EMPTY_ADDR });
  const [deleteId, setDeleteId] = useState<number | null>(null);

  const { data: addresses, isLoading } = useQuery({ queryKey: ["addresses"], queryFn: () => addressApi.list().then((r) => r.data) });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["addresses"] });

  const save = useMutation({
    mutationFn: () => (editing ? addressApi.update(editing, form) : addressApi.create(form)),
    onSuccess: () => {
      toast.success(editing ? "Address updated" : "Address added");
      setModal(false);
      invalidate();
    },
    onError: (err: any) => toast.error(err?.response?.data?.error?.message ?? "Could not save address"),
  });

  const remove = useMutation({
    mutationFn: (id: number) => addressApi.remove(id),
    onSuccess: () => {
      toast.success("Address removed");
      setDeleteId(null);
      invalidate();
    },
  });

  const valid = form.full_name.trim().length >= 2 && form.phone.trim().length >= 7 && form.line1.trim().length >= 4 && form.city.trim().length >= 2 && form.state.trim().length >= 2 && form.postal_code.trim().length >= 4;

  if (isLoading) return <PageLoader />;

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => { setEditing(null); setForm({ ...EMPTY_ADDR }); setModal(true); }}>
          <Plus className="h-4 w-4" aria-hidden /> Add address
        </Button>
      </div>
      {(!addresses || addresses.length === 0) && (
        <EmptyState icon={<MapPin className="h-10 w-10" aria-hidden />} title="No saved addresses" description="Save an address to speed up checkout." />
      )}
      <div className="grid gap-4 sm:grid-cols-2">
        {addresses?.map((a) => (
          <Card key={a.id} className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <span className="rounded bg-brand-100 px-1.5 py-0.5 text-xs font-medium text-brand-600">{a.label}</span>
                {a.is_default && <span className="ml-1.5 rounded bg-emerald-50 px-1.5 py-0.5 text-xs font-medium text-emerald-700">Default</span>}
              </div>
              <div className="flex gap-1">
                <button onClick={() => { setEditing(a.id); setForm({ label: a.label, full_name: a.full_name, phone: a.phone, line1: a.line1, line2: a.line2 ?? "", city: a.city, state: a.state, postal_code: a.postal_code, country: a.country }); setModal(true); }} className="rounded p-1.5 text-brand-300 hover:text-brand-700" aria-label="Edit address">
                  <Pencil className="h-4 w-4" />
                </button>
                <button onClick={() => setDeleteId(a.id)} className="rounded p-1.5 text-brand-300 hover:text-red-600" aria-label="Delete address">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
            <p className="mt-2 text-sm font-semibold text-brand-900">{a.full_name}</p>
            <p className="text-sm text-brand-500">{a.line1}{a.line2 ? `, ${a.line2}` : ""}</p>
            <p className="text-sm text-brand-500">{a.city}, {a.state} {a.postal_code}</p>
            <p className="text-sm text-brand-400">{a.phone}</p>
          </Card>
        ))}
      </div>

      <Modal open={modal} onClose={() => setModal(false)} title={editing ? "Edit address" : "Add address"}>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Label">
            <Select value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })}>
              <option>Home</option><option>Work</option><option>Other</option>
            </Select>
          </Field>
          <Field label="Full name" required>
            <Input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
          </Field>
          <Field label="Phone" required>
            <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          </Field>
          <Field label="City" required>
            <Input value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
          </Field>
          <div className="sm:col-span-2">
            <Field label="Address line 1" required>
              <Input value={form.line1} onChange={(e) => setForm({ ...form, line1: e.target.value })} />
            </Field>
          </div>
          <div className="sm:col-span-2">
            <Field label="Address line 2">
              <Input value={form.line2} onChange={(e) => setForm({ ...form, line2: e.target.value })} />
            </Field>
          </div>
          <Field label="State" required>
            <Input value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value })} />
          </Field>
          <Field label="Postal code" required>
            <Input value={form.postal_code} onChange={(e) => setForm({ ...form, postal_code: e.target.value })} />
          </Field>
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setModal(false)}>Cancel</Button>
          <Button onClick={() => save.mutate()} loading={save.isPending} disabled={!valid}>Save</Button>
        </div>
      </Modal>

      <ConfirmDialog
        open={deleteId !== null}
        onClose={() => setDeleteId(null)}
        onConfirm={() => deleteId && remove.mutate(deleteId)}
        title="Delete address?"
        message="This address will be removed from your account. Orders already placed are unaffected."
        confirmLabel="Delete"
        danger
        loading={remove.isPending}
      />
    </div>
  );
}

/* ------------------------------------------------- wishlist */

export function WishlistPage() {
  const queryClient = useQueryClient();
  const { data: items, isLoading } = useQuery({ queryKey: ["wishlist"], queryFn: () => wishlistApi.list().then((r) => r.data) });

  const move = useMutation({
    mutationFn: async (bookId: number) => {
      await cartApi.addItem(bookId, 1);
      await wishlistApi.remove(bookId);
    },
    onSuccess: () => {
      toast.success("Moved to cart");
      queryClient.invalidateQueries({ queryKey: ["wishlist"] });
      queryClient.invalidateQueries({ queryKey: ["cart"] });
    },
    onError: (err: any) => toast.error(err?.response?.data?.error?.message ?? "Could not move to cart"),
  });

  const remove = useMutation({
    mutationFn: (bookId: number) => wishlistApi.remove(bookId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["wishlist"] }),
  });

  if (isLoading) return <PageLoader label="Loading wishlist…" />;
  if (!items || items.length === 0) {
    return (
      <EmptyState icon={<Heart className="h-10 w-10" aria-hidden />} title="Your wishlist is empty" description="Tap the heart on any book to save it for later." action={<Button onClick={() => (window.location.href = "/books")}>Find something to read</Button>} />
    );
  }

  return (
    <div className="space-y-4">
      {items.map((item) => (
        <Card key={item.book_id} className="flex gap-4 p-4">
          <BookCover src={item.cover_image} alt={item.title} className="h-28 w-20 shrink-0 rounded-lg" />
          <div className="flex min-w-0 flex-1 flex-col">
            <Link to={`/books/${item.slug}`} className="font-semibold text-brand-900 hover:text-brand-600">{item.title}</Link>
            <p className="text-sm text-brand-400">{item.author_names}</p>
            <p className="mt-1 font-bold text-brand-900">{formatCurrency(item.effective_price)}</p>
            <div className="mt-auto flex gap-2 pt-2">
              <Button size="sm" disabled={item.available_quantity <= 0} onClick={() => move.mutate(item.book_id)}>
                Move to cart
              </Button>
              <Button size="sm" variant="ghost" onClick={() => remove.mutate(item.book_id)}>Remove</Button>
              {item.available_quantity <= 0 && <span className="self-center text-xs text-red-500">Out of stock</span>}
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}

/* ------------------------------------------------- my reviews */

export function MyReviewsPage() {
  const { data: reviews, isLoading, isError } = useQuery({ queryKey: ["my-reviews"], queryFn: () => accountApi.myReviews().then((r) => r.data) });
  const queryClient = useQueryClient();

  const remove = useMutation({
    mutationFn: (id: number) => catalogApi.deleteReview(id),
    onSuccess: () => {
      toast.success("Review deleted");
      queryClient.invalidateQueries({ queryKey: ["my-reviews"] });
    },
  });

  if (isLoading) return <PageLoader />;
  if (isError) return <ErrorState message="Could not load your reviews." />;
  if (!reviews || reviews.length === 0) {
    return <EmptyState icon={<Star className="h-10 w-10" aria-hidden />} title="No reviews written yet" description="Reviews you write on purchased books will appear here." />;
  }

  return (
    <div className="space-y-4">
      {reviews.map((r) => (
        <Card key={r.id} className="p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-semibold text-brand-900">{r.title || "Review"}</p>
              <p className="text-xs text-brand-400">{formatDate(r.created_at)}</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-accent-500">{"★".repeat(r.rating)}{"☆".repeat(5 - r.rating)}</span>
              <button onClick={() => remove.mutate(r.id)} className="rounded p-1.5 text-brand-300 hover:text-red-600" aria-label="Delete review">
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
          <p className="mt-2 text-sm text-brand-600">{r.content}</p>
        </Card>
      ))}
    </div>
  );
}

/* ------------------------------------------------- security */

export function SecurityPage() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (next !== confirm) {
      toast.error("New passwords do not match");
      return;
    }
    setBusy(true);
    try {
      await authApi.changePassword({ current_password: current, new_password: next });
      toast.success("Password updated");
      setCurrent(""); setNext(""); setConfirm("");
    } catch (err: any) {
      toast.error(err?.response?.data?.error?.message ?? "Could not change password");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card className="max-w-xl">
      <CardHeader title="Change password" description="Choose a strong, unique password" />
      <CardBody>
        <form onSubmit={submit} className="space-y-4">
          <Field label="Current password" required>
            <Input type="password" value={current} onChange={(e) => setCurrent(e.target.value)} required autoComplete="current-password" />
          </Field>
          <Field label="New password" required hint="Minimum 8 characters">
            <Input type="password" value={next} onChange={(e) => setNext(e.target.value)} required minLength={8} autoComplete="new-password" />
          </Field>
          <Field label="Confirm new password" required>
            <Input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required minLength={8} autoComplete="new-password" />
          </Field>
          <Button type="submit" loading={busy}>Update password</Button>
        </form>
      </CardBody>
    </Card>
  );
}

/* ------------------------------------------------- notifications */

export function NotificationsPage() {
  const [page, setPage] = useState(1);
  const queryClient = useQueryClient();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["notifications", page],
    queryFn: () => notificationsApi.list({ page }).then((r) => r.data),
  });

  const markRead = useMutation({
    mutationFn: (id: number) => notificationsApi.markRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markAll = useMutation({
    mutationFn: () => notificationsApi.markAllRead(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  if (isError) return <ErrorState message="Could not load notifications." />;
  if (isLoading) return <PageLoader />;
  if (!data || data.items.length === 0) {
    return <EmptyState icon={<Bell className="h-10 w-10" aria-hidden />} title="No notifications" description="Order updates and announcements will appear here." />;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button variant="ghost" size="sm" onClick={() => markAll.mutate()} disabled={(data.unread_count ?? 0) === 0}>
          Mark all as read
        </Button>
      </div>
      {data.items.map((n) => (
        <Card key={n.id} className={`p-4 ${!n.is_read ? "border-l-4 border-l-brand-600" : ""}`}>
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className={`text-sm ${n.is_read ? "text-brand-500" : "font-semibold text-brand-900"}`}>{n.title}</p>
              <p className="mt-1 text-sm text-brand-500">{n.body}</p>
              <p className="mt-1.5 text-xs text-brand-300">{formatDateTime(n.created_at)}</p>
            </div>
            {!n.is_read && (
              <Button variant="ghost" size="sm" onClick={() => markRead.mutate(n.id)}>Mark read</Button>
            )}
          </div>
        </Card>
      ))}
      <Pagination page={data.page} pages={data.pages} onChange={setPage} />
    </div>
  );
}

export function NotSignedIn() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-16">
      <EmptyState
        icon={<LogIn className="h-10 w-10" aria-hidden />}
        title="Sign in required"
        description="Please sign in to view this page."
        action={<Link to="/login"><Button>Sign in</Button></Link>}
      />
    </div>
  );
}

export type { Address };
