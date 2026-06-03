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


def _make_batch(db, user_id, department="测试", reporter="测试", **kwargs):
    from app.services.batch_service import create_batch
    from app.schemas.batch import CreateBatchRequest
    return create_batch(db, user_id, CreateBatchRequest(department=department, reporter=reporter, **kwargs))


def _get_headers(user):
    from app.services.auth_service import create_access_token
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


class TestUpdateBatchAPI:
    def test_update_department(self, client, db):
        user = _make_user(db, "api_final_upd")
        batch = _make_batch(db, user.id, "旧部门", "张三")
        headers = _get_headers(user)

        resp = client.put(
            f"/api/batches/{batch.id}",
            json={"department": "新部门"},
            headers=headers,
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["department"] == "新部门"

    def test_update_not_found(self, client, db):
        user = _make_user(db, "api_final_upd_nf")
        headers = _get_headers(user)

        resp = client.put(
            "/api/batches/99999",
            json={"department": "X"},
            headers=headers,
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_requires_auth(self, client):
        resp = client.put("/api/batches/1", json={"department": "X"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestDeleteBatchAPI:
    def test_delete_batch(self, client, db):
        user = _make_user(db, "api_final_del")
        inv = _make_invoice(db, user.id, status="confirmed", amount=100)
        batch = _make_batch(db, user.id)
        headers = _get_headers(user)

        client.post(
            f"/api/batches/{batch.id}/invoices",
            json={"invoice_ids": [inv.id]},
            headers=headers,
        )

        resp = client.delete(f"/api/batches/{batch.id}", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["deleted"] is True
        assert data["released_invoice_count"] == 1

    def test_delete_not_found(self, client, db):
        user = _make_user(db, "api_final_del_nf")
        headers = _get_headers(user)

        resp = client.delete("/api/batches/99999", headers=headers)
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_requires_auth(self, client):
        resp = client.delete("/api/batches/1")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestExportExcelAPI:
    def test_export_no_invoices(self, client, db):
        user = _make_user(db, "api_final_exp1")
        batch = _make_batch(db, user.id)
        headers = _get_headers(user)

        resp = client.get(f"/api/batches/{batch.id}/export-excel", headers=headers)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_export_with_invoices(self, client, db):
        user = _make_user(db, "api_final_exp2")
        inv = _make_invoice(db, user.id, status="confirmed", amount=100.0,
                            invoice_date=date(2026, 5, 15))
        batch = _make_batch(db, user.id, "研发部", "张三",
                            period_start=date(2026, 5, 1), period_end=date(2026, 5, 31))
        headers = _get_headers(user)

        client.post(
            f"/api/batches/{batch.id}/invoices",
            json={"invoice_ids": [inv.id]},
            headers=headers,
        )

        resp = client.get(f"/api/batches/{batch.id}/export-excel", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in resp.headers.get("content-type", "")
        assert "filename" in resp.headers.get("content-disposition", "")
        assert len(resp.content) > 0

    def test_export_requires_auth(self, client, db):
        user = _make_user(db, "api_final_exp_auth")
        batch = _make_batch(db, user.id)

        resp = client.get(f"/api/batches/{batch.id}/export-excel")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED