import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { IndianRupee, ShoppingCart, Users, Boxes, RefreshCcw, Ticket, MessageSquare, ScrollText } from "lucide-react";
import { OrderDetailPage } from "@/features/account/AccountPages";
import { toast } from "sonner";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { Field } from "@/components/ui/Input";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, PieChart, Pie, Cell, Legend,
} from "recharts";
import { adminApi } from "@/api/endpoints";
import { Card, CardBody, CardHeader, Badge, StatusBadge } from "@/components/ui/Card";
import { Pagination } from "@/components/ui/misc";
import { Table, THead, TH, TBody, TR, TD, TableSkeleton } from "@/components/ui/Table";
import { EmptyState, PageLoader } from "@/components/ui/states";
import { Select } from "@/components/ui/Input";
import { formatCurrency } from "@/utils";

/* ------------------------------------------------------------------ dashboard */

const DAY_OPTIONS = [7, 30, 90, 365];

export function AdminDashboardPage() {
  const [days, setDays] = useState(30);

  const { data: summary } = useQuery({
    queryKey: ["admin-summary", days],
    queryFn: () => adminApi.dashboardSummary(days).then((r) => r.data),
  });
  const { data: charts } = useQuery({
    queryKey: ["admin-charts", days],
    queryFn: () => adminApi.dashboardCharts(days).then((r) => r.data),
  });
  const { data: top } = useQuery({
    queryKey: ["admin-top", days],
    queryFn: () => adminApi.dashboardTop(days).then((r) => r.data),
  });

  if (!summary || !charts || !top) return <PageLoader label="Loading dashboard…" />;

  const COLORS = ["#1e3a5f", "#356cab", "#84add9", "#b3cde9", "#eab308", "#94a3b8"];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-serif text-2xl font-bold text-brand-900">Dashboard</h1>
          <p className="text-sm text-brand-400">Store performance at a glance</p>
        </div>
        <Select value={String(days)} onChange={(e) => setDays(Number(e.target.value))} className="w-40" aria-label="Time range">
          {DAY_OPTIONS.map((d) => (
            <option key={d} value={d}>Last {d} days</option>
          ))}
        </Select>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Kpi icon={IndianRupee} label="Revenue" value={formatCurrency(summary.total_revenue)} sub={`${formatCurrency(summary.revenue_today)} today`} />
        <Kpi icon={ShoppingCart} label="Orders" value={String(summary.total_orders)} sub={`${summary.orders_today} today`} />
        <Kpi icon={Users} label="Customers" value={String(summary.total_customers)} sub={`Avg ₹${summary.avg_order_value.toFixed(0)} / order`} />
        <Kpi icon={Boxes} label="Inventory value" value={formatCurrency(summary.inventory_value)} sub={`${summary.active_books} active titles`} />
      </div>

      {/* Alert strip */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MiniStat label="Pending orders" value={summary.pending_orders} tone={summary.pending_orders > 0 ? "warning" : "neutral"} />
        <MiniStat label="Open returns" value={summary.open_returns} tone={summary.open_returns > 0 ? "info" : "neutral"} />
        <MiniStat label="Low stock" value={summary.low_stock_count} tone={summary.low_stock_count > 0 ? "warning" : "neutral"} />
        <MiniStat label="Out of stock" value={summary.out_of_stock_count} tone={summary.out_of_stock_count > 0 ? "danger" : "neutral"} />
      </div>

      {/* Charts */}
      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader title="Revenue over time" />
          <CardBody className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={charts.revenue} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                <defs>
                  <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#356cab" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#356cab" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(v: string) => v.slice(5)} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: number) => formatCurrency(v)} />
                <Area type="monotone" dataKey="value" stroke="#1e3a5f" strokeWidth={2} fill="url(#rev)" />
              </AreaChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Orders over time" />
          <CardBody className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts.orders} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(v: string) => v.slice(5)} />
                <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#356cab" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        {/* Top books */}
        <Card className="lg:col-span-2">
          <CardHeader title="Top-selling books" />
          <CardBody className="p-0">
            {top.books.length === 0 ? (
              <p className="px-5 py-8 text-center text-sm text-brand-400">No sales in this period.</p>
            ) : (
              <Table className="min-w-0 border-0 shadow-none">
                <THead>
                  <tr><TH>Book</TH><TH className="text-right">Units</TH><TH className="text-right">Revenue</TH></tr>
                </THead>
                <TBody>
                  {top.books.map((b) => (
                    <TR key={b.title}>
                      <TD>
                        <p className="font-medium text-brand-900">{b.title}</p>
                        <p className="text-xs text-brand-400">{b.author_names}</p>
                      </TD>
                      <TD className="text-right tabular-nums">{b.units_sold}</TD>
                      <TD className="text-right tabular-nums">{formatCurrency(b.revenue)}</TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            )}
          </CardBody>
        </Card>

        {/* Status distribution */}
        <Card>
          <CardHeader title="Order status mix" />
          <CardBody className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={top.status_distribution} dataKey="count" nameKey="status" innerRadius={50} outerRadius={80} paddingAngle={3}>
                  {top.status_distribution.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend formatter={(v: string) => v.replaceAll("_", " ")} wrapperStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>
      </div>

      {/* Customer growth */}
      <Card>
        <CardHeader title="New customers" />
        <CardBody className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={charts.customer_growth}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(v: string) => v.slice(5)} />
              <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip />
              <Area type="monotone" dataKey="count" stroke="#0d9488" fill="#0d948820" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </CardBody>
      </Card>
    </div>
  );
}

function Kpi({ icon: Icon, label, value, sub }: { icon: any; label: string; value: string; sub: string }) {
  return (
    <Card className="p-4">
      <div className="flex items-center gap-3">
        <div className="rounded-lg bg-brand-50 p-2.5 text-brand-700">
          <Icon className="h-5 w-5" aria-hidden />
        </div>
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-wide text-brand-400">{label}</p>
          <p className="truncate text-lg font-bold text-brand-950">{value}</p>
        </div>
      </div>
      <p className="mt-2 text-xs text-brand-400">{sub}</p>
    </Card>
  );
}

function MiniStat({ label, value, tone }: { label: string; value: number; tone: "neutral" | "warning" | "info" | "danger" }) {
  return (
    <Card className="flex items-center justify-between p-4">
      <p className="text-sm text-brand-500">{label}</p>
      <Badge tone={tone === "neutral" ? "neutral" : tone}>{value}</Badge>
    </Card>
  );
}

/* ------------------------------------------------------------------ books admin */

const EMPTY_BOOK = {
  title: "", isbn: "", description: "", language: "English", format: "paperback",
  pages: "", published_year: "", publisher_id: "", price: "", discount_percent: 0,
  stock_quantity: 0, low_stock_threshold: 5, is_active: true, is_featured: false,
  author_ids: [] as number[], category_ids: [] as number[],
};

export function AdminBooksPage() {
  const queryClient = useQueryClient();
  const [q, setQ] = useState("");
  const [modal, setModal] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState({ ...EMPTY_BOOK });
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [coverFile, setCoverFile] = useState<File | null>(null);

  const { data: books, isLoading } = useQuery({
    queryKey: ["admin-books", q],
    queryFn: () => adminApi.books({ q, page_size: 60 }).then((r) => r.data),
  });
  const { data: authors } = useQuery({ queryKey: ["admin-authors"], queryFn: () => adminApi.authors().then((r) => r.data) });
  const { data: categories } = useQuery({ queryKey: ["admin-categories"], queryFn: () => adminApi.categories().then((r) => r.data) });
  const { data: publishers } = useQuery({ queryKey: ["admin-publishers"], queryFn: () => adminApi.publishers().then((r) => r.data) });

  const save = useMutation({
    mutationFn: async () => {
      const payload: Record<string, unknown> = {
        title: form.title,
        isbn: form.isbn || null,
        description: form.description || null,
        language: form.language,
        format: form.format,
        pages: form.pages ? Number(form.pages) : null,
        published_year: form.published_year ? Number(form.published_year) : null,
        publisher_id: form.publisher_id ? Number(form.publisher_id) : null,
        price: Number(form.price),
        discount_percent: Number(form.discount_percent),
        is_active: form.is_active,
        is_featured: form.is_featured,
        author_ids: form.author_ids,
        category_ids: form.category_ids,
      };
      if (editId === null) {
        payload.stock_quantity = Number(form.stock_quantity);
        payload.low_stock_threshold = Number(form.low_stock_threshold);
      }
      const book = editId === null
        ? (await adminApi.createBook(payload)).data
        : (await adminApi.updateBook(editId, payload)).data;
      if (coverFile) await adminApi.uploadCover(book.id, coverFile);
      return book;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-books"] });
      queryClient.invalidateQueries({ queryKey: ["books"] });
      editId ? toast.success("Book updated") : toast.success("Book created");
      setModal(false);
      setCoverFile(null);
    },
    onError: (err: any) => toast.error(err?.response?.data?.error?.message ?? "Could not save book"),
  });

  const archive = useMutation({
    mutationFn: (id: number) => adminApi.deleteBook(id, false),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-books"] });
      queryClient.invalidateQueries({ queryKey: ["books"] });
      toast.success("Book archived");
      setDeleteId(null);
    },
    onError: (err: any) => toast.error(err?.response?.data?.error?.message ?? "Could not archive book"),
  });

  const openEdit = async (id: number) => {
    const book = (await adminApi.book(id)).data;
    setEditId(id);
    setForm({
      title: book.title, isbn: book.isbn ?? "", description: book.description ?? "",
      language: book.language, format: book.format,
      pages: book.pages ? String(book.pages) : "", published_year: book.published_year ? String(book.published_year) : "",
      publisher_id: book.publisher ? String(book.publisher.id) : "",
      price: String(book.price), discount_percent: book.discount_percent,
      stock_quantity: book.stock_quantity, low_stock_threshold: book.low_stock_threshold,
      is_active: book.is_active, is_featured: book.is_featured,
      author_ids: book.authors.map((a) => a.id), category_ids: book.categories.map((c) => c.id),
    });
    setCoverFile(null);
    setModal(true);
  };

  const valid = form.title.trim().length > 0 && Number(form.price) > 0;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-serif text-2xl font-bold text-brand-900">Books</h1>
          <p className="text-sm text-brand-400">Manage the catalog</p>
        </div>
        <div className="flex gap-2">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search books…"
            className="h-10 rounded-lg border border-brand-200 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
            aria-label="Search books"
          />
          <Button onClick={() => { setEditId(null); setForm({ ...EMPTY_BOOK }); setModal(true); }}>Add book</Button>
        </div>
      </div>

      {isLoading ? (
        <TableSkeleton />
      ) : !books || books.length === 0 ? (
        <EmptyState title="No books found" />
      ) : (
        <Table>
          <THead>
            <tr>
              <TH>Book</TH><TH>Price</TH><TH>Stock</TH><TH>Rating</TH><TH>Status</TH><TH className="text-right">Actions</TH>
            </tr>
          </THead>
          <TBody>
            {books.map((b) => (
              <TR key={b.id}>
                <TD>
                  <div className="flex items-center gap-3">
                    <img src={b.cover_image ? `/${b.cover_image}` : undefined} alt="" className="h-12 w-8 rounded bg-brand-50 object-cover" />
                    <div>
                      <p className="font-medium text-brand-900">{b.title}</p>
                      <p className="text-xs text-brand-400">{b.authors.map((a) => a.name).join(", ")}</p>
                    </div>
                  </div>
                </TD>
                <TD>
                  <span className="tabular-nums">₹{b.effective_price.toFixed(2)}</span>
                  {b.discount_percent > 0 && <span className="ml-1 text-xs text-brand-300 line-through">₹{b.price.toFixed(0)}</span>}
                </TD>
                <TD className="tabular-nums">{b.stock_quantity}</TD>
                <TD className="tabular-nums">{b.rating_avg.toFixed(1)} ({b.rating_count})</TD>
                <TD>
                  <div className="flex gap-1">
                    <Badge tone={b.is_active ? "success" : "neutral"}>{b.is_active ? "Active" : "Archived"}</Badge>
                    {b.is_featured && <Badge tone="accent">Featured</Badge>}
                  </div>
                </TD>
                <TD className="text-right">
                  <div className="flex justify-end gap-2">
                    <Link to={`/books/${b.slug}`} className="text-xs font-medium text-brand-500 hover:text-brand-800">View</Link>
                    <button onClick={() => openEdit(b.id)} className="text-xs font-medium text-brand-600 hover:text-brand-800">Edit</button>
                    <button onClick={() => setDeleteId(b.id)} className="text-xs font-medium text-red-500 hover:text-red-700" disabled={!b.is_active}>Archive</button>
                  </div>
                </TD>
              </TR>
            ))}
          </TBody>
        </Table>
      )}

      <BookForm
        open={modal}
        onClose={() => setModal(false)}
        form={form}
        setForm={setForm}
        authors={authors ?? []}
        categories={categories ?? []}
        publishers={publishers ?? []}
        isEdit={editId !== null}
        valid={valid}
        saving={save.isPending}
        onSubmit={() => save.mutate()}
        coverFile={coverFile}
        setCoverFile={setCoverFile}
      />

      <ConfirmArchiving
        open={deleteId !== null}
        onClose={() => setDeleteId(null)}
        onConfirm={() => deleteId && archive.mutate(deleteId)}
        loading={archive.isPending}
      />
    </div>
  );
}

