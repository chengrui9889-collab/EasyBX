from datetime import date

import pytest
from fastapi import HTTPException

from app.models.batch import BatchInvoice, ReimbursementBatch
from app.models.invoice import Invoice
from app.models.user import User
from app.schemas.batch import AddInvoicesRequest, CreateBatchRequest


def _make_user(db, username):
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

    return create_batch(db, user_id, CreateBatchRequest(department=department, reporter=reporter))


class TestListAvailableInvoices:
    def test_returns_only_confirmed(self, db):
        from app.services.batch_service import list_available_invoices

        user = _make_user(db, "avail_test")
        _make_invoice(db, user.id, status="processing", amount=50)
        confirmed = _make_invoice(db, user.id, status="confirmed", amount=100)

        resp = list_available_invoices(db, user.id)
        assert resp.total == 1
        assert resp.items[0].id == confirmed.id

    def test_excludes_invoices_in_batches(self, db):
        from app.services.batch_service import add_invoices, list_available_invoices

        user = _make_user(db, "avail_test2")
        inv1 = _make_invoice(db, user.id, status="confirmed", amount=100)
        inv2 = _make_invoice(db, user.id, status="confirmed", amount=200)

        batch_resp = _make_batch(db, user.id)
        add_invoices(db, user.id, batch_resp.id, AddInvoicesRequest(invoice_ids=[inv1.id]))

        resp = list_available_invoices(db, user.id)
        assert resp.total == 1
        assert resp.items[0].id == inv2.id

    def test_keyword_search(self, db):
        from app.services.batch_service import list_available_invoices

        user = _make_user(db, "avail_test3")
        _make_invoice(db, user.id, status="confirmed", amount=100, vendor="铁路总公司")
        _make_invoice(db, user.id, status="confirmed", amount=200, vendor="滴滴出行")

        resp = list_available_invoices(db, user.id, keyword="铁路")
        assert resp.total == 1
        assert resp.items[0].vendor == "铁路总公司"

    def test_keyword_search_invoice_no(self, db):
        from app.services.batch_service import list_available_invoices

        user = _make_user(db, "avail_test4")
        _make_invoice(db, user.id, status="confirmed", amount=100, invoice_no="ABC123")
        _make_invoice(db, user.id, status="confirmed", amount=200, invoice_no="XYZ789")

        resp = list_available_invoices(db, user.id, keyword="ABC")
        assert resp.total == 1
        assert resp.items[0].invoice_no == "ABC123"

    def test_pagination(self, db):
        from app.services.batch_service import list_available_invoices

        user = _make_user(db, "avail_test5")
        for i in range(5):
            _make_invoice(db, user.id, status="confirmed", amount=100.0 + i)

        resp = list_available_invoices(db, user.id, page=1, page_size=2)
        assert resp.total == 5
        assert resp.page == 1
        assert resp.page_size == 2
        assert len(resp.items) == 2


class TestAddInvoices:
    def test_add_invoices_success(self, db):
        from app.services.batch_service import add_invoices

        user = _make_user(db, "add_test")
        inv1 = _make_invoice(db, user.id, status="confirmed", amount=100)
        inv2 = _make_invoice(db, user.id, status="confirmed", amount=200)

        batch_resp = _make_batch(db, user.id)
        req = AddInvoicesRequest(invoice_ids=[inv1.id, inv2.id])
        result = add_invoices(db, user.id, batch_resp.id, req)

        assert len(result) == 2
        for row in result:
            assert row["quantity"] == 1.0
            assert row["advance_amount"] in (100.0, 200.0)

    def test_add_invoices_sets_initial_values(self, db):
        from app.services.batch_service import add_invoices

        user = _make_user(db, "add_test2")
        inv = _make_invoice(db, user.id, status="confirmed", amount=150.0)

        batch_resp = _make_batch(db, user.id)
        req = AddInvoicesRequest(invoice_ids=[inv.id])
        result = add_invoices(db, user.id, batch_resp.id, req)

        row = result[0]
        assert row["quantity"] == 1.0
        assert row["unit_price"] == 150.0
        assert row["advance_amount"] == 150.0

    def test_add_invoices_rejects_processing(self, db):
        from app.services.batch_service import add_invoices

        user = _make_user(db, "add_test3")
        inv = _make_invoice(db, user.id, status="processing", amount=100)

        batch_resp = _make_batch(db, user.id)
        req = AddInvoicesRequest(invoice_ids=[inv.id])

        with pytest.raises(HTTPException) as exc:
            add_invoices(db, user.id, batch_resp.id, req)
        assert exc.value.status_code == 400

    def test_add_invoices_rejects_duplicate(self, db):
        from app.services.batch_service import add_invoices

        user = _make_user(db, "add_test4")
        inv = _make_invoice(db, user.id, status="confirmed", amount=100)

        batch_resp = _make_batch(db, user.id)
        req = AddInvoicesRequest(invoice_ids=[inv.id])
        add_invoices(db, user.id, batch_resp.id, req)

        batch2_resp = _make_batch(db, user.id)
        with pytest.raises(HTTPException) as exc:
            add_invoices(db, user.id, batch2_resp.id, req)
        assert exc.value.status_code == 400

    def test_add_invoices_rollback_on_failure(self, db):
        from app.services.batch_service import add_invoices

        user = _make_user(db, "add_test5")
        inv_valid = _make_invoice(db, user.id, status="confirmed", amount=100)
        inv_invalid = _make_invoice(db, user.id, status="processing", amount=200)

        batch_resp = _make_batch(db, user.id)
        req = AddInvoicesRequest(invoice_ids=[inv_valid.id, inv_invalid.id])

        with pytest.raises(HTTPException):
            add_invoices(db, user.id, batch_resp.id, req)

        count = db.query(BatchInvoice).filter(BatchInvoice.batch_id == batch_resp.id).count()
        assert count == 0

    def test_add_invoices_updates_total_amount(self, db):
        from app.services.batch_service import add_invoices

        user = _make_user(db, "add_test6")
        inv1 = _make_invoice(db, user.id, status="confirmed", amount=100)
        inv2 = _make_invoice(db, user.id, status="confirmed", amount=200)

        batch_resp = _make_batch(db, user.id)
        req = AddInvoicesRequest(invoice_ids=[inv1.id, inv2.id])
        add_invoices(db, user.id, batch_resp.id, req)

        batch = db.query(ReimbursementBatch).filter(ReimbursementBatch.id == batch_resp.id).first()
        assert batch.total_amount == 300.0


