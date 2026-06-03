from fastapi import status

from app.models.invoice import Invoice


def _make_user(db, username):
    from app.models.user import User
    user = User(username=username, password_hash="hash")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_invoice(db, user_id, status="confirmed", amount=100.0, **kwargs):
    inv = Invoice(
        user_id=user_id,
        file_path=f"/tmp/{user_id}/test.pdf",
        status=status,
        amount=amount,
        **kwargs,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


def _make_batch(db, user_id, department="测试", reporter="测试"):
    from app.services.batch_service import create_batch
    from app.schemas.batch import CreateBatchRequest
    return create_batch(db, user_id, CreateBatchRequest(department=department, reporter=reporter))


def _get_headers(user):
    from app.services.auth_service import create_access_token
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


class TestListAvailableInvoicesAPI:
    def test_returns_only_confirmed(self, client, db):
        user = _make_user(db, "api_avail1")
        _make_invoice(db, user.id, status="processing", amount=50)
        confirmed = _make_invoice(db, user.id, status="confirmed", amount=100)
        headers = _get_headers(user)

        resp = client.get("/api/batches/available-invoices", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == confirmed.id

    def test_excludes_invoices_in_batches(self, client, db):
        user = _make_user(db, "api_avail2")
        inv1 = _make_invoice(db, user.id, status="confirmed", amount=100)
        inv2 = _make_invoice(db, user.id, status="confirmed", amount=200)
        batch = _make_batch(db, user.id)
        headers = _get_headers(user)

        client.post(
            f"/api/batches/{batch.id}/invoices",
            json={"invoice_ids": [inv1.id]},
            headers=headers,
        )

        resp = client.get("/api/batches/available-invoices", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == inv2.id

    def test_keyword_search(self, client, db):
        user = _make_user(db, "api_avail3")
        _make_invoice(db, user.id, status="confirmed", vendor="铁路总公司")
        _make_invoice(db, user.id, status="confirmed", vendor="滴滴出行")
        headers = _get_headers(user)

        resp = client.get("/api/batches/available-invoices?keyword=铁路", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["vendor"] == "铁路总公司"

    def test_pagination(self, client, db):
        user = _make_user(db, "api_avail4")
        for i in range(5):
            _make_invoice(db, user.id, status="confirmed", amount=100.0 + i)
        headers = _get_headers(user)

        resp = client.get("/api/batches/available-invoices?page=1&page_size=2", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["items"]) == 2

    def test_requires_auth(self, client):
        resp = client.get("/api/batches/available-invoices")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestAddInvoicesAPI:
    def test_add_invoices_success(self, client, db):
        user = _make_user(db, "api_add1")
        inv1 = _make_invoice(db, user.id, status="confirmed", amount=100)
        inv2 = _make_invoice(db, user.id, status="confirmed", amount=200)
        batch = _make_batch(db, user.id)
        headers = _get_headers(user)

        resp = client.post(
            f"/api/batches/{batch.id}/invoices",
            json={"invoice_ids": [inv1.id, inv2.id]},
            headers=headers,
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data) == 2
        assert data[0]["quantity"] == 1.0

    def test_rejects_processing_invoice(self, client, db):
        user = _make_user(db, "api_add2")
        inv = _make_invoice(db, user.id, status="processing", amount=100)
        batch = _make_batch(db, user.id)
        headers = _get_headers(user)

        resp = client.post(
            f"/api/batches/{batch.id}/invoices",
            json={"invoice_ids": [inv.id]},
            headers=headers,
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_rejects_non_owner(self, client, db):
        user1 = _make_user(db, "api_add_owner")
        user2 = _make_user(db, "api_add_other")
        inv = _make_invoice(db, user2.id, status="confirmed", amount=100)
        batch = _make_batch(db, user1.id)
        headers = _get_headers(user2)

        resp = client.post(
            f"/api/batches/{batch.id}/invoices",
            json={"invoice_ids": [inv.id]},
            headers=headers,
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_requires_auth(self, client, db):
        user = _make_user(db, "api_add_auth")
        batch = _make_batch(db, user.id)

        resp = client.post(
            f"/api/batches/{batch.id}/invoices",
            json={"invoice_ids": [1]},
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_batch_not_found(self, client, db):
        user = _make_user(db, "api_add_nf")
        headers = _get_headers(user)

        resp = client.post(
            "/api/batches/99999/invoices",
            json={"invoice_ids": [1]},
            headers=headers,
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND


class TestRemoveInvoiceAPI:
    def test_remove_invoice_success(self, client, db):
        user = _make_user(db, "api_rm1")
        inv = _make_invoice(db, user.id, status="confirmed", amount=100)
        batch = _make_batch(db, user.id)
        headers = _get_headers(user)

        client.post(
            f"/api/batches/{batch.id}/invoices",
            json={"invoice_ids": [inv.id]},
            headers=headers,
        )

        resp = client.delete(
            f"/api/batches/{batch.id}/invoices/{inv.id}",
            headers=headers,
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["removed"] is True

    def test_remove_invoice_not_found(self, client, db):
        user = _make_user(db, "api_rm2")
        batch = _make_batch(db, user.id)
        headers = _get_headers(user)

        resp = client.delete(
            f"/api/batches/{batch.id}/invoices/99999",
            headers=headers,
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_requires_auth(self, client, db):
        user = _make_user(db, "api_rm_auth")
        batch = _make_batch(db, user.id)

        resp = client.delete(f"/api/batches/{batch.id}/invoices/1")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED