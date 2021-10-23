"""Shared pytest fixtures. The suite runs against in-memory SQLite by default;
set TEST_DATABASE_URL to run against MySQL instead."""

import os

# Must be set before app modules import settings.
os.environ["EMAIL_WORKER_ENABLED"] = "false"
os.environ["EMAIL_ENABLED"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models import (
    Address,
    Author,
    Book,
    Category,
    Coupon,
    Inventory,
    Publisher,
    User,
    UserRole,
)

TEST_DB_URL = "sqlite://"


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """The limiter is process-global; keep buckets clean between tests."""
    from app.utils import rate_limit

    rate_limit._buckets.clear()
    yield
    rate_limit._buckets.clear()


@pytest.fixture()
def db_engine():
    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db(db_engine):
    Session = sessionmaker(bind=db_engine, expire_on_commit=False)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Data factories
# ---------------------------------------------------------------------------


def make_user(db, username="customer", email=None, *, admin=False, verified=True, password="Passw0rd!"):
    user = User(
        email=email or f"{username}@example.com",
        username=username,
        full_name=username.title(),
        hashed_password=hash_password(password),
        role=UserRole.ADMIN if admin else UserRole.CUSTOMER,
        is_active=True,
        is_verified=verified,
    )
    db.add(user)
    db.flush()
    return user


def make_book(db, title="Test Book", *, price=100, stock=10, discount=0, threshold=5, active=True, **kwargs):
    author = db.query(Author).filter(Author.name == kwargs.pop("author_name", "Test Author")).first()
    if author is None:
        author = Author(name=kwargs.pop("author_name", "Test Author"), slug=f"author-{title.lower().replace(' ', '-')[:40]}-{id(title) % 10000}")
        db.add(author)
    category = db.query(Category).filter(Category.name == "Fiction").first()
    if category is None:
        category = Category(name="Fiction", slug="fiction")
        db.add(category)
    publisher = db.query(Publisher).first()
    if publisher is None:
        publisher = Publisher(name="Test Press", slug="test-press")
        db.add(publisher)
    db.flush()

    slug = f"{title.lower().replace(' ', '-').replace(':', '')}-{id(title) % 100000}"
    book = Book(
        title=title,
        slug=slug,
        description="A test book.",
        language="English",
        pages=200,
        published_year=2020,
        publisher_id=publisher.id,
        price=price,
        discount_percent=discount,
        is_active=active,
        **{k: v for k, v in kwargs.items() if k in {"isbn"}},
    )
    book.authors = [author]
    book.categories = [category]
    db.add(book)
    db.flush()
    db.add(Inventory(book_id=book.id, stock_quantity=stock, low_stock_threshold=threshold))
    db.flush()
    return book


def make_address(db, user, **overrides):
    address = Address(
        user_id=user.id,
        label="Home",
        full_name=user.full_name,
        phone="+91 9876543210",
        line1="42 Test Lane",
        city="Mumbai",
        state="Maharashtra",
        postal_code="400001",
        country="India",
        is_default=True,
        **overrides,
    )
    db.add(address)
    db.flush()
    return address


def make_coupon(db, code="TEST10", *, discount_type="percent", value=10, min_order=0, active=True, usage_limit=None, used_count=0):
    coupon = Coupon(
        code=code,
        discount_type=discount_type,
        value=value,
        min_order_amount=min_order,
        usage_limit=usage_limit,
        used_count=used_count,
        is_active=active,
    )
    db.add(coupon)
    db.flush()
    return coupon


def auth_header(client, db, user, password="Passw0rd!"):
    resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": user.username, "password": password},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


SHIPPING_ADDRESS = {
    "full_name": "Jane Doe",
    "phone": "+91 9876543210",
    "line1": "42 Test Lane",
    "city": "Mumbai",
    "state": "Maharashtra",
    "postal_code": "400001",
    "country": "India",
}


def checkout(client, header, book_id, qty=1, payment="cod", **extra):
    client.post("/api/v1/cart/items", headers=header, json={"book_id": book_id, "quantity": qty})
    resp = client.post(
        "/api/v1/orders/checkout",
        headers=header,
        json={"shipping_address": dict(SHIPPING_ADDRESS), "payment_method": payment, **extra},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def mark_delivered(client, admin_header, order_number):
    """Walk the order through every intermediate status (the state machine
    forbids skipping stages)."""
    for status in ("confirmed", "processing", "shipped", "out_for_delivery", "delivered"):
        resp = client.put(
            f"/api/v1/admin/orders/{order_number}/status", headers=admin_header, json={"status": status}
        )
        assert resp.status_code == 200, resp.text


@pytest.fixture()
def customer(db):
    return make_user(db, "jane_doe", "jane@example.com")


@pytest.fixture()
def admin(db):
    return make_user(db, "root_admin", "root@example.com", admin=True)


@pytest.fixture()
def book(db):
    return make_book(db)
