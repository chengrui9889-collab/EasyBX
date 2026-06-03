from datetime import date

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


class TestGetBatchDetailAPI:
    def test_returns_detail(self, client, db):
        user = _make_user(db, "api_detail1")
        batch = _make_batch(db, user.id, "研发部", "张三")
        headers = _get_headers(user)

        resp = client.get(f"/api/batches/{batch.id}", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["department"] == "研发部"
        assert data["reporter"] == "张三"
        assert data["ledger_rows"] == []

    def test_with_invoices(self, client, db):
        user = _make_user(db, "api_detail2")
        inv = _make_invoice(db, user.id, status="confirmed", amount=34.0,
                            invoice_date=date(2026, 5, 15))
        batch = _make_batch(db, user.id)
        headers = _get_headers(user)

        client.post(
            f"/api/batches/{batch.id}/invoices",
            json={"invoice_ids": [inv.id]},
            headers=headers,
        )

        resp = client.get(f"/api/batches/{batch.id}", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data["ledger_rows"]) == 1
        row = data["ledger_rows"][0]
        assert row["amount"] == 34.0
        assert row["quantity"] == 1.0
        assert row["unit_price"] == 34.0

    def test_empty_invoices(self, client, db):
        user = _make_user(db, "api_detail3")
        batch = _make_batch(db, user.id)
        headers = _get_headers(user)

        resp = client.get(f"/api/batches/{batch.id}", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["ledger_rows"] == []

    def test_not_found(self, client, db):
        user = _make_user(db, "api_detail4")
        headers = _get_headers(user)

        resp = client.get("/api/batches/99999", headers=headers)
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_requires_auth(self, client):
        resp = client.get("/api/batches/1")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED