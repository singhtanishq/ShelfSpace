"""Return/replacement eligibility, quantities and admin decisions."""

from datetime import datetime, timedelta, timezone

from app.models import Inventory, OrderStatus

API = "/api/v1"


def _deliver_order(client, db, customer_header, admin_header, book, qty=2):
    client.post(f"{API}/cart/items", headers=customer_header, json={"book_id": book.id, "quantity": qty})
    resp = client.post(
        f"{API}/orders/checkout",
        headers=customer_header,
        json={
            "shipping_address": {"full_name": "J", "phone": "+91 9876543210", "line1": "1 St", "city": "X", "state": "Y", "postal_code": "1", "country": "India"},
            "payment_method": "cod",
        },
    )
    order = resp.json()
    number = order["order_number"]
    client.put(f"{API}/admin/orders/{number}/status", headers=admin_header, json={"status": "delivered"})
    detail = client.get(f"{API}/orders/{number}", headers=customer_header).json()
    return detail, order["items"][0]["id"]


def _request_return(client, customer_header, order_number, item_id, qty=1, rtype="return"):
    return client.post(
        f"{API}/orders/{order_number}/returns",
        headers=customer_header,
        json={"type": rtype, "reason": "damaged", "description": "Arrived bent.", "items": [{"order_item_id": item_id, "quantity": qty}]},
    )


class TestReturnEligibility:
    def test_pending_order_not_eligible(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        client.post(f"{API}/cart/items", headers=ch, json={"book_id": book.id, "quantity": 1})
        resp = client.post(
            f"{API}/orders/checkout",
            headers=ch,
            json={
                "shipping_address": {"full_name": "J", "phone": "+91 9876543210", "line1": "1 St", "city": "X", "state": "Y", "postal_code": "1", "country": "India"},
                "payment_method": "cod",
            },
        )
        order = resp.json()
        item_id = order["items"][0]["id"]
        resp = _request_return(client, ch, order["order_number"], item_id)
        assert resp.status_code == 422

    def test_return_window_expired(self, client, db, customer, admin, book, monkeypatch):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        detail, item_id = _deliver_order(client, db, ch, ah, book)
        # Age the delivery beyond the 14-day window.
        order = detail
        from app.models import Order

        db_obj = db.query(Order).filter(Order.order_number == order["order_number"]).first()
        db_obj.delivered_at = datetime.now(timezone.utc) - timedelta(days=30)
        db.flush()
        resp = _request_return(client, ch, order["order_number"], item_id)
        assert resp.status_code == 422
        assert "window" in resp.json()["error"]["message"].lower()

    def test_return_request_created_with_refund_amount(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        detail, item_id = _deliver_order(client, db, ch, ah, book)
        resp = _request_return(client, ch, detail["order_number"], item_id, qty=2)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["status"] == "requested"
        assert body["refund_amount"] == float(book.effective_price) * 2

    def test_quantity_capped_by_purchased_amount(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        detail, item_id = _deliver_order(client, db, ch, ah, book, qty=1)
        resp = _request_return(client, ch, detail["order_number"], item_id, qty=5)
        assert resp.status_code == 400


class TestReturnDecisions:
    def test_full_approve_complete_flips_order_state(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        detail, item_id = _deliver_order(client, db, ch, ah, book, qty=1)
        number = detail["order_number"]
        created = _request_return(client, ch, number, item_id, qty=1).json()

        approve = client.put(f"{API}/admin/returns/{created['id']}/approve", headers=ah, json={"note": "ok"})
        assert approve.json()["status"] == "approved"
        complete = client.put(f"{API}/admin/returns/{created['id']}/complete", headers=ah, json={})
        assert complete.status_code == 200
        assert complete.json()["refund_status"] == "completed"

        final = client.get(f"{API}/orders/{number}", headers=ch).json()
        assert final["status"] == "returned"
        assert final["payment_status"] == "refunded"
        db.refresh(book.inventory)
        assert book.inventory.stock_quantity == book.stock_quantity  # restocked

    def test_cannot_have_two_open_requests(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        detail, item_id = _deliver_order(client, db, ch, ah, book, qty=2)
        number = detail["order_number"]
        first = _request_return(client, ch, number, item_id, qty=1)
        assert first.status_code == 201
        second = _request_return(client, ch, number, item_id, qty=1)
        assert second.status_code == 422

    def test_rejected_request_frees_the_order(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        detail, item_id = _deliver_order(client, db, ch, ah, book, qty=2)
        number = detail["order_number"]
        created = _request_return(client, ch, number, item_id, qty=1).json()
        client.put(f"{API}/admin/returns/{created['id']}/reject", headers=ah, json={"note": "no evidence"})
        again = _request_return(client, ch, number, item_id, qty=1)
        assert again.status_code == 201

    def test_replacement_issues_new_stock(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        detail, item_id = _deliver_order(client, db, ch, ah, book, qty=1)
        db.refresh(book.inventory)
        stock_after_sale = book.inventory.stock_quantity

        created = _request_return(client, ch, detail["order_number"], item_id, qty=1, rtype="replacement").json()
        client.put(f"{API}/admin/returns/{created['id']}/approve", headers=ah, json={})
        client.put(f"{API}/admin/returns/{created['id']}/complete", headers=ah, json={})

        db.refresh(book.inventory)
        assert book.inventory.stock_quantity == stock_after_sale - 1  # new copy shipped

    def test_customer_cannot_decide(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        detail, item_id = _deliver_order(client, db, ch, ah, book, qty=1)
        created = _request_return(client, ch, detail["order_number"], item_id, qty=1).json()
        resp = client.put(f"{API}/admin/returns/{created['id']}/approve", headers=ch, json={})
        assert resp.status_code == 403
