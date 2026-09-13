import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { Field } from "@/components/ui/Input";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, PieChart, Pie, Cell, Legend,
} from "recharts";
import { adminApi } from "@/api/endpoints";
import { Card, CardBody, CardHeader, Badge } from "@/components/ui/Card";
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