class TestAutoRemark:
    def test_uses_existing_remark(self, db):
        from app.services.batch_service import add_invoices

        user = _make_user(db, "remark_test1")
        inv = _make_invoice(db, user.id, status="confirmed", amount=100, remark="已有备注")

        batch_resp = _make_batch(db, user.id)
        req = AddInvoicesRequest(invoice_ids=[inv.id])
        result = add_invoices(db, user.id, batch_resp.id, req)
        assert result[0]["remark"] == "已有备注"

    def test_auto_remark_train(self, db):
        from app.services.batch_service import add_invoices

        user = _make_user(db, "remark_test2")
        inv = _make_invoice(
            db, user.id, status="confirmed", amount=34,
            departure_station="合肥", arrival_station="淮南南",
        )

        batch_resp = _make_batch(db, user.id)
        req = AddInvoicesRequest(invoice_ids=[inv.id])
        result = add_invoices(db, user.id, batch_resp.id, req)
        assert result[0]["remark"] == "合肥→淮南南"

    def test_auto_remark_didi(self, db):
        from app.services.batch_service import add_invoices

        user = _make_user(db, "remark_test3")
        inv = _make_invoice(
            db, user.id, status="confirmed", amount=50,
            departure_location="A地点", arrival_location="B地点",
        )

        batch_resp = _make_batch(db, user.id)
        req = AddInvoicesRequest(invoice_ids=[inv.id])
        result = add_invoices(db, user.id, batch_resp.id, req)
        assert result[0]["remark"] == "A地点→B地点"

    def test_auto_remark_flight(self, db):
        from app.services.batch_service import add_invoices

        user = _make_user(db, "remark_test4")
        inv = _make_invoice(
            db, user.id, status="confirmed", amount=1000,
            departure_city="北京", arrival_city="上海",
        )

        batch_resp = _make_batch(db, user.id)
        req = AddInvoicesRequest(invoice_ids=[inv.id])
        result = add_invoices(db, user.id, batch_resp.id, req)
        assert result[0]["remark"] == "北京→上海"

    def test_auto_remark_priority_train_over_didi(self, db):
        from app.services.batch_service import add_invoices

        user = _make_user(db, "remark_test5")
        inv = _make_invoice(
            db, user.id, status="confirmed", amount=34,
            departure_station="合肥", arrival_station="淮南南",
            departure_location="A", arrival_location="B",
        )

        batch_resp = _make_batch(db, user.id)
        req = AddInvoicesRequest(invoice_ids=[inv.id])
        result = add_invoices(db, user.id, batch_resp.id, req)
        assert result[0]["remark"] == "合肥→淮南南"

    def test_auto_remark_empty(self, db):
        from app.services.batch_service import add_invoices

        user = _make_user(db, "remark_test6")
        inv = _make_invoice(db, user.id, status="confirmed", amount=100)

        batch_resp = _make_batch(db, user.id)
        req = AddInvoicesRequest(invoice_ids=[inv.id])
        result = add_invoices(db, user.id, batch_resp.id, req)
        assert result[0]["remark"] == ""


class TestRemoveInvoice:
    def test_remove_invoice(self, db):
        from app.services.batch_service import add_invoices, list_available_invoices, remove_invoice

        user = _make_user(db, "rm_test")
        inv = _make_invoice(db, user.id, status="confirmed", amount=100)

        batch_resp = _make_batch(db, user.id)
        req = AddInvoicesRequest(invoice_ids=[inv.id])
        add_invoices(db, user.id, batch_resp.id, req)

        result = remove_invoice(db, user.id, batch_resp.id, inv.id)
        assert result is True

        resp = list_available_invoices(db, user.id)
        assert resp.total == 1
        assert resp.items[0].id == inv.id

    def test_remove_invoice_not_in_batch(self, db):
        from app.services.batch_service import remove_invoice

        user = _make_user(db, "rm_test2")
        inv = _make_invoice(db, user.id, status="confirmed", amount=100)
        batch_resp = _make_batch(db, user.id)

        with pytest.raises(HTTPException) as exc:
            remove_invoice(db, user.id, batch_resp.id, inv.id)
        assert exc.value.status_code == 404

    def test_remove_invoice_updates_total(self, db):
        from app.services.batch_service import add_invoices, remove_invoice

        user = _make_user(db, "rm_test3")
        inv1 = _make_invoice(db, user.id, status="confirmed", amount=100)
        inv2 = _make_invoice(db, user.id, status="confirmed", amount=200)

        batch_resp = _make_batch(db, user.id)
        req = AddInvoicesRequest(invoice_ids=[inv1.id, inv2.id])
        add_invoices(db, user.id, batch_resp.id, req)

        remove_invoice(db, user.id, batch_resp.id, inv1.id)

        batch = db.query(ReimbursementBatch).filter(ReimbursementBatch.id == batch_resp.id).first()
        assert batch.total_amount == 200.0