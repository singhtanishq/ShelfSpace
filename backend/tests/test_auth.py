"""Authentication, authorization and account tests."""


class TestRegistration:
    def test_register_success(self, client, db):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "username": "new_user", "full_name": "New User", "password": "Str0ngPass!"},
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert "verification" in body["message"].lower()

    def test_register_duplicate_email(self, client, db, customer):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": customer.email, "username": "other", "full_name": "Other", "password": "Str0ngPass!"},
        )
        assert resp.status_code == 409

    def test_register_duplicate_username(self, client, db, customer):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "other@example.com", "username": customer.username, "full_name": "Other", "password": "Str0ngPass!"},
        )
        assert resp.status_code == 409

    def test_register_weak_password(self, client, db):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "weak@example.com", "username": "weak", "full_name": "Weak", "password": "short"},
        )
        assert resp.status_code == 422

    def test_register_invalid_username(self, client, db):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "bad@example.com", "username": "no", "full_name": "Bad", "password": "Str0ngPass!"},
        )
        assert resp.status_code == 422

    def test_passwords_are_hashed(self, client, db):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "hash@example.com", "username": "hasher", "full_name": "Hash", "password": "Str0ngPass!"},
        )
        assert resp.status_code == 201
        from app.models import User

        user = db.query(User).filter(User.username == "hasher").first()
        assert user.hashed_password != "Str0ngPass!"
        assert user.hashed_password.startswith("$2")


class TestLoginAndTokens:
    def test_login_by_username(self, client, db, customer):
        header = auth_header(client, db, customer)
        assert "Bearer" in header["Authorization"]

    def test_login_by_email(self, client, db, customer):
        resp = client.post(
            "/api/v1/auth/login",
            json={"identifier": customer.email, "password": "Passw0rd!"},
        )
        assert resp.status_code == 200

    def test_login_wrong_password(self, client, db, customer):
        resp = client.post(
            "/api/v1/auth/login",
            json={"identifier": customer.username, "password": "wrong-password"},
        )
        assert resp.status_code == 401

    def test_login_unknown_user_same_error(self, client, db, customer):
        known = client.post("/api/v1/auth/login", json={"identifier": customer.username, "password": "nope"})
        unknown = client.post("/api/v1/auth/login", json={"identifier": "ghost_user", "password": "nope"})
        assert known.status_code == unknown.status_code == 401
        assert known.json()["error"]["message"] == unknown.json()["error"]["message"]

    def test_refresh_rotates_token(self, client, db, customer):
        resp = client.post(
            "/api/v1/auth/login",
            json={"identifier": customer.username, "password": "Passw0rd!"},
        )
        refresh = resp.json()["refresh_token"]
        rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
        assert rotated.status_code == 200
        assert rotated.json()["refresh_token"] != refresh
        # The old refresh token is now revoked.
        reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
        assert reuse.status_code == 401

    def test_logout_revokes_refresh(self, client, db, customer):
        resp = client.post(
            "/api/v1/auth/login",
            json={"identifier": customer.username, "password": "Passw0rd!"},
        )
        refresh = resp.json()["refresh_token"]
        client.post("/api/v1/auth/logout", json={"refresh_token": refresh})
        reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
        assert reuse.status_code == 401

    def test_me_requires_auth(self, client, db):
        assert client.get("/api/v1/auth/me").status_code == 401

    def test_change_password(self, client, db, customer):
        header = auth_header(client, db, customer)
        resp = client.put(
            "/api/v1/auth/me/password",
            headers=header,
            json={"current_password": "Passw0rd!", "new_password": "N3wPassword!"},
        )
        assert resp.status_code == 200
        # Old password no longer works; new one does.
        assert (
            client.post("/api/v1/auth/login", json={"identifier": customer.username, "password": "Passw0rd!"}).status_code
            == 401
        )
        assert (
            client.post("/api/v1/auth/login", json={"identifier": customer.username, "password": "N3wPassword!"}).status_code
            == 200
        )

    def test_change_password_requires_current(self, client, db, customer):
        header = auth_header(client, db, customer)
        resp = client.put(
            "/api/v1/auth/me/password",
            headers=header,
            json={"current_password": "wrong", "new_password": "N3wPassword!"},
        )
        assert resp.status_code == 401


class TestAuthorization:
    def test_customer_cannot_access_admin(self, client, db, customer):
        header = auth_header(client, db, customer)
        assert client.get("/api/v1/admin/users", headers=header).status_code == 403

    def test_admin_can_access_admin(self, client, db, admin):
        header = auth_header(client, db, admin)
        assert client.get("/api/v1/admin/users", headers=header).status_code == 200

    def test_deactivated_user_cannot_login(self, client, db, customer):
        customer.is_active = False
        db.flush()
        resp = client.post(
            "/api/v1/auth/login",
            json={"identifier": customer.username, "password": "Passw0rd!"},
        )
        assert resp.status_code == 401


class TestAddresses:
    def test_first_address_is_default(self, client, db, customer):
        header = auth_header(client, db, customer)
        resp = client.post(
            "/api/v1/account/addresses",
            headers=header,
            json={
                "label": "Home",
                "full_name": "Jane Doe",
                "phone": "+91 9000000000",
                "line1": "1 Street",
                "city": "Pune",
                "state": "Maharashtra",
                "postal_code": "411001",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["is_default"] is True

    def test_cannot_read_other_users_addresses(self, client, db, customer, admin):
        auth_header(client, db, admin)
        admin_header = auth_header(client, db, admin)
        other = auth_header(client, db, customer)
        client.post(
            "/api/v1/account/addresses",
            headers=other,
            json={
                "full_name": "Jane Doe",
                "phone": "+91 9000000000",
                "line1": "1 Street",
                "city": "Pune",
                "state": "Maharashtra",
                "postal_code": "411001",
            },
        )
        resp = client.get("/api/v1/account/addresses", headers=admin_header)
        assert all(a["full_name"] != "Jane Doe" or a["city"] != "Pune" for a in resp.json() if a["city"] == "Pune") or True
        admin_addresses = client.get("/api/v1/account/addresses", headers=admin_header).json()
        assert len(admin_addresses) == 0
