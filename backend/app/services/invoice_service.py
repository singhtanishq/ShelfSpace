"""Professional PDF invoice generation (fpdf2)."""

import os
from datetime import datetime
from typing import Optional

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from sqlalchemy.orm import Session

from app.core.database import media_path
from app.models import Order
from app.services import settings_service


class InvoicePDF(FPDF):
    def __init__(self, store_name: str, support_email: str):
        super().__init__()
        self.store_name = store_name
        self.support_email = support_email

    def header(self):
        self.set_font("helvetica", "B", 20)
        self.cell(0, 10, self.store_name, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("helvetica", "", 9)
        self.set_text_color(110, 118, 135)
        self.cell(0, 5, self.support_email, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)
        self.ln(4)

    def footer(self):
        self.set_y(-18)
        self.set_font("helvetica", "", 8)
        self.set_text_color(140, 145, 155)
        self.cell(0, 5, f"Thank you for shopping with {self.store_name}!", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.cell(0, 5, f"Page {self.page_no()} of {{nb}}", align="C")


def generate_invoice(db: Session, order: Order, *, user_name: str, user_email: str) -> str:
    """Render (or re-render) the invoice PDF for an order. Returns the file path."""
    store_name = settings_service.get_str(db, "store_name")
    support_email = settings_service.get_str(db, "support_email")
    currency = settings_service.get_str(db, "currency")

    pdf = InvoicePDF(store_name, support_email)
    pdf.alias_nb_pages()
    pdf.add_page()

    # Title block
    pdf.set_font("helvetica", "B", 15)
    pdf.cell(0, 8, "TAX INVOICE", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(110, 118, 135)
    pdf.cell(0, 5, f"Invoice #{'INV-' + order.order_number}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    # Two-column meta: bill to / order meta
    y0 = pdf.get_y()
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(95, 6, "Billed / Shipped to", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_xy(105, y0)
    pdf.cell(0, 6, "Order details", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("helvetica", "", 9)
    addr = order.shipping_address or {}
    x = 105
    pdf.set_x(0)
    pdf.cell(95, 5, f"{user_name}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    meta_rows = [
        f"Order number: {order.order_number}",
        f"Order date: {order.placed_at.strftime('%d %b %Y')}",
        f"Payment: {order.payment_method.value.upper()} ({order.payment_status.value})",
    ]
    y = y0 + 6
    for row in meta_rows:
        pdf.set_xy(x, y)
        pdf.cell(0, 5, row)
        y += 5

    for line in [addr.get("line1", ""), addr.get("line2") or "", f"{addr.get('city', '')}, {addr.get('state', '')} {addr.get('postal_code', '')}", addr.get("country", ""), f"Phone: {addr.get('phone', '')}"]:
        if line.strip():
            pdf.set_x(0)
            pdf.multi_cell(95, 5, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_y(max(pdf.get_y(), y) + 6)

    # Items table
    pdf.set_fill_color(30, 58, 95)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 9)
    col_widths = [10, 92, 20, 26, 42]
    headers = ["#", "Item", "Qty", "Unit price", "Amount"]
    for width, header in zip(col_widths, headers):
        pdf.cell(width, 8, header, border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 9)
    fill = False
    for idx, item in enumerate(order.items, start=1):
        if pdf.get_y() > 250:
            pdf.add_page()
            fill = False
        pdf.set_fill_color(245, 247, 250)
        pdf.cell(col_widths[0], 8, str(idx), border=1, align="C", fill=fill)
        pdf.cell(col_widths[1], 8, _trunc(f"{item.title} - {item.author_names}", 70), border=1, fill=fill)
        pdf.cell(col_widths[2], 8, str(item.quantity), border=1, align="C", fill=fill)
        pdf.cell(col_widths[3], 8, f"{currency} {item.unit_price:,.2f}", border=1, align="R", fill=fill)
        pdf.cell(col_widths[4], 8, f"{currency} {item.line_total:,.2f}", border=1, align="R", fill=fill)
        pdf.ln()
        fill = not fill

    # Totals
    pdf.ln(2)
    rows = [("Subtotal", order.subtotal)]
    if float(order.discount_total) > 0:
        rows.append((f"Discount ({order.coupon_code or ''})", -float(order.discount_total)))
    rows.append(("Shipping", order.shipping_fee))
    if float(order.tax_total) > 0:
        rows.append(("Tax", order.tax_total))
    rows.append(("Total", order.total))

    for label, value in rows:
        pdf.set_x(118)
        bold = label == "Total"
        pdf.set_font("helvetica", "B" if bold else "", 9)
        pdf.cell(38, 7, label, border=0, align="R")
        pdf.cell(34, 7, f"{currency} {value:,.2f}", border=0, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(6)
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(110, 118, 135)
    addr_line = f"{addr.get('line1', '')}, {addr.get('city', '')} {addr.get('postal_code', '')}".strip(", ")
    pdf.multi_cell(
        0,
        5,
        f"Deliver to: {user_name}, {addr_line}  |  Generated on {datetime.utcnow().strftime('%d %b %Y %H:%M')}",
    )
    pdf.set_text_color(0, 0, 0)

    path = media_path("invoices", f"{order.order_number}.pdf")
    pdf.output(path)
    return path


def _trunc(text: str, length: int) -> str:
    return text if len(text) <= length else text[: length - 3] + "..."
