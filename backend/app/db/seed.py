"""Database seeding: `python -m app.db.seed [--fresh]`

Creates a demo-ready store: users, catalog with generated cover art, orders
across every lifecycle stage, reviews, coupons and settings.
"""

import random
import sys
from datetime import datetime, timedelta, timezone

from app.core.database import SessionLocal, media_path, create_engine  # noqa
from app.core.logging import get_logger
from app.core.security import hash_password
from app.models import (
    Address,
    Author,
    Book,
    Category,
    Coupon,
    Inventory,
    InventoryChangeType,
    InventoryTransaction,
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
    Payment,
    PaymentMethod,
    PaymentStatus,
    Publisher,
    Review,
    User,
    UserRole,
)
from app.db.seeds.seed_data import (
    ADDRESSES,
    ADMINS,
    AUTHORS,
    BOOKS,
    CATEGORIES,
    COUPONS,
    CUSTOMERS,
    PUBLISHERS,
    REVIEW_SNIPPETS,
)

logger = get_logger(__name__)

random.seed(42)

# Cover art palettes (deterministic per title via hashing).
PALETTES = [
    ("#1e3a5f", "#3b82c4"), ("#4c1d95", "#8b5cf6"), ("#7c2d12", "#ea580c"),
    ("#064e3b", "#10b981"), ("#831843", "#ec4899"), ("#1e3a8a", "#6366f1"),
    ("#713f12", "#eab308"), ("#134e4a", "#14b8a6"), ("#3f3f46", "#a1a1aa"),
    ("#7f1d1d", "#f87171"),
]


def generate_cover(title: str, author: str) -> str:
    """Create a simple, tasteful SVG cover so the catalog looks alive offline."""
    idx = sum(ord(c) for c in title) % len(PALETTES)
    dark, light = PALETTES[idx]
    short_title = title if len(title) <= 34 else title[:32].rstrip() + "…"
    short_author = author if len(author) <= 30 else author[:28] + "…"
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="600" viewBox="0 0 400 600">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{dark}"/>
      <stop offset="100%" stop-color="{light}"/>
    </linearGradient>
  </defs>
  <rect width="400" height="600" fill="url(#g)"/>
  <rect x="0" y="0" width="18" height="600" fill="rgba(0,0,0,0.25)"/>
  <rect x="40" y="60" width="52" height="4" fill="rgba(255,255,255,0.85)"/>
  <text x="40" y="130" font-family="Georgia, serif" font-size="30" fill="#ffffff" font-weight="bold">
    {'</tspan><tspan x="40" dy="40">'.join(_wrap(short_title, 20))}
  </text>
  <text x="40" y="520" font-family="Helvetica, Arial, sans-serif" font-size="17" fill="rgba(255,255,255,0.85)">{_esc(short_author)}</text>
  <text x="40" y="556" font-family="Helvetica, Arial, sans-serif" font-size="12" fill="rgba(255,255,255,0.5)" letter-spacing="3">SHELFSPACE</text>
