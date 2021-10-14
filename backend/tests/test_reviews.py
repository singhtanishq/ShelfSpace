"""Reviews: verified purchases, duplicate prevention, rating aggregates, moderation."""

from tests.conftest import auth_header, checkout, mark_delivered  # noqa: F401

API = "/api/v1"


def _purchase_and_deliver(client, db, ch, ah, book):
    order = checkout(client, ch, book.id)
    mark_delivered(client, ah, order["order_number"])
    return order


class TestReviews:
    def test_review_requires_purchase(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        resp = client.post(
            f"{API}/books/{book.slug}/reviews", headers=ch, json={"rating": 5, "content": "Great!"}
        )
        assert resp.status_code == 422

    def test_verified_purchase_review(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        _purchase_and_deliver(client, db, ch, ah, book)
        resp = client.post(f"{API}/books/{book.slug}/reviews", headers=ch, json={"rating": 4, "title": "Nice", "content": "Solid read."})
        assert resp.status_code == 201
        assert resp.json()["is_verified_purchase"] is True

    def test_duplicate_review_rejected(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        _purchase_and_deliver(client, db, ch, ah, book)
        client.post(f"{API}/books/{book.slug}/reviews", headers=ch, json={"rating": 4, "content": "First."})
        second = client.post(f"{API}/books/{book.slug}/reviews", headers=ch, json={"rating": 2, "content": "Second."})
        assert second.status_code == 409

    def test_rating_aggregate_recomputed(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        _purchase_and_deliver(client, db, ch, ah, book)
        client.post(f"{API}/books/{book.slug}/reviews", headers=ch, json={"rating": 5, "content": "Loved it."})
        detail = client.get(f"{API}/books/{book.slug}").json()
        assert detail["rating_count"] == 1
        assert detail["rating_avg"] == 5.0

    def test_user_can_edit_own_review(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        _purchase_and_deliver(client, db, ch, ah, book)
        created = client.post(f"{API}/books/{book.slug}/reviews", headers=ch, json={"rating": 3, "content": "Ok."}).json()
        updated = client.put(f"{API}/reviews/{created['id']}", headers=ch, json={"rating": 5, "content": "Better on re-read."})
        assert updated.json()["rating"] == 5

    def test_user_cannot_edit_others_review(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        _purchase_and_deliver(client, db, ch, ah, book)
        created = client.post(f"{API}/books/{book.slug}/reviews", headers=ch, json={"rating": 3, "content": "Ok."}).json()
        resp = client.put(f"{API}/reviews/{created['id']}", headers=ah, json={"rating": 1, "content": "hijack"})
        assert resp.status_code == 404

    def test_admin_hide_updates_aggregate(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        _purchase_and_deliver(client, db, ch, ah, book)
        created = client.post(f"{API}/books/{book.slug}/reviews", headers=ch, json={"rating": 1, "content": "spam"}).json()
        client.put(f"{API}/admin/reviews/{created['id']}/hide", headers=ah)
        detail = client.get(f"{API}/books/{book.slug}").json()
        assert detail["rating_count"] == 0
        assert detail["rating_avg"] == 0.0

    def test_rating_bounds(self, client, db, customer, admin, book):
        ch = auth_header(client, db, customer)
        ah = auth_header(client, db, admin)
        _purchase_and_deliver(client, db, ch, ah, book)
        resp = client.post(f"{API}/books/{book.slug}/reviews", headers=ch, json={"rating": 9, "content": "bogus"})
        assert resp.status_code == 422
