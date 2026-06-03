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


class TestArchiveBatchService:
    def test_archive_success(self, db):
        from app.services.batch_service import archive_batch

        user = User(username="ar1", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        batch = _make_batch(user.id, status="completed")
        db.add(batch); db.commit(); db.refresh(batch)

        inv1 = _make_invoice(user.id)
        inv2 = _make_invoice(user.id)
        db.add_all([inv1, inv2]); db.commit()

        db.add_all([
            BatchInvoice(batch_id=batch.id, invoice_id=inv1.id),
            BatchInvoice(batch_id=batch.id, invoice_id=inv2.id),
        ]); db.commit()

        result = archive_batch(db, user.id, batch.id)
        assert result["archived"] is True
        assert result["archived_invoice_count"] == 2
        assert result["batch_status"] == "archived"

        db.refresh(batch)
        assert batch.status == "archived"
        db.refresh(inv1)
        assert inv1.status == "archived"
        db.refresh(inv2)
        assert inv2.status == "archived"

    def test_archive_not_completed(self, db):
        from app.services.batch_service import archive_batch

        user = User(username="ar2", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        batch = _make_batch(user.id, status="draft")
        db.add(batch); db.commit(); db.refresh(batch)

        inv = _make_invoice(user.id)
        db.add(inv); db.commit()
        db.add(BatchInvoice(batch_id=batch.id, invoice_id=inv.id)); db.commit()

        with pytest.raises(HTTPException) as exc:
            archive_batch(db, user.id, batch.id)
        assert exc.value.status_code == 400
        assert "只有已完成状态的批次才能归档" in exc.value.detail

    def test_archive_no_invoices(self, db):
        from app.services.batch_service import archive_batch

        user = User(username="ar3", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        batch = _make_batch(user.id, status="completed")
        db.add(batch); db.commit(); db.refresh(batch)

        with pytest.raises(HTTPException) as exc:
            archive_batch(db, user.id, batch.id)
        assert exc.value.status_code == 400
        assert "该批次无发票" in exc.value.detail

    def test_archive_already_archived(self, db):
        from app.services.batch_service import archive_batch

        user = User(username="ar4", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        batch = _make_batch(user.id, status="archived")
        db.add(batch); db.commit(); db.refresh(batch)

        with pytest.raises(HTTPException) as exc:
            archive_batch(db, user.id, batch.id)
        assert exc.value.status_code == 400

    def test_archive_not_found(self, db):
        from app.services.batch_service import archive_batch

        user = User(username="ar5", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        with pytest.raises(HTTPException) as exc:
            archive_batch(db, user.id, 999)
        assert exc.value.status_code == 404

    def test_archive_wrong_user(self, db):
        from app.services.batch_service import archive_batch

        u1 = User(username="ar6a", password_hash="hash")
        u2 = User(username="ar6b", password_hash="hash")
        db.add_all([u1, u2]); db.commit()
        db.refresh(u1); db.refresh(u2)

        batch = _make_batch(u1.id, status="completed")
        db.add(batch); db.commit(); db.refresh(batch)

        inv = _make_invoice(u1.id)
        db.add(inv); db.commit()
        db.add(BatchInvoice(batch_id=batch.id, invoice_id=inv.id)); db.commit()

        with pytest.raises(HTTPException) as exc:
            archive_batch(db, u2.id, batch.id)
        assert exc.value.status_code == 404


class TestRestoreArchivedInvoice:
    def test_restore_success(self, db):
        from app.services.invoice_service import restore_archived_invoice

        user = User(username="rs1", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        inv = _make_invoice(user.id, status="archived")
        db.add(inv); db.commit(); db.refresh(inv)

        result = restore_archived_invoice(db, user.id, inv.id)
        assert result.status == "confirmed"
        db.refresh(inv)
        assert inv.status == "confirmed"

    def test_restore_not_archived(self, db):
        from app.services.invoice_service import restore_archived_invoice

        user = User(username="rs2", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        inv = _make_invoice(user.id, status="confirmed")
        db.add(inv); db.commit(); db.refresh(inv)

        with pytest.raises(HTTPException) as exc:
            restore_archived_invoice(db, user.id, inv.id)
        assert exc.value.status_code == 400
        assert "只有已归档状态的发票才能恢复" in exc.value.detail

    def test_restore_wrong_user(self, db):
        from app.services.invoice_service import restore_archived_invoice

        u1 = User(username="rs3a", password_hash="hash")
        u2 = User(username="rs3b", password_hash="hash")
        db.add_all([u1, u2]); db.commit()
        db.refresh(u1); db.refresh(u2)

        inv = _make_invoice(u1.id, status="archived")
        db.add(inv); db.commit(); db.refresh(inv)

        with pytest.raises(HTTPException) as exc:
            restore_archived_invoice(db, u2.id, inv.id)
        assert exc.value.status_code == 404


class TestListInvoicesExcludesArchived:
    def test_all_view_excludes_archived(self, db):
        from app.services.invoice_service import list_invoices

        user = User(username="le1", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        db.add_all([
            _make_invoice(user.id, status="confirmed", invoice_no="INV001"),
            _make_invoice(user.id, status="confirmed", invoice_no="INV002"),
            _make_invoice(user.id, status="archived", invoice_no="INV003"),
        ]); db.commit()

        result = list_invoices(db, user.id)
        assert result.total == 2
        for item in result.items:
            assert item.status != "archived"

    def test_archived_view_returns_only_archived(self, db):
        from app.services.invoice_service import list_invoices

        user = User(username="le2", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        db.add_all([
            _make_invoice(user.id, status="confirmed", invoice_no="INV001"),
            _make_invoice(user.id, status="archived", invoice_no="INV002"),
            _make_invoice(user.id, status="archived", invoice_no="INV003"),
        ]); db.commit()

        result = list_invoices(db, user.id, state="archived")
        assert result.total == 2
        for item in result.items:
            assert item.status == "archived"

    def test_archived_view_empty(self, db):
        from app.services.invoice_service import list_invoices

        user = User(username="le3", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        result = list_invoices(db, user.id, state="archived")
        assert result.total == 0

    def test_confirmed_view_excludes_archived(self, db):
        from app.services.invoice_service import list_invoices

        user = User(username="le4", password_hash="hash")
        db.add(user); db.commit(); db.refresh(user)

        db.add_all([
            _make_invoice(user.id, status="confirmed", invoice_no="INV001"),
            _make_invoice(user.id, status="archived", invoice_no="INV002"),
        ]); db.commit()

        result = list_invoices(db, user.id, state="confirmed")
        assert result.total == 1
        assert result.items[0].status == "confirmed"


class TestArchiveAPI:
    def test_api_archive_success(self, client, auth_headers, test_user, db):
        batch = _make_batch(test_user.id, status="completed")
        db.add(batch); db.commit(); db.refresh(batch)

        inv = _make_invoice(test_user.id)
        db.add(inv); db.commit()
        db.add(BatchInvoice(batch_id=batch.id, invoice_id=inv.id)); db.commit()

        r = client.post(f"/api/batches/{batch.id}/archive", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["archived"] is True
        assert data["archived_invoice_count"] == 1
        assert data["batch_status"] == "archived"

    def test_api_archive_no_auth(self, client):
        r = client.post("/api/batches/1/archive")
        assert r.status_code == 401


class TestRestoreAPI:
    def test_api_restore_success(self, client, auth_headers, test_user, db):
        inv = _make_invoice(test_user.id, status="archived")
        db.add(inv); db.commit(); db.refresh(inv)

        r = client.post(f"/api/invoices/{inv.id}/restore-from-archive", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "confirmed"

    def test_api_restore_no_auth(self, client):
        r = client.post("/api/invoices/1/restore-from-archive")
        assert r.status_code == 401