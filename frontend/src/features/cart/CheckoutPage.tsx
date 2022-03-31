import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Banknote, CreditCard, Smartphone, CheckCircle2, Plus, Pencil } from "lucide-react";
import { toast } from "sonner";
import { addressApi, cartApi, ordersApi } from "@/api/endpoints";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input, Field, Select } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { EmptyState, PageLoader } from "@/components/ui/states";
import { cn, formatCurrency } from "@/utils";

const PAYMENT_METHODS = [
  { value: "cod", label: "Cash on delivery", hint: "Pay when your books arrive", icon: Banknote },
  { value: "card", label: "Card (demo)", hint: "Mock payment — no real charge", icon: CreditCard },
  { value: "upi", label: "UPI (demo)", hint: "Mock payment — no real charge", icon: Smartphone },
] as const;

const EMPTY_FORM = {
  label: "Home",
  full_name: "",
  phone: "",
  line1: "",
  line2: "",
  city: "",
  state: "",
  postal_code: "",
  country: "India",
};

export function CheckoutPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedAddressId, setSelectedAddressId] = useState<number | "new">("new");
  const [payment, setPayment] = useState<"cod" | "card" | "upi">("cod");
  const [cardNumber, setCardNumber] = useState("");
  const [upiId, setUpiId] = useState("");
  const [notes, setNotes] = useState("");
  const [addressModal, setAddressModal] = useState(false);
  const [editingAddress, setEditingAddress] = useState<number | null>(null);
  const [form, setForm] = useState({ ...EMPTY_FORM });

  const { data: cart } = useQuery({ queryKey: ["cart"], queryFn: () => cartApi.get().then((r) => r.data) });
  const { data: addresses } = useQuery({
    queryKey: ["addresses"],
    queryFn: () => addressApi.list().then((r) => r.data),
  });

  const defaultAddress = useMemo(
    () => addresses?.find((a) => a.is_default) ?? addresses?.[0],
    [addresses]
  );

  useMemo(() => {
    if (defaultAddress && selectedAddressId === "new" && addresses && addresses.length > 0 && selectedAddressId !== "new") {
      // no-op: keeps types honest
    }
  }, [defaultAddress, addresses, selectedAddressId]);

  const saveAddress = useMutation({
    mutationFn: () =>
      editingAddress
        ? addressApi.update(editingAddress, form)
        : addressApi.create(form),
    onSuccess: () => {
      toast.success(editingAddress ? "Address updated" : "Address saved");
      setAddressModal(false);
      queryClient.invalidateQueries({ queryKey: ["addresses"] });
    },
    onError: (err: any) => toast.error(err?.response?.data?.error?.message ?? "Could not save address"),
  });

  const placeOrder = useMutation({
    mutationFn: () => {
      const payload: Record<string, unknown> = {
        payment_method: payment,
        notes: notes || undefined,
      };
      if (selectedAddressId === "new") {
        payload.shipping_address = form;
      } else {
        payload.address_id = selectedAddressId;
      }
      if (payment === "card") payload.card_number = cardNumber;
      if (payment === "upi") payload.upi_id = upiId;
      return ordersApi.checkout(payload as any);
    },
    onSuccess: (r) => {
      queryClient.setQueryData(["cart"], r.data ? null : null);
      queryClient.invalidateQueries({ queryKey: ["cart"] });
      toast.success("Order placed successfully!");
      navigate(`/account/orders/${r.data.order_number}`, { state: { justOrdered: true } });
    },
    onError: (err: any) => toast.error(err?.response?.data?.error?.message ?? "Checkout failed"),
  });

  if (!cart) return <PageLoader label="Preparing checkout…" />;

  if (cart.items.length === 0) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16">
        <EmptyState title="Your cart is empty" description="Add some books before checking out." action={<Button onClick={() => navigate("/books")}>Browse books</Button>} />
      </div>
    );
  }

  const addressFormValid =
    form.full_name.trim().length >= 2 && form.phone.trim().length >= 7 && form.line1.trim().length >= 4 &&
    form.city.trim().length >= 2 && form.state.trim().length >= 2 && form.postal_code.trim().length >= 4;

  const canPlace =
    cart.items.every((i) => i.in_stock) &&
    (selectedAddressId !== "new" || addressFormValid) &&
    (payment !== "card" || cardNumber.replace(/\s/g, "").length >= 12) &&
    (payment !== "upi" || upiId.includes("@")) &&
    !placeOrder.isPending;

  const openNewAddress = () => {
    setEditingAddress(null);
    setForm({ ...EMPTY_FORM, full_name: "", phone: "" });
    setAddressModal(true);
  };

  const openEditAddress = (id: number) => {
    const a = addresses?.find((x) => x.id === id);
    if (!a) return;
    setEditingAddress(id);
    setForm({
      label: a.label, full_name: a.full_name, phone: a.phone, line1: a.line1,
      line2: a.line2 ?? "", city: a.city, state: a.state, postal_code: a.postal_code, country: a.country,
    });
    setAddressModal(true);
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <h1 className="font-serif text-2xl font-bold text-brand-900 sm:text-3xl">Checkout</h1>

      <div className="mt-6 grid gap-8 lg:grid-cols-[1fr_360px]">
        <div className="space-y-6">
          {/* Address */}
          <Card>
            <CardHeader
              title="Shipping address"
              action={
                <Button variant="ghost" size="sm" onClick={openNewAddress}>
                  <Plus className="h-4 w-4" aria-hidden /> New address
                </Button>
              }
            />
            <CardBody className="space-y-3">
              {addresses && addresses.length > 0 ? (
                addresses.map((a) => (
                  <div
                    key={a.id}
                    className={cn(
                      "flex cursor-pointer items-start justify-between gap-3 rounded-xl border p-4 transition-colors",
                      selectedAddressId === a.id ? "border-brand-600 bg-brand-50/60 ring-1 ring-brand-600" : "border-brand-100 hover:border-brand-300"
                    )}
                    onClick={() => setSelectedAddressId(a.id)}
                    role="radio"
                    aria-checked={selectedAddressId === a.id}
                    tabIndex={0}
                    onKeyDown={(e) => e.key === "Enter" && setSelectedAddressId(a.id)}
                  >
                    <div className="flex items-start gap-3">
                      <input type="radio" checked={selectedAddressId === a.id} onChange={() => setSelectedAddressId(a.id)} className="mt-1 h-4 w-4" aria-label={`Use address ${a.label}`} />
                      <div className="text-sm">
                        <p className="font-semibold text-brand-900">
                          {a.full_name} <span className="ml-1 rounded bg-brand-100 px-1.5 py-0.5 text-xs font-medium text-brand-600">{a.label}</span>
                        </p>
                        <p className="mt-0.5 text-brand-500">{a.line1}{a.line2 ? `, ${a.line2}` : ""}, {a.city}, {a.state} {a.postal_code}</p>
                        <p className="text-brand-400">{a.phone}</p>
                      </div>
                    </div>
                    <button onClick={(e) => { e.stopPropagation(); openEditAddress(a.id); }} className="rounded p-1.5 text-brand-300 hover:text-brand-700" aria-label={`Edit ${a.label} address`}>
                      <Pencil className="h-4 w-4" />
                    </button>
                  </div>
                ))
              ) : (
                <p className="text-sm text-brand-400">No saved addresses yet — add one below.</p>
              )}

              <button
                onClick={() => setSelectedAddressId("new")}
                className={cn(
                  "w-full rounded-xl border border-dashed p-4 text-left text-sm transition-colors",
                  selectedAddressId === "new" ? "border-brand-600 bg-brand-50/60 text-brand-800 ring-1 ring-brand-600" : "border-brand-200 text-brand-400 hover:border-brand-400"
                )}
              >
                + Enter a new shipping address
              </button>

              {selectedAddressId === "new" && (
                <div className="grid gap-3 rounded-xl bg-brand-50/50 p-4 sm:grid-cols-2">
                  <Field label="Full name" required>
                    <Input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} placeholder="Your name" />
                  </Field>
                  <Field label="Phone" required>
                    <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} placeholder="+91 …" />
                  </Field>
                  <div className="sm:col-span-2">
                    <Field label="Address line 1" required>
                      <Input value={form.line1} onChange={(e) => setForm({ ...form, line1: e.target.value })} placeholder="House no, street, area" />
                    </Field>
                  </div>
                  <div className="sm:col-span-2">
                    <Field label="Address line 2">
                      <Input value={form.line2} onChange={(e) => setForm({ ...form, line2: e.target.value })} placeholder="Landmark (optional)" />
                    </Field>
                  </div>
                  <Field label="City" required>
                    <Input value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
                  </Field>
                  <Field label="State" required>
                    <Input value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value })} />
                  </Field>
                  <Field label="Postal code" required>
                    <Input value={form.postal_code} onChange={(e) => setForm({ ...form, postal_code: e.target.value })} />
                  </Field>
                  <Field label="Country">
                    <Input value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })} />
                  </Field>
                </div>
              )}
            </CardBody>
          </Card>

          {/* Payment */}
          <Card>
            <CardHeader title="Payment method" />
            <CardBody className="grid gap-3 sm:grid-cols-3">
              {PAYMENT_METHODS.map((m) => (
                <button
                  key={m.value}
                  onClick={() => setPayment(m.value)}
                  className={cn(
                    "flex flex-col items-start gap-1 rounded-xl border p-4 text-left transition-colors",
                    payment === m.value ? "border-brand-600 bg-brand-50/60 ring-1 ring-brand-600" : "border-brand-100 hover:border-brand-300"
                  )}
                  role="radio"
                  aria-checked={payment === m.value}
                >
                  <m.icon className="h-5 w-5 text-brand-600" aria-hidden />
                  <span className="text-sm font-semibold text-brand-900">{m.label}</span>
                  <span className="text-xs text-brand-400">{m.hint}</span>
                </button>
              ))}
              {payment === "card" && (
                <div className="sm:col-span-3">
                  <Field label="Card number" required hint="Demo gateway — any 12+ digit number works, e.g. 4242 4242 4242 4242">
                    <Input value={cardNumber} onChange={(e) => setCardNumber(e.target.value)} placeholder="4242 4242 4242 4242" inputMode="numeric" />
                  </Field>
                </div>
              )}
              {payment === "upi" && (
                <div className="sm:col-span-3">
                  <Field label="UPI ID" required hint="Demo gateway — any name@bank format works">
                    <Input value={upiId} onChange={(e) => setUpiId(e.target.value)} placeholder="you@upi" />
                  </Field>
                </div>
              )}
            </CardBody>
          </Card>

          {/* Notes */}
          <Card>
            <CardHeader title="Order notes (optional)" />
            <CardBody>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                maxLength={1000}
                placeholder="Delivery instructions, gift note…"
                className="w-full rounded-lg border border-brand-200 p-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
              />
            </CardBody>
          </Card>
        </div>

        {/* Summary */}
        <div>
          <Card className="sticky top-24">
            <CardHeader title={`Order summary (${cart.total_quantity} items)`} />
            <CardBody className="space-y-3 text-sm">
              <ul className="max-h-44 space-y-2 overflow-y-auto pr-1">
                {cart.items.map((i) => (
                  <li key={i.book_id} className="flex justify-between gap-3 text-brand-600">
                    <span className="line-clamp-1">{i.title} × {i.quantity}</span>
                    <span className="shrink-0 tabular-nums">{formatCurrency(i.line_total)}</span>
                  </li>
                ))}
              </ul>
              <div className="flex justify-between border-t border-brand-100 pt-3 text-brand-600">
                <span>Subtotal</span>
                <span className="font-medium">{formatCurrency(cart.subtotal)}</span>
              </div>
              {cart.discount_total > 0 && (
                <div className="flex justify-between text-emerald-600">
                  <span>Coupon ({cart.coupon?.code})</span>
                  <span className="font-medium">−{formatCurrency(cart.discount_total)}</span>
                </div>
              )}
              <div className="flex justify-between text-brand-600">
                <span>Shipping</span>
                <span className="font-medium">{cart.shipping_fee === 0 ? "Free" : formatCurrency(cart.shipping_fee)}</span>
              </div>
              {cart.tax_total > 0 && (
                <div className="flex justify-between text-brand-600">
                  <span>Tax</span>
                  <span className="font-medium">{formatCurrency(cart.tax_total)}</span>
                </div>
              )}
              <div className="flex justify-between border-t border-brand-100 pt-3 text-base font-bold text-brand-950">
                <span>Total</span>
                <span>{formatCurrency(cart.total)}</span>
              </div>
              <Button className="w-full" size="lg" disabled={!canPlace} loading={placeOrder.isPending} onClick={() => placeOrder.mutate()}>
                <CheckCircle2 className="h-5 w-5" aria-hidden />
                Place order
              </Button>
              <p className="text-center text-xs text-brand-400">
                By placing this order you agree to our terms. Payments are simulated in this demo build.
              </p>
            </CardBody>
          </Card>
        </div>
      </div>

      {/* Address modal */}
      <Modal open={addressModal} onClose={() => setAddressModal(false)} title={editingAddress ? "Edit address" : "New address"}>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Label">
            <Select value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })}>
              <option>Home</option>
              <option>Work</option>
              <option>Other</option>
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
          <Button variant="ghost" onClick={() => setAddressModal(false)}>Cancel</Button>
          <Button onClick={() => saveAddress.mutate()} loading={saveAddress.isPending} disabled={!addressFormValid}>
            {editingAddress ? "Save changes" : "Save address"}
          </Button>
        </div>
      </Modal>
    </div>
  );
}
