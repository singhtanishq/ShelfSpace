"""Catalog: search, filters, sorting, facets, related books."""


class TestBookBrowsing:
    def test_list_books_excludes_inactive(self, client, db):
        from tests.conftest import make_book

        make_book(db, "Active Book", stock=5)
        make_book(db, "Hidden Book", stock=5, active=False)
        resp = client.get("/api/v1/books")
        titles = [b["title"] for b in resp.json()["items"]]
        assert "Active Book" in titles
        assert "Hidden Book" not in titles

    def test_search_by_title(self, client, db):
        from tests.conftest import make_book

        make_book(db, "The Rusty Compass")
        make_book(db, "Unrelated Volume")
        resp = client.get("/api/v1/books", params={"q": "compass"})
        assert resp.json()["total"] == 1
        assert resp.json()["items"][0]["title"] == "The Rusty Compass"

    def test_price_filter_and_sort(self, client, db):
        from tests.conftest import make_book

        make_book(db, "Cheap", price=50)
        make_book(db, "Mid", price=200)
        make_book(db, "Dear", price=500)
        resp = client.get("/api/v1/books", params={"sort": "price_desc", "max_price": 500})
        prices = [b["price"] for b in resp.json()["items"]]
        assert prices == sorted(prices, reverse=True)

    def test_effective_price_applies_discount(self, client, db):
        from tests.conftest import make_book

        make_book(db, "Discounted", price=200, discount=25)
        resp = client.get("/api/v1/books", params={"q": "Discounted"})
        assert resp.json()["items"][0]["effective_price"] == 150.0

    def test_book_detail(self, client, db, book):
        resp = client.get(f"/api/v1/books/{book.slug}")
        assert resp.status_code == 200
        assert resp.json()["title"] == book.title
        assert "available_quantity" in resp.json()

    def test_book_detail_404(self, client, db):
        assert client.get("/api/v1/books/does-not-exist").status_code == 404

    def test_facets(self, client, db, book):
        resp = client.get("/api/v1/books/facets")
        assert resp.status_code == 200
        assert resp.json()["price_max"] >= 100

    def test_home_feed(self, client, db, book):
        resp = client.get("/api/v1/home")
        assert resp.status_code == 200
        assert "best_sellers" in resp.json()

    def test_related_books(self, client, db):
        from tests.conftest import make_book

        a = make_book(db, "Shared Universe")
        b = make_book(db, "Sequel Title")
        # both share the default "Fiction" category
        resp = client.get(f"/api/v1/books/{a.slug}/related")
        assert resp.status_code == 200
        assert any(item["id"] == b.id for item in resp.json()["related"])
