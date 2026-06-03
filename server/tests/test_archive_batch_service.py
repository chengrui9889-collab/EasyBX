import pytest
from fastapi import HTTPException

from app.models.batch import BatchInvoice, ReimbursementBatch
from app.models.invoice import Invoice
from app.models.user import User
from app.schemas.batch import (
    AddInvoicesRequest,
    UpdateBatchInvoiceRequest,
    UpdateBatchRequest,
)


def _make_batch(user_id, **kwargs):
    defaults = {"department": "研发部", "reporter": "张三", "status": "draft"}
    defaults.update(kwargs)
    return ReimbursementBatch(user_id=user_id, **defaults)


class TestCompleteBatchService:
    def test_complete_batch_success(self, db):
        from app.services.batch_service import complete_batch

        user = User(username="cb1", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        batch = _make_batch(user.id)
        db.add(batch); db.commit(); db.refresh(batch)

        result = complete_batch(db, user.id, batch.id)
        assert result.status == "completed"
        db.refresh(batch)
        assert batch.status == "completed"

    def test_complete_batch_already_completed(self, db):
        from app.services.batch_service import complete_batch

        user = User(username="cb2", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        batch = _make_batch(user.id, status="completed")
        db.add(batch); db.commit(); db.refresh(batch)

        with pytest.raises(HTTPException) as exc:
            complete_batch(db, user.id, batch.id)
        assert exc.value.status_code == 400
        assert "只有草稿状态的批次才能完成" in exc.value.detail

    def test_complete_batch_already_archived(self, db):
        from app.services.batch_service import complete_batch

        user = User(username="cb3", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        batch = _make_batch(user.id, status="archived")
        db.add(batch); db.commit(); db.refresh(batch)

        with pytest.raises(HTTPException) as exc:
            complete_batch(db, user.id, batch.id)
        assert exc.value.status_code == 400

    def test_complete_batch_not_found(self, db):
        from app.services.batch_service import complete_batch

        user = User(username="cb4", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        with pytest.raises(HTTPException) as exc:
            complete_batch(db, user.id, 999)
        assert exc.value.status_code == 404

    def test_complete_batch_wrong_user(self, db):
        from app.services.batch_service import complete_batch

        user1 = User(username="cb5a", password_hash="hash")
        user2 = User(username="cb5b", password_hash="hash")
        db.add_all([user1, user2]); db.commit()
        db.refresh(user1); db.refresh(user2)

        batch = _make_batch(user1.id)
        db.add(batch); db.commit(); db.refresh(batch)

        with pytest.raises(HTTPException) as exc:
            complete_batch(db, user2.id, batch.id)
        assert exc.value.status_code == 404


class TestCompleteBatchLocksEditing:
    def test_update_batch_blocked_on_completed(self, db):
        from app.services.batch_service import update_batch

        user = User(username="lock1", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        batch = _make_batch(user.id, status="completed")
        db.add(batch); db.commit(); db.refresh(batch)

        with pytest.raises(HTTPException) as exc:
            update_batch(db, user.id, batch.id, UpdateBatchRequest(department="新部门"))
        assert exc.value.status_code == 400
        assert "只有草稿状态的批次才能修改" in exc.value.detail

    def test_add_invoices_blocked_on_completed(self, db):
        from app.services.batch_service import add_invoices

        user = User(username="lock2", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        batch = _make_batch(user.id, status="completed")
        db.add(batch); db.commit(); db.refresh(batch)

        invoice = Invoice(user_id=user.id, status="confirmed", amount=100.0, file_path="/tmp/test.pdf")
        db.add(invoice); db.commit(); db.refresh(invoice)

        with pytest.raises(HTTPException) as exc:
            add_invoices(db, user.id, batch.id, AddInvoicesRequest(invoice_ids=[invoice.id]))
        assert exc.value.status_code == 400

    def test_remove_invoice_blocked_on_completed(self, db):
        from app.services.batch_service import remove_invoice

        user = User(username="lock3", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        batch = _make_batch(user.id, status="completed")
        db.add(batch); db.commit(); db.refresh(batch)

        invoice = Invoice(user_id=user.id, status="confirmed", amount=100.0, file_path="/tmp/test.pdf")
        db.add(invoice); db.commit(); db.refresh(invoice)

        bi = BatchInvoice(batch_id=batch.id, invoice_id=invoice.id)
        db.add(bi); db.commit()

        with pytest.raises(HTTPException) as exc:
            remove_invoice(db, user.id, batch.id, invoice.id)
        assert exc.value.status_code == 400

    def test_update_batch_invoice_blocked_on_completed(self, db):
        from app.services.batch_service import update_batch_invoice

        user = User(username="lock4", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        batch = _make_batch(user.id, status="completed")
        db.add(batch); db.commit(); db.refresh(batch)

        invoice = Invoice(user_id=user.id, status="confirmed", amount=100.0, file_path="/tmp/test.pdf")
        db.add(invoice); db.commit(); db.refresh(invoice)

        bi = BatchInvoice(batch_id=batch.id, invoice_id=invoice.id)
        db.add(bi); db.commit()

        with pytest.raises(HTTPException) as exc:
            update_batch_invoice(db, user.id, batch.id, invoice.id, UpdateBatchInvoiceRequest(quantity=5))
        assert exc.value.status_code == 400

    def test_draft_still_allows_editing(self, db):
        from app.services.batch_service import update_batch, add_invoices, remove_invoice, update_batch_invoice

        user = User(username="lock5", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        batch = _make_batch(user.id)
        db.add(batch); db.commit(); db.refresh(batch)

        invoice = Invoice(user_id=user.id, status="confirmed", amount=100.0, file_path="/tmp/test.pdf")
        db.add(invoice); db.commit(); db.refresh(invoice)

        result = update_batch(db, user.id, batch.id, UpdateBatchRequest(department="新部门"))
        assert result.department == "新部门"

        result2 = add_invoices(db, user.id, batch.id, AddInvoicesRequest(invoice_ids=[invoice.id]))
        assert len(result2) == 1

        result3 = update_batch_invoice(db, user.id, batch.id, invoice.id, UpdateBatchInvoiceRequest(quantity=2))
        assert result3["quantity"] == 2.0

        remove_invoice(db, user.id, batch.id, invoice.id)
        bi = db.query(BatchInvoice).filter(
            BatchInvoice.batch_id == batch.id, BatchInvoice.invoice_id == invoice.id
        ).first()
        assert bi is None


class TestCompleteBatchAPI:
    def test_api_complete_batch_success(self, client, auth_headers, test_user, db):
        batch = _make_batch(test_user.id)
        db.add(batch); db.commit(); db.refresh(batch)

        r = client.put(f"/api/batches/{batch.id}/complete", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "completed"

    def test_api_complete_batch_not_found(self, client, auth_headers):
        r = client.put("/api/batches/999/complete", headers=auth_headers)
        assert r.status_code == 404

    def test_api_complete_batch_no_auth(self, client):
        r = client.put("/api/batches/1/complete")
        assert r.status_code == 401