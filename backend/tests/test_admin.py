"""Admin platform: dashboard, inventory, book CRUD, users, coupons, settings, audit."""


from tests.conftest import auth_header, make_coupon  # noqa: F401

class TestDashboard:
    def test_summary_metrics(self, client, db, admin):
        header = auth_header(client, db, admin)
        resp = client.get("/api/v1/admin/dashboard/summary", headers=header)
        assert resp.status_code == 200
        body = resp.json()
        for key in ("total_books", "total_customers", "pending_orders", "inventory_value"):
            assert key in body

    def test_charts_and_top(self, client, db, admin):
        header = auth_header(client, db, admin)
        charts = client.get("/api/v1/admin/dashboard/charts?days=7", headers=header)
        assert charts.status_code == 200
        assert len(charts.json()["revenue"]) == 8
        top = client.get("/api/v1/admin/dashboard/top?days=7", headers=header)
        assert top.status_code == 200
        assert "books" in top.json()

    def test_low_stock_list(self, client, db, admin, book):
        book.inventory.stock_quantity = 2
        db.flush()
        header = auth_header(client, db, admin)
        resp = client.get("/api/v1/admin/dashboard/low-stock", headers=header)
        assert any(b["book_id"] == book.id for b in resp.json())


class TestBookAdmin:
    def test_create_book(self, client, db, admin):
        header = auth_header(client, db, admin)
        resp = client.post(
            "/api/v1/admin/books",
            headers=header,
            json={"title": "Brand New Book", "price": 299, "stock_quantity": 7, "description": "New."},
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["stock_quantity"] == 7

    def test_create_book_invalid_price(self, client, db, admin):
        header = auth_header(client, db, admin)
        resp = client.post(
            "/api/v1/admin/books", headers=header, json={"title": "Bad", "price": -5, "stock_quantity": 1}
        )
        assert resp.status_code == 422

    def test_archive_protects_order_history(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        client.post(f"/api/v1/cart/items", headers=ch, json={"book_id": book.id, "quantity": 1})
        order = client.post(
            f"/api/v1/orders/checkout",
            headers=ch,
            json={
                "shipping_address": {"full_name": "J", "phone": "+91 9876543210", "line1": "1 St", "city": "X", "state": "Y", "postal_code": "1", "country": "India"},
                "payment_method": "cod",
            },
        ).json()

        hard = client.delete(f"/api/v1/admin/books/{book.id}?hard=true", headers=ah)
        assert hard.status_code == 422
        soft = client.delete(f"/api/v1/admin/books/{book.id}", headers=ah)
        assert soft.status_code == 200
        assert soft.json()["archived"] is True

    def test_cover_upload_validates_type(self, client, db, admin, book):
        header = auth_header(client, db, admin)
        resp = client.post(
            f"/api/v1/admin/books/{book.id}/cover",
            headers=header,
            files={"file": ("evil.exe", b"MZ...", "application/x-msdownload")},
        )
        assert resp.status_code == 400

    def test_cover_upload_accepts_png(self, client, db, admin, book, tmp_path):
        from PIL import Image
        import io

        header = auth_header(client, db, admin)
        buf = io.BytesIO()
        Image.new("RGB", (10, 10), color=(30, 58, 95)).save(buf, format="PNG")
        buf.seek(0)
        resp = client.post(
            f"/api/v1/admin/books/{book.id}/cover",
            headers=header,
            files={"file": ("cover.png", buf.read(), "image/png")},
        )
        assert resp.status_code == 200
        assert resp.json()["cover_image"].endswith(".png")


class TestInventoryAdmin:
    def test_adjust_stock_creates_ledger_entry(self, client, db, admin, book):
        header = auth_header(client, db, admin)
        resp = client.post(
            f"/api/v1/admin/inventory/{book.id}/adjust", headers=header, json={"change": 5, "note": "restock"}
        )
        assert resp.status_code == 200
        assert resp.json()["stock_quantity"] == book.inventory.stock_quantity + 5
        txs = client.get(f"/api/v1/admin/inventory/{book.id}/transactions", headers=header).json()
        assert txs[0]["change"] == 5
        assert txs[0]["balance_after"] == book.inventory.stock_quantity + 5

    def test_negative_adjust_beyond_stock_rejected(self, client, db, admin, book):
        header = auth_header(client, db, admin)
        resp = client.post(
            f"/api/v1/admin/inventory/{book.id}/adjust", headers=header, json={"change": -(book.inventory.stock_quantity + 1)}
        )
        assert resp.status_code == 422


class TestTaxonomyAdmin:
    def test_term_crud_and_delete_guard(self, client, db, admin, book):
        header = auth_header(client, db, admin)
        created = client.post("/api/v1/admin/categories", headers=header, json={"name": "Poetry"})
        assert created.status_code == 201
        term_id = created.json()["id"]
        updated = client.put(f"/api/v1/admin/categories/{term_id}", headers=header, json={"name": "Modern Poetry"})
        assert updated.json()["name"] == "Modern Poetry"
        # in use by `book` → delete must be blocked
        book.categories.append(updated.json())
        db.flush()
        blocked = client.delete(f"/api/v1/admin/categories/{term_id}", headers=header)
        assert blocked.status_code == 422


class TestUserAdmin:
    def test_role_change_and_self_protection(self, client, db, customer, admin):
        ah = auth_header(client, db, admin)
        resp = client.put(f"/api/v1/admin/users/{customer.id}", headers=ah, json={"role": "admin"})
        assert resp.json()["role"] == "admin"
        self_demote = client.put(f"/api/v1/admin/users/{admin.id}", headers=ah, json={"role": "customer"})
        assert self_demote.status_code == 422

    def test_deactivate_user(self, client, db, customer, admin):
        ah = auth_header(client, db, admin)
        resp = client.put(f"/api/v1/admin/users/{customer.id}", headers=ah, json={"is_active": False})
        assert resp.json()["is_active"] is False

    def test_hard_delete_blocked_with_orders(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        client.post(f"/api/v1/cart/items", headers=ch, json={"book_id": book.id, "quantity": 1})
        client.post(
            f"/api/v1/orders/checkout",
            headers=ch,
            json={
                "shipping_address": {"full_name": "J", "phone": "+91 9876543210", "line1": "1 St", "city": "X", "state": "Y", "postal_code": "1", "country": "India"},
                "payment_method": "cod",
            },
        )
        resp = client.delete(f"/api/v1/admin/users/{customer.id}?hard=true", headers=ah)
        assert resp.status_code == 422


class TestCouponsAdmin:
    def test_coupon_crud(self, client, db, admin):
        ah = auth_header(client, db, admin)
        created = client.post(
            "/api/v1/admin/coupons",
            headers=ah,
            json={"code": "summer25", "discount_type": "percent", "value": 25, "max_discount_amount": 100},
        )
        assert created.status_code == 201
        assert created.json()["code"] == "SUMMER25"
        dup = client.post(
            "/api/v1/admin/coupons", headers=ah, json={"code": "SUMMER25", "discount_type": "fixed", "value": 5}
        )
        assert dup.status_code == 409
        over = client.post(
            "/api/v1/admin/coupons", headers=ah, json={"code": "TOOBIG", "discount_type": "percent", "value": 150}
        )
        assert over.status_code == 422

    def test_used_coupon_deactivated_not_deleted(self, client, db, admin):
        from tests.conftest import make_coupon

        ah = auth_header(client, db, admin)
        coupon = make_coupon(db, "USED", value=5, discount_type="fixed", used_count=3)
        resp = client.delete(f"/api/v1/admin/coupons/{coupon.id}", headers=ah)
        assert resp.json()["deactivated"] is True


class TestSettingsAndAudit:
    def test_update_settings(self, client, db, admin):
        ah = auth_header(client, db, admin)
        resp = client.put(
            "/api/v1/admin/settings", headers=ah, json={"tax_percent": 5.0, "shipping_fee": 40}
        )
        assert resp.json()["tax_percent"] == 5.0
        assert resp.json()["shipping_fee"] == 40.0

    def test_invalid_setting_rejected(self, client, db, admin):
        ah = auth_header(client, db, admin)
        resp = client.put("/api/v1/admin/settings", headers=ah, json={"tax_percent": 500})
        assert resp.status_code == 400

    def test_audit_log_records_admin_actions(self, client, db, admin):
        ah = auth_header(client, db, admin)
        client.post("/api/v1/admin/books", headers=ah, json={"title": "Audited Book", "price": 100, "stock_quantity": 1})
        logs = client.get("/api/v1/admin/audit-logs", headers=ah).json()
        assert any(entry["action"] == "book.create" for entry in logs["items"])

    def test_notifications_flow(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        client.post(f"/api/v1/cart/items", headers=ch, json={"book_id": book.id, "quantity": 1})
        client.post(
            f"/api/v1/orders/checkout",
            headers=ch,
            json={
                "shipping_address": {"full_name": "J", "phone": "+91 9876543210", "line1": "1 St", "city": "X", "state": "Y", "postal_code": "1", "country": "India"},
                "payment_method": "cod",
            },
        )
        resp = client.get("/api/v1/notifications", headers=ch).json()
        assert resp["total"] >= 1
        assert resp["unread_count"] >= 1
        first_id = resp["items"][0]["id"]
        client.post(f"/api/v1/notifications/{first_id}/read", headers=ch)
        after = client.get("/api/v1/notifications/unread-count", headers=ch).json()
        assert after["count"] == resp["unread_count"] - 1