</svg>"""
    filename = f"cover-{abs(hash(title)) % 10_000_000:07d}.svg"
    path = media_path("covers", filename)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    return f"media/covers/{filename}"


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _wrap(text: str, width: int) -> list:
    import textwrap

    return [_esc(line) for line in textwrap.wrap(text, width=width) or [""]]


def seed(fresh: bool = False) -> None:
    from sqlalchemy import create_engine as ce
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings

    engine = ce(settings.DATABASE_URL, pool_pre_ping=True)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    db = Session()

    if fresh:
        logger.info("Wiping existing data…")
        from sqlalchemy import inspect, text as _text

        inspector = inspect(engine)
        db.execute(_text("SET FOREIGN_KEY_CHECKS=0"))
        for table in inspector.get_table_names():
            if table != "alembic_version":
                db.execute(_text(f"TRUNCATE TABLE {table}"))
        db.execute(_text("SET FOREIGN_KEY_CHECKS=1"))
        db.commit()

    if db.query(User).count() > 0:
        print("Database already seeded. Use --fresh to reseed from scratch.")
        return

    print("Seeding ShelfSpace demo data…")

    # --- Users -------------------------------------------------------------
    admin = User(
        email=ADMINS[0]["email"],
        username=ADMINS[0]["username"],
        full_name=ADMINS[0]["full_name"],
        hashed_password=hash_password(ADMINS[0]["password"]),
        role=UserRole.ADMIN,
        is_verified=True,
    )
    db.add(admin)
    users_by_username = {}
    for spec in CUSTOMERS:
        user = User(
            email=spec["email"],
            username=spec["username"],
            full_name=spec["full_name"],
            hashed_password=hash_password(spec["password"]),
            role=UserRole.CUSTOMER,
            is_verified=spec["is_verified"],
            phone=spec.get("phone"),
            created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(10, 150)),
        )
        db.add(user)
        users_by_username[spec["username"]] = user
    db.flush()

    # --- Addresses ----------------------------------------------------------
    for username, label, line1, city, state, postal, is_default in ADDRESSES:
        db.add(
            Address(
                user_id=users_by_username[username].id,
                label=label,
                full_name=users_by_username[username].full_name,
                phone=users_by_username[username].phone or "+91 9800000000",
                line1=line1,
                city=city,
                state=state,
                postal_code=postal,
                country="India",
                is_default=is_default,
            )
        )

    # --- Taxonomy ------------------------------------------------------------
    categories = {}
    for name, description in CATEGORIES:
        slug = name.lower().replace("&", "and").replace(" ", "-")
        categories[name] = Category(name=name, slug=slug, description=description)
        db.add(categories[name])
    authors = {}
    for name, bio in AUTHORS:
        slug = name.lower().replace(".", "").replace(" ", "-")
        authors[name] = Author(name=name, slug=slug, bio=bio)
        db.add(authors[name])
    publishers = {}
    for name in PUBLISHERS:
        slug = name.lower().replace("&", "and").replace(" ", "-")
        publishers[name] = Publisher(name=name, slug=slug)
        db.add(publishers[name])
    db.flush()

    # --- Books ---------------------------------------------------------------
    books = []
    now = datetime.now(timezone.utc)
    for i, (title, book_authors_list, book_cats, publisher, year, pages, price, discount, stock, featured, isbn, description) in enumerate(BOOKS):
        author_names = ", ".join(book_authors_list)
        book = Book(
            title=title,
            slug=title.lower().replace(":", "").replace(",", "").replace("&", "and").replace(" ", "-"),
            isbn=isbn,
            description=description,
            language="English",
            pages=pages,
            published_year=year,
            publisher_id=publishers[publisher].id,
            price=price,
            discount_percent=discount,
            is_featured=featured,
            cover_image=generate_cover(title, author_names),
            created_at=now - timedelta(days=random.randint(1, 300)),
        )
        book.authors = [authors[a] for a in book_authors_list]
        book.categories = [categories[c] for c in book_cats]
        db.add(book)
        books.append((book, stock))
    db.flush()

    for book, stock in books:
        threshold = 5 if stock > 30 else 3
        db.add(Inventory(book_id=book.id, stock_quantity=stock, low_stock_threshold=threshold))
        db.add(
            InventoryTransaction(
                book_id=book.id,
                change=stock,
                change_type=InventoryChangeType.RESTOCK,
                balance_after=stock,
                reference_type="seed",
                note="Opening stock",
                created_by=admin.id,
            )
        )

    # --- Coupons ---------------------------------------------------------------
    for spec in COUPONS:
        db.add(
            Coupon(
                code=spec["code"],
                description=spec["description"],
                discount_type=spec["discount_type"],
                value=spec["value"],
                min_order_amount=spec["min_order_amount"],
                max_discount_amount=spec["max_discount_amount"],
                usage_limit=spec["usage_limit"],
                starts_at=now - timedelta(days=30),
                expires_at=now + timedelta(days=180),
            )
        )

    # --- Orders ------------------------------------------------------------------
    statuses_pool = (
        [OrderStatus.DELIVERED] * 9
        + [OrderStatus.SHIPPED] * 3
        + [OrderStatus.PROCESSING] * 2
        + [OrderStatus.CONFIRMED] * 2
        + [OrderStatus.PENDING] * 2
        + [OrderStatus.CANCELLED] * 2
        + [OrderStatus.OUT_FOR_DELIVERY] * 1
    )
    customers = [users_by_username[s["username"]] for s in CUSTOMERS if users_by_username[s["username"]].is_verified]
    order_seq = 0
    delivered_orders = []
    for status in statuses_pool:
        order_seq += 1
        customer = random.choice(customers)
        address = db.query(Address).filter(Address.user_id == customer.id).first()
        n_items = random.choice([1, 1, 1, 2, 2, 3])
        chosen = random.sample(books, k=min(n_items, len(books)))
        items = []
        subtotal = 0.0
        placed_days_ago = random.randint(2, 120)
        placed_at = now - timedelta(days=placed_days_ago)
        for book, _stock in chosen:
            qty = random.choice([1, 1, 2])
            unit = float(book.effective_price)
            items.append(
                OrderItem(
                    book_id=book.id,
                    title=book.title,
                    author_names=book.author_names(),
                    isbn=book.isbn,
                    cover_image=book.cover_image,
                    unit_price=unit,
                    quantity=qty,
                    line_total=round(unit * qty, 2),
                )
            )
            subtotal += unit * qty
        subtotal = round(subtotal, 2)
        method = random.choice([PaymentMethod.COD, PaymentMethod.CARD, PaymentMethod.UPI])
        if status == OrderStatus.DELIVERED:
            payment_status = PaymentStatus.PAID
            delivered_at = placed_at + timedelta(days=random.randint(3, 8))
        elif status == OrderStatus.CANCELLED:
            payment_status = PaymentStatus.PAID if method != PaymentMethod.COD else PaymentStatus.PENDING
            delivered_at = None
        else:
            payment_status = PaymentStatus.PAID if method != PaymentMethod.COD else PaymentStatus.PENDING
            delivered_at = None

        order = Order(
            order_number=f"SS-{placed_at:%Y%m%d}-{order_seq:05d}",
            user_id=customer.id,
            status=status,
            payment_method=method,
            payment_status=payment_status,
            subtotal=subtotal,
            shipping_fee=0,
            tax_total=0,
            total=subtotal,
            shipping_address={
                "full_name": customer.full_name,
                "phone": address.phone,
                "line1": address.line1,
                "line2": None,
                "city": address.city,
                "state": address.state,
                "postal_code": address.postal_code,
                "country": address.country,
            },
            placed_at=placed_at,
            delivered_at=delivered_at,
            cancelled_at=placed_at + timedelta(days=1) if status == OrderStatus.CANCELLED else None,
        )
        order.items = items
        db.add(order)
        db.flush()

        history = [OrderStatusHistory(order_id=order.id, from_status=None, to_status=OrderStatus.PENDING, changed_by_id=customer.id, note="Order placed", created_at=placed_at)]
        flow = [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED]
        try:
            end = flow.index(status)
            chain = flow[: end + 1]
        except ValueError:
            chain = flow[:3]
        prev = None
        for j, st in enumerate(chain):
            ts = placed_at + timedelta(hours=j * 18)
            if status == OrderStatus.CANCELLED and st == OrderStatus.PROCESSING:
                break
            history.append(
                OrderStatusHistory(
                    order_id=order.id,
                    from_status=prev,
                    to_status=st,
                    changed_by_id=admin.id if prev else customer.id,
                    created_at=ts,
                )
            )
            prev = st
        if status == OrderStatus.CANCELLED:
            history.append(OrderStatusHistory(order_id=order.id, from_status=prev, to_status=OrderStatus.CANCELLED, changed_by_id=customer.id, note="Cancelled by customer", created_at=placed_at + timedelta(days=1)))
        for h in history:
            db.add(h)

        pay_status = PaymentStatus.PAID if payment_status == PaymentStatus.PAID else PaymentStatus.PENDING
        db.add(
            Payment(
                order_id=order.id,
                provider="mock",
                method=method,
                amount=order.total,
                status=pay_status,
                transaction_ref=f"mock_{method.value}_{abs(hash(order.order_number)) % 10**10:010d}",
                paid_at=placed_at if pay_status == PaymentStatus.PAID else None,
            )
        )

        for item in order.items:
            if item.book_id:
                book = db.get(Book, item.book_id)
                book.sales_count = (book.sales_count or 0) + item.quantity
        if status == OrderStatus.DELIVERED:
            delivered_orders.append((order, delivered_at))

    # --- Reviews ---------------------------------------------------------------
    used = set()
    rating_pool = [5, 5, 4, 4, 5, 3, 5, 4]
    for order, delivered_at in delivered_orders:
        for item in order.items:
            key = (order.user_id, item.book_id)
            if key in used or item.book_id is None:
                continue
            used.add(key)
            title, content = random.choice(REVIEW_SNIPPETS)
            db.add(
                Review(
                    book_id=item.book_id,
                    user_id=order.user_id,
                    rating=random.choice(rating_pool),
                    title=title,
                    content=content,
                    is_verified_purchase=True,
                    created_at=delivered_at + timedelta(days=random.randint(1, 5)),
                )
            )

    _refresh_all_ratings(db)
    db.commit()

    counts = {
        "users": db.query(User).count(),
        "books": db.query(Book).count(),
        "orders": db.query(Order).count(),
        "reviews": db.query(Review).count(),
        "coupons": db.query(Coupon).count(),
    }
    print("Seed complete:", ", ".join(f"{k}={v}" for k, v in counts.items()))
    db.close()


def _refresh_all_ratings(db) -> None:
    from sqlalchemy import func

    rows = db.query(Review.book_id, func.avg(Review.rating), func.count(Review.id)).filter(Review.is_hidden.is_(False)).group_by(Review.book_id).all()
    for book_id, avg, count in rows:
        book = db.get(Book, book_id)
        if book:
            book.rating_avg = round(float(avg), 2)
            book.rating_count = count


if __name__ == "__main__":
    seed(fresh="--fresh" in sys.argv)
