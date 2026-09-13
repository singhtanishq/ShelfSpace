"""Order lifecycle: state machine, cancellation, authorization, invoice."""

from datetime import datetime, timedelta, timezone

from app.models import Inventory, Order, OrderStatus

API = "/api/v1"


def _checkout(client, header, book_id, qty=1, payment="cod"):
    client.post(f"{API}/cart/items", headers=header, json={"book_id": book_id, "quantity": qty})
    resp = client.post(
        f"{API}/orders/checkout",
        headers=header,
        json={
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
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestOrderStateMachine:
    def test_happy_path_transitions(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        order = _checkout(client, ch, book.id)
        number = order["order_number"]

        for status in ("confirmed", "processing", "shipped", "out_for_delivery", "delivered"):
            resp = client.put(f"{API}/admin/orders/{number}/status", headers=ah, json={"status": status})
            assert resp.status_code == 200, resp.text
            assert resp.json()["status"] == status

        final = client.get(f"{API}/orders/{number}", headers=ch).json()
        assert final["status"] == "delivered"
        assert final["delivered_at"] is not None
        # COD orders are captured on delivery.
        assert final["payment_status"] == "paid"

    def test_invalid_transition_rejected(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        order = _checkout(client, ch, book.id)
        resp = client.put(
            f"{API}/admin/orders/{order['order_number']}/status", headers=ah, json={"status": "shipped"}
        )
        assert resp.status_code == 422

    def test_delivered_cannot_go_back(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        order = _checkout(client, ch, book.id)
        number = order["order_number"]
        for status in ("confirmed", "delivered"):
            client.put(f"{API}/admin/orders/{number}/status", headers=ah, json={"status": status})
        resp = client.put(f"{API}/admin/orders/{number}/status", headers=ah, json={"status": "processing"})
        assert resp.status_code == 422

    def test_cancel_restocks_inventory(self, client, db, customer, book):
        ch = auth_header(client, db, customer)
        order = _checkout(client, ch, book.id, qty=2)
        db.refresh(book.inventory)
        after_sale = book.inventory.stock_quantity
        assert after_sale == book.stock_quantity - 2

        resp = client.post(f"{API}/orders/{order['order_number']}/cancel", headers=ch, json={"note": "changed mind"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"
        db.refresh(book.inventory)
        assert book.inventory.stock_quantity == book.stock_quantity

    def test_cancel_after_delivered_rejected(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        order = _checkout(client, ch, book.id)
        number = order["order_number"]
        client.put(f"{API}/admin/orders/{number}/status", headers=ah, json={"status": "delivered"})
        resp = client.post(f"{API}/orders/{number}/cancel", headers=ch, json={})
        assert resp.status_code == 422

    def test_paid_order_cancel_marks_refund(self, client, db, customer, book):
        ch = auth_header(client, db, customer)
        order = _checkout(client, ch, book.id, payment="upi")  # mock gateway lacks upi without id? card path validated
        # use card to be paid
        ch2 = auth_header(client, db, customer)
        client.delete(f"{API}/cart", headers=ch2)
        resp = None
        client.post(f"{API}/cart/items", headers=ch2, json={"book_id": book.id, "quantity": 1})
        resp = client.post(
            f"{API}/orders/checkout",
            headers=ch2,
            json={
                "shipping_address": {"full_name": "J", "phone": "+91 9876543210", "line1": "1 St", "city": "X", "state": "Y", "postal_code": "1", "country": "India"},
                "payment_method": "card",
                "card_number": "4242424242424242",
            },
        )
        paid = resp.json()
        cancel = client.post(f"{API}/orders/{paid['order_number']}/cancel", headers=ch2, json={})
        assert cancel.status_code == 200
        assert cancel.json()["payment_status"] == "refunded"


class TestOrderAuthorization:
    def test_user_cannot_see_others_order(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        order = _checkout(client, ch, book.id)
        resp = client.get(f"{API}/orders/{order['order_number']}", headers=ah)
        assert resp.status_code == 404  # admin has no customer role bypass on customer routes

    def test_user_cannot_cancel_others_order(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        order = _checkout(client, ch, book.id)
        resp = client.post(f"{API}/orders/{order['order_number']}/cancel", headers=ah, json={})
        assert resp.status_code == 404

    def test_order_list_only_own(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        _checkout(client, ch, book.id)
        mine = client.get(f"{API}/orders", headers=ah).json()
        assert mine["total"] == 0


class TestInvoice:
    def test_invoice_download(self, client, db, customer, book):
        ch = auth_header(client, db, customer)
        order = _checkout(client, ch, book.id)
        resp = client.get(f"{API}/orders/{order['order_number']}/invoice", headers=ch)
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:4] == b"%PDF"

    def test_invoice_of_other_user_forbidden(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        order = _checkout(client, ch, book.id)
        resp = client.get(f"{API}/orders/{order['order_number']}/invoice", headers=ah)
        assert resp.status_code == 404