function ConfirmArchiving(props: { open: boolean; onClose: () => void; onConfirm: () => void; loading: boolean }) {
  return (
    <ConfirmDialog
      {...props}
      title="Archive this book?"
      message="Archived books are hidden from the storefront but remain linked to past orders. You can re-activate them any time."
      confirmLabel="Archive book"
      danger
    />
  );
}

function BookForm({
  open, onClose, form, setForm, authors, categories, publishers, isEdit, valid, saving, onSubmit, coverFile, setCoverFile,
}: any) {
  return (
    <Modal open={open} onClose={onClose} title={isEdit ? "Edit book" : "Add book"} size="lg">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <Field label="Title" required>
            <input value={form.title} onChange={(e: any) => setForm({ ...form, title: e.target.value })} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" />
          </Field>
        </div>
        <Field label="Price (₹)" required>
          <input type="number" min="0" step="0.01" value={form.price} onChange={(e: any) => setForm({ ...form, price: e.target.value })} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" />
        </Field>
        <Field label="Discount %">
          <input type="number" min="0" max="100" value={form.discount_percent} onChange={(e: any) => setForm({ ...form, discount_percent: e.target.value })} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" />
        </Field>
        <Field label="ISBN">
          <input value={form.isbn} onChange={(e: any) => setForm({ ...form, isbn: e.target.value })} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" />
        </Field>
        <Field label="Publisher">
          <select value={form.publisher_id} onChange={(e: any) => setForm({ ...form, publisher_id: e.target.value })} className="h-10 w-full rounded-lg border border-brand-200 px-2 text-sm">
            <option value="">—</option>
            {publishers.map((p: any) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </Field>
        <Field label="Pages">
          <input type="number" value={form.pages} onChange={(e: any) => setForm({ ...form, pages: e.target.value })} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" />
        </Field>
        <Field label="Published year">
          <input type="number" value={form.published_year} onChange={(e: any) => setForm({ ...form, published_year: e.target.value })} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" />
        </Field>
        <Field label="Format">
          <select value={form.format} onChange={(e: any) => setForm({ ...form, format: e.target.value })} className="h-10 w-full rounded-lg border border-brand-200 px-2 text-sm">
            <option value="paperback">Paperback</option>
            <option value="hardcover">Hardcover</option>
          </select>
        </Field>
        <Field label="Language">
          <input value={form.language} onChange={(e: any) => setForm({ ...form, language: e.target.value })} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" />
        </Field>
        {!isEdit && (
          <>
            <Field label="Initial stock">
              <input type="number" min="0" value={form.stock_quantity} onChange={(e: any) => setForm({ ...form, stock_quantity: e.target.value })} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" />
            </Field>
            <Field label="Low-stock threshold">
              <input type="number" min="0" value={form.low_stock_threshold} onChange={(e: any) => setForm({ ...form, low_stock_threshold: e.target.value })} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" />
            </Field>
          </>
        )}
        <div className="sm:col-span-2">
          <Field label="Authors">
            <MultiCheck
              options={authors}
              selected={form.author_ids}
              onChange={(ids: number[]) => setForm({ ...form, author_ids: ids })}
            />
          </Field>
        </div>
        <div className="sm:col-span-2">
          <Field label="Categories">
            <MultiCheck
              options={categories}
              selected={form.category_ids}
              onChange={(ids: number[]) => setForm({ ...form, category_ids: ids })}
            />
          </Field>
        </div>
        <div className="sm:col-span-2">
          <Field label="Description">
            <textarea value={form.description} onChange={(e: any) => setForm({ ...form, description: e.target.value })} rows={3} className="w-full rounded-lg border border-brand-200 p-3 text-sm" />
          </Field>
        </div>
        <Field label="Cover image">
          <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(e: any) => setCoverFile(e.target.files?.[0] ?? null)} className="text-sm" />
          {coverFile && <p className="mt-1 text-xs text-emerald-600">{coverFile.name} ready</p>}
        </Field>
        <div className="flex items-center gap-6 pt-6">
          <label className="flex items-center gap-2 text-sm text-brand-700">
            <input type="checkbox" checked={form.is_active} onChange={(e: any) => setForm({ ...form, is_active: e.target.checked })} className="h-4 w-4" />
            Active
          </label>
          <label className="flex items-center gap-2 text-sm text-brand-700">
            <input type="checkbox" checked={form.is_featured} onChange={(e: any) => setForm({ ...form, is_featured: e.target.checked })} className="h-4 w-4" />
            Featured
          </label>
        </div>
      </div>
      <div className="mt-5 flex justify-end gap-2">
        <Button variant="ghost" onClick={onClose} type="button">Cancel</Button>
        <Button onClick={onSubmit} loading={saving} disabled={!valid} type="button">{isEdit ? "Save changes" : "Create book"}</Button>
      </div>
    </Modal>
  );
}

function MultiCheck({ options, selected, onChange }: { options: { id: number; name: string }[]; selected: number[]; onChange: (ids: number[]) => void }) {
  const toggle = (id: number) => {
    onChange(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]);
  };
  return (
    <div className="max-h-36 overflow-y-auto rounded-lg border border-brand-200 p-2">
      <div className="flex flex-wrap gap-2">
        {options.map((o) => (
          <button
            key={o.id}
            type="button"
            onClick={() => toggle(o.id)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              selected.includes(o.id) ? "bg-brand-700 text-white" : "bg-brand-50 text-brand-600 hover:bg-brand-100"
            }`}
          >
            {o.name}
          </button>
        ))}
        {options.length === 0 && <span className="text-xs text-brand-300">Nothing available</span>}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ inventory */

export function AdminInventoryPage() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<"all" | "low" | "out">("all");
  const [q, setQ] = useState("");
  const [adjust, setAdjust] = useState<{ bookId: number; title: string; stock: number } | null>(null);
  const [change, setChange] = useState("");
  const [note, setNote] = useState("");
  const [history, setHistory] = useState<{ bookId: number; title: string } | null>(null);

  const { data: rows, isLoading } = useQuery({
    queryKey: ["admin-inventory", filter, q],
    queryFn: () => adminApi.inventory({ filter, q, page_size: 60 }).then((r) => r.data),
  });

  const { data: transactions } = useQuery({
    queryKey: ["admin-inv-transactions", history?.bookId],
    queryFn: () => adminApi.inventoryTransactions(history!.bookId).then((r) => r.data),
    enabled: history !== null,
  });

  const doAdjust = useMutation({
    mutationFn: () => adminApi.adjustInventory(adjust!.bookId, { change: Number(change), note: note || undefined }),
    onSuccess: () => {
      toast.success("Stock adjusted");
      queryClient.invalidateQueries({ queryKey: ["admin-inventory"] });
      queryClient.invalidateQueries({ queryKey: ["admin-summary"] });
      setAdjust(null);
      setChange("");
      setNote("");
    },
    onError: (err: any) => toast.error(err?.response?.data?.error?.message ?? "Could not adjust stock"),
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-serif text-2xl font-bold text-brand-900">Inventory</h1>
          <p className="text-sm text-brand-400">Stock levels and movement ledger</p>
        </div>
        <div className="flex gap-2">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search…"
            className="h-10 rounded-lg border border-brand-200 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
            aria-label="Search inventory"
          />
          <Select value={filter} onChange={(e) => setFilter(e.target.value as any)} className="w-36" aria-label="Filter">
            <option value="all">All</option>
            <option value="low">Low stock</option>
            <option value="out">Out of stock</option>
          </Select>
        </div>
      </div>

      {isLoading ? (
        <TableSkeleton />
      ) : !rows || rows.length === 0 ? (
        <EmptyState title="Nothing here" description="No inventory rows match this filter." />
      ) : (
        <Table>
          <THead>
            <tr><TH>Book</TH><TH className="text-right">Stock</TH><TH className="text-right">Reserved</TH><TH className="text-right">Available</TH><TH>Status</TH><TH className="text-right">Actions</TH></tr>
          </THead>
          <TBody>
            {rows.map((r) => (
              <TR key={r.book_id}>
                <TD>
                  <p className="font-medium text-brand-900">{r.title}</p>
                  <p className="text-xs text-brand-400">{r.is_active ? "Active" : "Archived"}</p>
                </TD>
                <TD className="text-right tabular-nums">{r.stock_quantity}</TD>
                <TD className="text-right tabular-nums">{r.reserved_quantity}</TD>
                <TD className="text-right tabular-nums font-medium">{r.available_quantity}</TD>
                <TD>
                  {r.stock_quantity <= 0 ? (
                    <Badge tone="danger">Out of stock</Badge>
                  ) : r.is_low_stock ? (
                    <Badge tone="warning">Low (≤{r.low_stock_threshold})</Badge>
                  ) : (
                    <Badge tone="success">Healthy</Badge>
                  )}
                </TD>
                <TD className="text-right">
                  <div className="flex justify-end gap-2">
                    <button onClick={() => setHistory({ bookId: r.book_id, title: r.title })} className="text-xs font-medium text-brand-500 hover:text-brand-800">History</button>
                    <button onClick={() => setAdjust({ bookId: r.book_id, title: r.title, stock: r.stock_quantity })} className="text-xs font-medium text-brand-600 hover:text-brand-800">Adjust</button>
                  </div>
                </TD>
              </TR>
            ))}
          </TBody>
        </Table>
      )}

      {/* Adjust modal */}
      <Modal open={adjust !== null} onClose={() => setAdjust(null)} title={`Adjust stock — ${adjust?.title ?? ""}`}>
        <p className="text-sm text-brand-500">Current stock: <strong>{adjust?.stock}</strong></p>
        <div className="mt-4 space-y-3">
          <Field label="Change (use negative to reduce)" required hint="e.g. 10 to add ten copies, -3 to remove three">
            <input type="number" value={change} onChange={(e) => setChange(e.target.value)} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" />
          </Field>
          <Field label="Note (optional)">
            <input value={note} onChange={(e) => setNote(e.target.value)} maxLength={255} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" placeholder="Restock, damage write-off…" />
          </Field>
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setAdjust(null)}>Cancel</Button>
          <Button onClick={() => doAdjust.mutate()} loading={doAdjust.isPending} disabled={!change || Number(change) === 0}>Apply adjustment</Button>
        </div>
      </Modal>

      {/* History modal */}
      <Modal open={history !== null} onClose={() => setHistory(null)} title={`Stock history — ${history?.title ?? ""}`} size="lg">
        {!transactions || transactions.length === 0 ? (
          <p className="py-6 text-center text-sm text-brand-400">No movements recorded.</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {transactions.map((t) => (
              <li key={t.id} className="flex items-center justify-between gap-3 rounded-lg border border-brand-50 px-3 py-2">
                <div>
                  <span className={`font-bold tabular-nums ${t.change > 0 ? "text-emerald-600" : "text-red-600"}`}>
                    {t.change > 0 ? "+" : ""}{t.change}
                  </span>
                  <span className="ml-2 capitalize text-brand-600">{t.change_type.replaceAll("_", " ").toLowerCase()}</span>
                  {t.note && <p className="text-xs text-brand-400">{t.note}</p>}
                </div>
                <div className="text-right text-xs text-brand-400">
                  <p>Balance: {t.balance_after}</p>
                  <p>{new Date(t.created_at).toLocaleString("en-IN")}</p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Modal>
    </div>
  );
}

/* ------------------------------------------------------------------ taxonomy */

export function AdminTermsPage() {
  const queryClient = useQueryClient();
  const [kind, setKind] = useState<"categories" | "authors" | "publishers">("categories");
  const [modal, setModal] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [deleteId, setDeleteId] = useState<number | null>(null);

  const { data: items, isLoading } = useQuery({
    queryKey: ["admin-terms", kind],
    queryFn: () => {
      const fn = kind === "categories" ? adminApi.categories : kind === "authors" ? adminApi.authors : adminApi.publishers;
      return fn().then((r) => r.data as { id: number; name: string; description?: string | null }[]);
    },
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["admin-terms"] });
    queryClient.invalidateQueries({ queryKey: ["facets"] });
  };

  const save = useMutation({
    mutationFn: () => {
      const payload = description ? { name, description } : { name };
      return editId ? adminApi.updateTerm(kind, editId, payload) : adminApi.createTerm(kind, payload);
    },
    onSuccess: () => {
      toast.success(editId ? "Updated" : "Created");
      setModal(false);
      invalidate();
    },
    onError: (err: any) => toast.error(err?.response?.data?.error?.message ?? "Could not save"),
  });

  const remove = useMutation({
    mutationFn: (id: number) => adminApi.deleteTerm(kind, id),
    onSuccess: () => {
      toast.success("Deleted");
      setDeleteId(null);
      invalidate();
    },
    onError: (err: any) => toast.error(err?.response?.data?.error?.message ?? "Cannot delete"),
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-serif text-2xl font-bold text-brand-900">Taxonomy</h1>
          <p className="text-sm text-brand-400">Categories, authors and publishers</p>
        </div>
        <div className="flex gap-2">
          <Select value={kind} onChange={(e) => setKind(e.target.value as any)} className="w-40" aria-label="Kind">
            <option value="categories">Categories</option>
            <option value="authors">Authors</option>
            <option value="publishers">Publishers</option>
          </Select>
          <Button onClick={() => { setEditId(null); setName(""); setDescription(""); setModal(true); }}>Add</Button>
        </div>
      </div>

      {isLoading ? (
        <TableSkeleton />
      ) : (
        <Table>
          <THead><tr><TH>Name</TH><TH className="text-right">Actions</TH></tr></THead>
          <TBody>
            {items?.map((t) => (
              <TR key={t.id}>
                <TD>
                  <p className="font-medium text-brand-900">{t.name}</p>
                  {t.description && <p className="text-xs text-brand-400">{t.description}</p>}
                </TD>
                <TD className="text-right">
                  <div className="flex justify-end gap-2">
                    <button onClick={() => { setEditId(t.id); setName(t.name); setDescription(t.description ?? ""); setModal(true); }} className="text-xs font-medium text-brand-600 hover:text-brand-800">Edit</button>
                    <button onClick={() => setDeleteId(t.id)} className="text-xs font-medium text-red-500 hover:text-red-700">Delete</button>
                  </div>
                </TD>
              </TR>
            ))}
          </TBody>
        </Table>
      )}

      <Modal open={modal} onClose={() => setModal(false)} title={editId ? "Edit" : "Create"}>
        <div className="space-y-3">
          <Field label="Name" required>
            <input value={name} onChange={(e) => setName(e.target.value)} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" />
          </Field>
          {kind !== "publishers" && (
            <Field label="Description">
              <input value={description} onChange={(e) => setDescription(e.target.value)} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" />
            </Field>
          )}
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setModal(false)}>Cancel</Button>
          <Button onClick={() => save.mutate()} loading={save.isPending} disabled={!name.trim()}>Save</Button>
        </div>
      </Modal>

      <ConfirmDialog
        open={deleteId !== null}
        onClose={() => setDeleteId(null)}
        onConfirm={() => deleteId && remove.mutate(deleteId)}
        title="Delete entry?"
        message="Entries linked to books cannot be deleted — this will be rejected with an explanation."
        confirmLabel="Delete"
        danger
        loading={remove.isPending}
      />
    </div>
  );
}

/* ------------------------------------------------------------------ orders */

const ORDER_STATUSES = ["pending", "confirmed", "processing", "shipped", "out_for_delivery", "delivered", "cancelled", "returned"] as const;
const NEXT_STATUSES: Record<string, string[]> = {
  pending: ["confirmed", "processing", "cancelled"],
  confirmed: ["processing", "shipped", "cancelled"],
  processing: ["shipped", "cancelled"],
  shipped: ["out_for_delivery", "delivered"],
  out_for_delivery: ["delivered"],
  delivered: [],
  cancelled: [],
  returned: [],
};

export function AdminOrdersPage() {
  const [status, setStatus] = useState("");
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const { data, isLoading } = useQuery({
    queryKey: ["admin-orders", status, q, page],
    queryFn: () => adminApi.orders({ status: status || undefined, q: q || undefined, page, page_size: 15 }).then((r) => r.data),
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-serif text-2xl font-bold text-brand-900">Orders</h1>
          <p className="text-sm text-brand-400">{data ? `${data.total} orders` : "All customer orders"}</p>
        </div>
        <div className="flex gap-2">
          <input
            value={q}
            onChange={(e) => { setQ(e.target.value); setPage(1); }}
            placeholder="Order number…"
            className="h-10 rounded-lg border border-brand-200 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
            aria-label="Search orders"
          />
          <Select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} className="w-40" aria-label="Status filter">
            <option value="">All statuses</option>
            {ORDER_STATUSES.map((s) => <option key={s} value={s}>{s.replaceAll("_", " ")}</option>)}
          </Select>
        </div>
      </div>

      {isLoading ? (
        <TableSkeleton />
      ) : !data || data.items.length === 0 ? (
        <EmptyState title="No orders found" />
      ) : (
        <>
          <Table>
            <THead>
              <tr><TH>Order</TH><TH>Items</TH><TH>Total</TH><TH>Payment</TH><TH>Status</TH><TH className="text-right">Actions</TH></tr>
            </THead>
            <TBody>
              {data.items.map((o) => (
                <TR key={o.id}>
                  <TD>
                    <Link to={`/admin/orders/${o.order_number}`} className="font-medium text-brand-800 hover:text-brand-600">{o.order_number}</Link>
                    <p className="text-xs text-brand-400">{new Date(o.placed_at).toLocaleDateString("en-IN")}</p>
                  </TD>
                  <TD className="tabular-nums">{o.items.length}</TD>
                  <TD className="tabular-nums font-medium">₹{o.total.toFixed(2)}</TD>
                  <TD>
                    <div className="flex gap-1">
                      <Badge>{o.payment_method.toUpperCase()}</Badge>
                      <Badge tone={o.payment_status === "paid" ? "success" : o.payment_status === "refunded" ? "neutral" : "warning"}>{o.payment_status}</Badge>
                    </div>
                  </TD>
                  <TD><StatusBadge status={o.status} /></TD>
                  <TD className="text-right">
                    <Link to={`/admin/orders/${o.order_number}`} className="text-xs font-medium text-brand-600 hover:text-brand-800">Manage →</Link>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
          <Pagination page={data.page} pages={data.pages} onChange={setPage} />
        </>
      )}
    </div>
  );
}

export function AdminOrderManagePage() {
  const { orderNumber = "" } = useParams();
  const queryClient = useQueryClient();
  const [note, setNote] = useState("");

  const { data: order, isLoading } = useQuery({
    queryKey: ["admin-order", orderNumber],
    queryFn: () => adminApi.order(orderNumber).then((r) => r.data),
  });

  const updateStatus = useMutation({
    mutationFn: (status: string) => adminApi.updateStatus(orderNumber, status, note || undefined),
    onSuccess: () => {
      toast.success("Status updated");
      setNote("");
      queryClient.invalidateQueries({ queryKey: ["admin-order", orderNumber] });
      queryClient.invalidateQueries({ queryKey: ["admin-orders"] });
    },
    onError: (err: any) => toast.error(err?.response?.data?.error?.message ?? "Transition not allowed"),
  });

  if (isLoading || !order) return <PageLoader label="Loading order…" />;

  const nexts = NEXT_STATUSES[order.status] ?? [];

  return (
    <div className="space-y-5">
      <Link to="/admin/orders" className="inline-block text-sm text-brand-500 hover:text-brand-800">← All orders</Link>

      <div className="grid gap-5 lg:grid-cols-[1fr_340px]">
        <OrderDetailPage adminMode />

        <Card className="sticky top-24 h-fit">
          <CardHeader title="Manage status" />
          <CardBody className="space-y-4">
            <div>
              <p className="text-sm text-brand-500">Current</p>
              <StatusBadge status={order.status} className="mt-1" />
            </div>
            <div>
              <p className="mb-2 text-sm font-medium text-brand-700">Advance to</p>
              {nexts.length === 0 ? (
                <p className="text-sm text-brand-400">This order is in a terminal state.</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {nexts.map((s) => (
                    <Button key={s} size="sm" variant={s === "cancelled" ? "danger" : "outline"} onClick={() => updateStatus.mutate(s)} loading={updateStatus.isPending}>
                      {s.replaceAll("_", " ")}
                    </Button>
                  ))}
                </div>
              )}
            </div>
            <Field label="Note (attached to this change)">
              <input value={note} onChange={(e) => setNote(e.target.value)} maxLength={255} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" placeholder="Shipped via BlueDart…" />
            </Field>
            <p className="text-xs text-brand-400">
              The customer is notified (in-app + email) on every status change. COD payments are captured automatically on delivery.
            </p>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ returns */

export function AdminReturnsPage() {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState("");
  const [type, setType] = useState("");
  const { data: requests, isLoading } = useQuery({
    queryKey: ["admin-returns", status, type],
    queryFn: () => adminApi.returns({ status: status || undefined, type: type || undefined }).then((r) => r.data as any[]),
  });

  const decide = useMutation({
    mutationFn: ({ id, decision }: { id: number; decision: "approve" | "reject" | "complete" }) =>
      adminApi.decideReturn(id, decision),
    onSuccess: () => {
      toast.success("Decision recorded");
      queryClient.invalidateQueries({ queryKey: ["admin-returns"] });
      queryClient.invalidateQueries({ queryKey: ["admin-summary"] });
    },
    onError: (err: any) => toast.error(err?.response?.data?.error?.message ?? "Could not record decision"),
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-serif text-2xl font-bold text-brand-900">Returns & replacements</h1>
          <p className="text-sm text-brand-400">Review and decide customer requests</p>
        </div>
        <div className="flex gap-2">
          <Select value={type} onChange={(e) => setType(e.target.value)} className="w-40" aria-label="Type">
            <option value="">All types</option>
            <option value="return">Returns</option>
            <option value="replacement">Replacements</option>
          </Select>
          <Select value={status} onChange={(e) => setStatus(e.target.value)} className="w-40" aria-label="Status">
            <option value="">All statuses</option>
            <option value="requested">Requested</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="completed">Completed</option>
          </Select>
        </div>
      </div>

      {isLoading ? (
        <TableSkeleton />
      ) : !requests || requests.length === 0 ? (
        <EmptyState icon={<RefreshCcw className="h-10 w-10" aria-hidden />} title="No requests" description="Nothing to review right now." />
      ) : (
        <div className="space-y-4">
          {requests.map((r) => (
            <Card key={r.id} className="p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-brand-900">{r.return_number}</span>
                    <StatusBadge status={r.status} />
                    <Badge tone={r.type === "return" ? "warning" : "accent"}>{r.type}</Badge>
                  </div>
                  <p className="mt-1 text-sm text-brand-500">
                    Order <Link to={`/admin/orders/${r.order_number}`} className="font-medium text-brand-700 hover:underline">{r.order_number}</Link>
                    {" · "}{r.reason.replaceAll("_", " ")} · requested {new Date(r.created_at).toLocaleDateString("en-IN")}
                  </p>
                  {r.description && <p className="mt-1 max-w-xl text-sm text-brand-500">“{r.description}”</p>}
                </div>
                <div className="text-right">
                  {r.refund_amount != null && (
                    <p className="font-bold text-brand-900">₹{r.refund_amount.toFixed(2)}</p>
                  )}
                  <p className="text-xs capitalize text-brand-400">refund: {r.refund_status}</p>
                </div>
              </div>

              <div className="mt-3 flex flex-wrap gap-2 text-xs text-brand-500">
                {r.items.map((i: any) => (
                  <span key={i.order_item_id} className="rounded-full bg-brand-50 px-2.5 py-1">
                    {i.title} × {i.quantity}
                  </span>
                ))}
              </div>

              {r.status === "requested" && (
                <div className="mt-4 flex gap-2">
                  <Button size="sm" onClick={() => decide.mutate({ id: r.id, decision: "approve" })} loading={decide.isPending}>Approve</Button>
                  <Button size="sm" variant="danger" onClick={() => decide.mutate({ id: r.id, decision: "reject" })} loading={decide.isPending}>Reject</Button>
                </div>
              )}
              {r.status === "approved" && (
                <div className="mt-4">
                  <Button size="sm" variant="secondary" onClick={() => decide.mutate({ id: r.id, decision: "complete" })} loading={decide.isPending}>
                    Mark completed
                  </Button>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ users */

export function AdminUsersPage() {
  const queryClient = useQueryClient();
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const { data, isLoading } = useQuery({
    queryKey: ["admin-users", q, page],
    queryFn: () => adminApi.users({ q, page, page_size: 15 }).then((r) => r.data),
  });

  const update = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Record<string, unknown> }) => adminApi.updateUser(id, data),
    onSuccess: () => {
      toast.success("User updated");
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
    onError: (err: any) => toast.error(err?.response?.data?.error?.message ?? "Could not update user"),
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-serif text-2xl font-bold text-brand-900">Users</h1>
          <p className="text-sm text-brand-400">{data ? `${data.total} registered accounts` : "Customer accounts"}</p>
        </div>
        <input
          value={q}
          onChange={(e) => { setQ(e.target.value); setPage(1); }}
          placeholder="Search name, email, username…"
          className="h-10 w-64 rounded-lg border border-brand-200 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
          aria-label="Search users"
        />
      </div>

      {isLoading ? (
        <TableSkeleton />
      ) : !data || data.items.length === 0 ? (
        <EmptyState title="No users found" />
      ) : (
        <>
          <Table>
            <THead>
              <tr><TH>User</TH><TH>Role</TH><TH>Orders</TH><TH>Spent</TH><TH>Status</TH><TH className="text-right">Actions</TH></tr>
            </THead>
            <TBody>
              {data.items.map((u) => (
                <TR key={u.id}>
                  <TD>
                    <div className="flex items-center gap-3">
                      <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-100 text-sm font-semibold text-brand-700">
                        {u.full_name.charAt(0)}
                      </span>
                      <div>
                        <p className="font-medium text-brand-900">{u.full_name}</p>
                        <p className="text-xs text-brand-400">{u.email}</p>
                      </div>
                    </div>
                  </TD>
                  <TD>
                    <Select
                      className="w-32"
                      value={u.role}
                      onChange={(e) => update.mutate({ id: u.id, data: { role: e.target.value } })}
                      aria-label={`Role for ${u.full_name}`}
                    >
                      <option value="customer">customer</option>
                      <option value="admin">admin</option>
                    </Select>
                  </TD>
                  <TD className="tabular-nums">{u.order_count}</TD>
                  <TD className="tabular-nums">₹{u.total_spent.toFixed(0)}</TD>
                  <TD>
                    <Badge tone={u.is_active ? "success" : "danger"}>{u.is_active ? "Active" : "Deactivated"}</Badge>
                    {!u.is_verified && <Badge tone="warning" className="ml-1">Unverified</Badge>}
                  </TD>
                  <TD className="text-right">
                    {u.is_active ? (
                      <button onClick={() => update.mutate({ id: u.id, data: { is_active: false } })} className="text-xs font-medium text-red-500 hover:text-red-700">
                        Deactivate
                      </button>
                    ) : (
                      <button onClick={() => update.mutate({ id: u.id, data: { is_active: true } })} className="text-xs font-medium text-emerald-600 hover:text-emerald-800">
                        Reactivate
                      </button>
                    )}
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
          <Pagination page={data.page} pages={data.pages} onChange={setPage} />
        </>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ coupons */

export function AdminCouponsPage() {
  const queryClient = useQueryClient();
  const [modal, setModal] = useState(false);
  const [form, setForm] = useState({ code: "", description: "", discount_type: "percent", value: "", min_order_amount: "", max_discount_amount: "", usage_limit: "", expires_at: "" });

  const { data: coupons, isLoading } = useQuery({ queryKey: ["admin-coupons"], queryFn: () => adminApi.coupons().then((r) => r.data) });

  const save = useMutation({
    mutationFn: () =>
      adminApi.createCoupon({
        code: form.code,
        description: form.description || undefined,
        discount_type: form.discount_type,
        value: Number(form.value),
        min_order_amount: Number(form.min_order_amount || 0),
        max_discount_amount: form.max_discount_amount ? Number(form.max_discount_amount) : null,
        usage_limit: form.usage_limit ? Number(form.usage_limit) : null,
        expires_at: form.expires_at ? new Date(form.expires_at).toISOString() : null,
      }),
    onSuccess: () => {
      toast.success("Coupon created");
      setModal(false);
      queryClient.invalidateQueries({ queryKey: ["admin-coupons"] });
    },
    onError: (err: any) => toast.error(err?.response?.data?.error?.message ?? "Could not create coupon"),
  });

  const toggle = useMutation({
    mutationFn: (c: any) => adminApi.updateCoupon(c.id, { is_active: !c.is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-coupons"] }),
  });

  const remove = useMutation({
    mutationFn: (id: number) => adminApi.deleteCoupon(id),
    onSuccess: (r: any) => {
      toast.success(r.data.deactivated ? "Coupon deactivated (already in use)" : "Coupon deleted");
      queryClient.invalidateQueries({ queryKey: ["admin-coupons"] });
    },
  });

  const valid = form.code.trim().length >= 3 && Number(form.value) > 0;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-serif text-2xl font-bold text-brand-900">Coupons</h1>
          <p className="text-sm text-brand-400">Discount codes for customers</p>
        </div>
        <Button onClick={() => setModal(true)}>Create coupon</Button>
      </div>

      {isLoading ? (
        <TableSkeleton />
      ) : !coupons || coupons.length === 0 ? (
        <EmptyState icon={<Ticket className="h-10 w-10" aria-hidden />} title="No coupons yet" />
      ) : (
        <Table>
          <THead>
            <tr><TH>Code</TH><TH>Discount</TH><TH>Min order</TH><TH>Usage</TH><TH>Expires</TH><TH>Status</TH><TH className="text-right">Actions</TH></tr>
          </THead>
          <TBody>
            {coupons.map((c) => (
              <TR key={c.id}>
                <TD>
                  <p className="font-mono font-bold text-brand-900">{c.code}</p>
                  {c.description && <p className="text-xs text-brand-400">{c.description}</p>}
                </TD>
                <TD>{c.discount_type === "percent" ? `${c.value}%` : `₹${c.value}`}{c.max_discount_amount ? ` (max ₹${c.max_discount_amount})` : ""}</TD>
                <TD className="tabular-nums">₹{c.min_order_amount}</TD>
                <TD className="tabular-nums">{c.used_count}{c.usage_limit ? ` / ${c.usage_limit}` : ""}</TD>
                <TD className="text-xs">{c.expires_at ? new Date(c.expires_at).toLocaleDateString("en-IN") : "—"}</TD>
                <TD><Badge tone={c.is_active ? "success" : "neutral"}>{c.is_active ? "Active" : "Inactive"}</Badge></TD>
                <TD className="text-right">
                  <div className="flex justify-end gap-2">
                    <button onClick={() => toggle.mutate(c)} className="text-xs font-medium text-brand-600 hover:text-brand-800">
                      {c.is_active ? "Disable" : "Enable"}
                    </button>
                    <button onClick={() => remove.mutate(c.id)} className="text-xs font-medium text-red-500 hover:text-red-700">Delete</button>
                  </div>
                </TD>
              </TR>
            ))}
          </TBody>
        </Table>
      )}

      <Modal open={modal} onClose={() => setModal(false)} title="Create coupon">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Code" required hint="Uppercase, 3+ characters">
            <input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })} className="h-10 w-full rounded-lg border border-brand-200 px-3 font-mono text-sm uppercase" />
          </Field>
          <Field label="Discount type" required>
            <Select value={form.discount_type} onChange={(e) => setForm({ ...form, discount_type: e.target.value })}>
              <option value="percent">Percent (%)</option>
              <option value="fixed">Fixed (₹)</option>
            </Select>
          </Field>
          <Field label={form.discount_type === "percent" ? "Percent off" : "Amount off (₹)"} required>
            <input type="number" min="0" value={form.value} onChange={(e) => setForm({ ...form, value: e.target.value })} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" />
          </Field>
          <Field label="Max discount (₹, percent only)">
            <input type="number" min="0" value={form.max_discount_amount} onChange={(e) => setForm({ ...form, max_discount_amount: e.target.value })} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" />
          </Field>
          <Field label="Minimum order (₹)">
            <input type="number" min="0" value={form.min_order_amount} onChange={(e) => setForm({ ...form, min_order_amount: e.target.value })} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" />
          </Field>
          <Field label="Usage limit">
            <input type="number" min="1" value={form.usage_limit} onChange={(e) => setForm({ ...form, usage_limit: e.target.value })} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" />
          </Field>
          <Field label="Expires at">
            <input type="date" value={form.expires_at} onChange={(e) => setForm({ ...form, expires_at: e.target.value })} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" />
          </Field>
          <div className="sm:col-span-2">
            <Field label="Description">
              <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" />
            </Field>
          </div>
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setModal(false)}>Cancel</Button>
          <Button onClick={() => save.mutate()} loading={save.isPending} disabled={!valid}>Create</Button>
        </div>
      </Modal>
    </div>
  );
}

/* ------------------------------------------------------------------ reviews */

export function AdminReviewsPage() {
  const queryClient = useQueryClient();
  const [hidden, setHidden] = useState("");
  const { data: reviews, isLoading } = useQuery({
    queryKey: ["admin-reviews", hidden],
    queryFn: () => adminApi.reviews({ hidden: hidden === "" ? undefined : hidden === "true" }).then((r) => r.data),
  });

  const act = useMutation({
    mutationFn: ({ id, hide }: { id: number; hide: boolean }) => (hide ? adminApi.hideReview(id) : adminApi.showReview(id)),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-reviews"] }),
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-serif text-2xl font-bold text-brand-900">Reviews</h1>
          <p className="text-sm text-brand-400">Moderate customer reviews</p>
        </div>
        <Select value={hidden} onChange={(e) => setHidden(e.target.value)} className="w-44" aria-label="Filter">
          <option value="">All reviews</option>
          <option value="false">Visible</option>
          <option value="true">Hidden</option>
        </Select>
      </div>

      {isLoading ? (
        <TableSkeleton />
      ) : !reviews || reviews.length === 0 ? (
        <EmptyState icon={<MessageSquare className="h-10 w-10" aria-hidden />} title="No reviews" />
      ) : (
        <div className="space-y-3">
          {reviews.map((r) => (
            <Card key={r.id} className="p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-accent-500">{"★".repeat(r.rating)}{"☆".repeat(5 - r.rating)}</span>
                    <span className="text-sm font-semibold text-brand-900">{r.title}</span>
                    {r.is_hidden && <Badge tone="danger">Hidden</Badge>}
                    {r.is_verified_purchase && <Badge tone="success">Verified</Badge>}
                  </div>
                  <p className="mt-1 text-sm text-brand-500">{r.content}</p>
                  <p className="mt-1 text-xs text-brand-400">
                    {r.author_name} · book #{r.book_id} · {new Date(r.created_at).toLocaleDateString("en-IN")}
                  </p>
                </div>
                <Button size="sm" variant={r.is_hidden ? "outline" : "ghost"} onClick={() => act.mutate({ id: r.id, hide: !r.is_hidden })}>
                  {r.is_hidden ? "Unhide" : "Hide"}
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ settings */

export function AdminSettingsPage() {
  const queryClient = useQueryClient();
  const { data: settings, isLoading } = useQuery({ queryKey: ["admin-settings"], queryFn: () => adminApi.settings().then((r) => r.data) });
  const [form, setForm] = useState<Record<string, string>>({});

  if (isLoading || !settings) return <PageLoader />;

  const value = (k: keyof typeof settings) => form[k] ?? String(settings[k]);
  const set = (k: string, v: string) => setForm({ ...form, [k]: v });

  const save = useMutation({
    mutationFn: () => {
      const payload: Record<string, number | string> = {};
      for (const k of Object.keys(form)) {
        payload[k] = ["store_name", "support_email", "currency"].includes(k) ? form[k] : Number(form[k]);
      }
      return adminApi.updateSettings(payload as any);
    },
    onSuccess: () => {
      toast.success("Settings saved");
      setForm({});
      queryClient.invalidateQueries({ queryKey: ["admin-settings"] });
    },
    onError: (err: any) => toast.error(err?.response?.data?.error?.message ?? "Could not save settings"),
  });

  const numericFields: [string, string, string][] = [
    ["tax_percent", "Tax percent", "Applied to the discounted subtotal at checkout"],
    ["shipping_fee", "Shipping fee (₹)", "Flat fee; free above the threshold"],
    ["free_shipping_threshold", "Free shipping above (₹)", "0 disables free shipping"],
    ["return_window_days", "Return window (days)", "Days after delivery during which returns are allowed"],
    ["low_stock_threshold", "Default low-stock threshold", "Used for new books"],
  ];

  return (
    <div className="max-w-2xl space-y-5">
      <div>
        <h1 className="font-serif text-2xl font-bold text-brand-900">Store settings</h1>
        <p className="text-sm text-brand-400">Business rules applied across the platform</p>
      </div>
      <Card>
        <CardHeader title="General" />
        <CardBody className="grid gap-4 sm:grid-cols-2">
          <Field label="Store name">
            <input value={value("store_name")} onChange={(e) => set("store_name", e.target.value)} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" />
          </Field>
          <Field label="Support email">
            <input value={value("support_email")} onChange={(e) => set("support_email", e.target.value)} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" />
          </Field>
          <Field label="Currency">
            <input value={value("currency")} onChange={(e) => set("currency", e.target.value)} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" />
          </Field>
        </CardBody>
      </Card>
      <Card>
        <CardHeader title="Commerce rules" />
        <CardBody className="grid gap-4 sm:grid-cols-2">
          {numericFields.map(([k, label, hint]) => (
            <Field key={k} label={label} hint={hint}>
              <input type="number" value={value(k as any)} onChange={(e) => set(k, e.target.value)} className="h-10 w-full rounded-lg border border-brand-200 px-3 text-sm" />
            </Field>
          ))}
        </CardBody>
      </Card>
      <div className="flex justify-end">
        <Button onClick={() => save.mutate()} loading={save.isPending} disabled={Object.keys(form).length === 0}>Save settings</Button>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ audit */

export function AdminAuditPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useQuery({
    queryKey: ["admin-audit", page],
    queryFn: () => adminApi.auditLogs({ page, page_size: 20 }).then((r) => r.data),
  });

  if (isLoading) return <TableSkeleton />;
  if (!data || data.items.length === 0) return <EmptyState icon={<ScrollText className="h-10 w-10" aria-hidden />} title="No audit entries yet" />;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-serif text-2xl font-bold text-brand-900">Audit log</h1>
        <p className="text-sm text-brand-400">Every administrative action, recorded</p>
      </div>
      <Table>
        <THead><tr><TH>When</TH><TH>Actor</TH><TH>Action</TH><TH>Entity</TH><TH>Detail</TH></tr></THead>
        <TBody>
          {data.items.map((log) => (
            <TR key={log.id}>
              <TD className="whitespace-nowrap text-xs text-brand-400">{new Date(log.created_at).toLocaleString("en-IN")}</TD>
              <TD className="text-sm">{log.actor_name ?? "system"}</TD>
              <TD><Badge tone="info">{log.action}</Badge></TD>
              <TD className="text-sm">{log.entity_type}{log.entity_id ? ` #${log.entity_id}` : ""}</TD>
              <TD className="max-w-xs truncate text-xs text-brand-400">{log.detail ? JSON.stringify(log.detail) : "—"}</TD>
            </TR>
          ))}
        </TBody>
      </Table>
      <Pagination page={data.page} pages={data.pages} onChange={setPage} />
    </div>
  );
}
