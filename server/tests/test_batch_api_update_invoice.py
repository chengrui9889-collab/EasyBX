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


class TestUpdateBatchInvoiceAPI:
    def test_update_quantity(self, client, db):
        user = _make_user(db, "api_upd_q")
        inv = _make_invoice(db, user.id, status="confirmed", amount=100.0)
        batch = _make_batch(db, user.id)
        headers = _get_headers(user)

        client.post(
            f"/api/batches/{batch.id}/invoices",
            json={"invoice_ids": [inv.id]},
            headers=headers,
        )

        resp = client.put(
            f"/api/batches/{batch.id}/invoices/{inv.id}",
            json={"quantity": 4},
            headers=headers,
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["quantity"] == 4.0
        assert data["unit_price"] == 25.0

    def test_update_advance_amount(self, client, db):
        user = _make_user(db, "api_upd_aa")
        inv = _make_invoice(db, user.id, status="confirmed", amount=200.0)
        batch = _make_batch(db, user.id)
        headers = _get_headers(user)

        client.post(
            f"/api/batches/{batch.id}/invoices",
            json={"invoice_ids": [inv.id]},
            headers=headers,
        )

        resp = client.put(
            f"/api/batches/{batch.id}/invoices/{inv.id}",
            json={"advance_amount": 150.0},
            headers=headers,
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["advance_amount"] == 150.0

    def test_update_remark(self, client, db):
        user = _make_user(db, "api_upd_rm")
        inv = _make_invoice(db, user.id, status="confirmed", amount=100.0)
        batch = _make_batch(db, user.id)
        headers = _get_headers(user)

        client.post(
            f"/api/batches/{batch.id}/invoices",
            json={"invoice_ids": [inv.id]},
            headers=headers,
        )

        resp = client.put(
            f"/api/batches/{batch.id}/invoices/{inv.id}",
            json={"remark": "打车费"},
            headers=headers,
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["remark"] == "打车费"

    def test_quantity_zero_returns_400(self, client, db):
        user = _make_user(db, "api_upd_q0")
        inv = _make_invoice(db, user.id, status="confirmed", amount=100.0)
        batch = _make_batch(db, user.id)
        headers = _get_headers(user)

        client.post(
            f"/api/batches/{batch.id}/invoices",
            json={"invoice_ids": [inv.id]},
            headers=headers,
        )

        resp = client.put(
            f"/api/batches/{batch.id}/invoices/{inv.id}",
            json={"quantity": 0},
            headers=headers,
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_requires_auth(self, client, db):
        user = _make_user(db, "api_upd_auth")
        batch = _make_batch(db, user.id)

        resp = client.put(
            f"/api/batches/{batch.id}/invoices/1",
            json={"quantity": 2},
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_batch_not_found(self, client, db):
        user = _make_user(db, "api_upd_nf")
        headers = _get_headers(user)

        resp = client.put(
            "/api/batches/99999/invoices/1",
            json={"quantity": 2},
            headers=headers,
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND