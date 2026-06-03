import pytest
from fastapi import HTTPException

from app.models.batch import BatchInvoice, ReimbursementBatch
from app.models.invoice import Invoice
from app.models.user import User


def _make_batch(user_id, **kwargs):
    defaults = {"department": "研发部", "reporter": "张三", "status": "draft"}
    defaults.update(kwargs)
    return ReimbursementBatch(user_id=user_id, **defaults)


def _make_invoice(user_id, **kwargs):
    defaults = {"user_id": user_id, "status": "confirmed", "amount": 100.0, "file_path": "/tmp/test.pdf"}
    defaults.update(kwargs)
    return Invoice(**defaults)


class TestUnarchiveBatchService:
    def test_unarchive_success(self, db):
        from app.services.batch_service import unarchive_batch

        user = User(username="ua1", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        batch = _make_batch(user.id, status="archived")
        db.add(batch); db.commit(); db.refresh(batch)

        inv1 = _make_invoice(user.id, status="archived")
        inv2 = _make_invoice(user.id, status="archived")
        db.add_all([inv1, inv2]); db.commit()

        db.add_all([
            BatchInvoice(batch_id=batch.id, invoice_id=inv1.id),
            BatchInvoice(batch_id=batch.id, invoice_id=inv2.id),
        ]); db.commit()

        result = unarchive_batch(db, user.id, batch.id)
        assert result["unarchived"] is True
        assert result["batch_status"] == "completed"
        assert result["restored_invoice_count"] == 2

        db.refresh(batch)
        assert batch.status == "completed"
        db.refresh(inv1)
        assert inv1.status == "confirmed"
        db.refresh(inv2)
        assert inv2.status == "confirmed"

    def test_unarchive_not_archived(self, db):
        from app.services.batch_service import unarchive_batch

        user = User(username="ua2", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        batch = _make_batch(user.id, status="completed")
        db.add(batch); db.commit(); db.refresh(batch)

        with pytest.raises(HTTPException) as exc:
            unarchive_batch(db, user.id, batch.id)
        assert exc.value.status_code == 400
        assert "只有已归档状态的批次才能撤销归档" in exc.value.detail

    def test_unarchive_draft(self, db):
        from app.services.batch_service import unarchive_batch

        user = User(username="ua3", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        batch = _make_batch(user.id, status="draft")
        db.add(batch); db.commit(); db.refresh(batch)

        with pytest.raises(HTTPException) as exc:
            unarchive_batch(db, user.id, batch.id)
        assert exc.value.status_code == 400
        assert "只有已归档状态的批次才能撤销归档" in exc.value.detail

    def test_unarchive_not_found(self, db):
        from app.services.batch_service import unarchive_batch

        user = User(username="ua4", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        with pytest.raises(HTTPException) as exc:
            unarchive_batch(db, user.id, 999)
        assert exc.value.status_code == 404

    def test_unarchive_wrong_user(self, db):
        from app.services.batch_service import unarchive_batch

        u1 = User(username="ua5a", password_hash="hash")
        u2 = User(username="ua5b", password_hash="hash")
        db.add_all([u1, u2]); db.commit()
        db.refresh(u1); db.refresh(u2)

        batch = _make_batch(u1.id, status="archived")
        db.add(batch); db.commit(); db.refresh(batch)

        with pytest.raises(HTTPException) as exc:
            unarchive_batch(db, u2.id, batch.id)
        assert exc.value.status_code == 404


class TestListBatchesWithStatus:
    def test_filter_by_status_draft(self, db):
        from app.services.batch_service import list_batches

        user = User(username="ls1", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        db.add(_make_batch(user.id, status="draft"))
        db.add(_make_batch(user.id, status="completed"))
        db.add(_make_batch(user.id, status="archived"))
        db.commit()

        result = list_batches(db, user.id, status="draft")
        assert result.total == 1
        assert result.items[0].status == "draft"

    def test_filter_by_status_archived(self, db):
        from app.services.batch_service import list_batches

        user = User(username="ls2", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        db.add(_make_batch(user.id, status="draft"))
        db.add(_make_batch(user.id, status="archived"))
        db.add(_make_batch(user.id, status="archived"))
        db.commit()

        result = list_batches(db, user.id, status="archived")
        assert result.total == 2

    def test_no_filter_returns_all(self, db):
        from app.services.batch_service import list_batches

        user = User(username="ls3", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        db.add(_make_batch(user.id, status="draft"))
        db.add(_make_batch(user.id, status="completed"))
        db.add(_make_batch(user.id, status="archived"))
        db.commit()

        result = list_batches(db, user.id)
        assert result.total == 3


class TestUnarchiveAPI:
    def test_api_unarchive_success(self, client, auth_headers, test_user, db):
        batch = _make_batch(test_user.id, status="archived")
        db.add(batch); db.commit(); db.refresh(batch)

        r = client.post(f"/api/batches/{batch.id}/unarchive", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["unarchived"] is True
        assert data["batch_status"] == "completed"

    def test_api_unarchive_no_auth(self, client):
        r = client.post("/api/batches/1/unarchive")
        assert r.status_code == 401