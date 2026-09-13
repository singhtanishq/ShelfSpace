"""Cart behavior and transactional checkout (incl. oversell prevention)."""

API = "/api/v1"


def _add_to_cart(client, header, book_id, qty=1):
    return client.post(f"{API}/cart/items", headers=header, json={"book_id": book_id, "quantity": qty})


class TestCart:
    def test_add_and_view(self, client, db, customer, book):
        header = auth_header(client, db, customer)
        resp = _add_to_cart(client, header, book.id, 2)
        assert resp.status_code == 201
        cart = resp.json()
        assert cart["items"][0]["quantity"] == 2
        assert cart["subtotal"] == book.effective_price * 2

    def test_add_same_book_merges(self, client, db, customer, book):
        header = auth_header(client, db, customer)
        _add_to_cart(client, header, book.id, 1)
        resp = _add_to_cart(client, header, book.id, 2)
        assert len(resp.json()["items"]) == 1
        assert resp.json()["items"][0]["quantity"] == 3

    def test_quantity_beyond_stock_rejected(self, client, db, customer, book):
        header = auth_header(client, db, customer)
        resp = _add_to_cart(client, header, book.id, book.stock_quantity + 1)
        assert resp.status_code == 400

    def test_update_and_remove(self, client, db, customer, book):
        header = auth_header(client, db, customer)
        _add_to_cart(client, header, book.id, 1)
        resp = client.patch(f"{API}/cart/items/{book.id}", headers=header, json={"quantity": 4})
        assert resp.json()["items"][0]["quantity"] == 4
        resp = client.delete(f"{API}/cart/items/{book.id}", headers=header)
        assert resp.json()["items"] == []

    def test_cart_is_per_user(self, client, db, customer, admin, book):
        h1 = auth_header(client, db, customer)
        h2 = auth_header(client, db, admin)
        _add_to_cart(client, h1, book.id, 1)
        assert client.get(f"{API}/cart", headers=h2).json()["items"] == []

    def test_coupon_application(self, client, db, customer, book):
        from tests.conftest import make_coupon

        coupon = make_coupon(db, "SAVE10", discount_type="percent", value=10)
        header = auth_header(client, db, customer)
        _add_to_cart(client, header, book.id, 1)  # 100
        resp = client.post(f"{API}/cart/coupon", headers=header, json={"code": "SAVE10"})
        assert resp.json()["discount_total"] == 10.0
        assert resp.json()["coupon"]["code"] == "SAVE10"

    def test_coupon_min_order_enforced(self, client, db, customer, book):
        from tests.conftest import make_coupon

        make_coupon(db, "BIG", discount_type="fixed", value=50, min_order=1000)
        header = auth_header(client, db, customer)
        _add_to_cart(client, header, book.id, 1)
        resp = client.post(f"{API}/cart/coupon", headers=header, json={"code": "BIG"})
        assert resp.status_code == 400


class TestCheckout:
    def _checkout(self, client, header, payment="card", **extra):
        payload = {
            "shipping_address": {
                "full_name": "Jane Doe",
                "phone": "+91 9876543210",
                "line1": "42 Test Lane",
                "city": "Mumbai",
                "state": "Maharashtra",
                "postal_code": "400001",
                "country": "India",
            },
            "payment_method": payment,
            **extra,
        }
        return client.post(f"{API}/orders/checkout", headers=header, json=payload)

    def test_checkout_creates_order_and_decrements_stock(self, client, db, customer, book):
        header = auth_header(client, db, customer)
        _add_to_cart(client, header, book.id, 3)
        resp = self._checkout(client, header, payment="cod")
        assert resp.status_code == 201, resp.text
        order = resp.json()
        assert order["status"] == "pending"
        assert order["payment_status"] == "pending"  # COD
        assert order["items"][0]["quantity"] == 3
        db.refresh(book.inventory)
        assert book.inventory.stock_quantity == book.stock_quantity - 3

    def test_mock_card_payment_is_paid(self, client, db, customer, book):
        header = auth_header(client, db, customer)
        _add_to_cart(client, header, book.id, 1)
        resp = self._checkout(client, header, card_number="4242424242424242")
        assert resp.json()["payment_status"] == "paid"

    def test_card_payment_requires_card_number(self, client, db, customer, book):
        header = auth_header(client, db, customer)
        _add_to_cart(client, header, book.id, 1)
        resp = self._checkout(client, header)
        assert resp.status_code == 400

    def test_checkout_clears_cart_and_applies_coupon_once(self, client, db, customer, book):
        from tests.conftest import make_coupon

        make_coupon(db, "FLAT20", discount_type="fixed", value=20)
        header = auth_header(client, db, customer)
        _add_to_cart(client, header, book.id, 2)
        client.post(f"{API}/cart/coupon", headers=header, json={"code": "FLAT20"})
        resp = self._checkout(client, header, payment="upi", upi_id="jane@upi")
        order = resp.json()
        assert order["discount_total"] == 20.0
        assert order["coupon_code"] == "FLAT20"
        assert client.get(f"{API}/cart", headers=header).json()["items"] == []

    def test_oversell_prevented_across_sessions(self, client, db, customer, admin, book):
        """Two users race for the same units; stock 3, both try to buy 3."""
        h1 = auth_header(client, db, customer)
        h2 = auth_header(client, db, admin)
        _add_to_cart(client, h1, book.id, 3)
        _add_to_cart(client, h2, book.id, 3)

        r1 = self._checkout(client, h1, payment="cod")
        assert r1.status_code == 201
        r2 = self._checkout(client, h2, payment="cod")
        assert r2.status_code == 422
        assert "available" in r2.json()["error"]["message"].lower()

    def test_checkout_with_empty_cart_fails(self, client, db, customer):
        header = auth_header(client, db, customer)
        resp = self._checkout(client, header)
        assert resp.status_code == 422

    def test_inactive_book_cannot_checkout(self, client, db, customer, book):
        header = auth_header(client, db, customer)
        _add_to_cart(client, header, book.id, 1)
        book.is_active = False
        db.flush()
        resp = self._checkout(client, header)
        assert resp.status_code == 422
