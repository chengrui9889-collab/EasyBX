import pytest
from fastapi import HTTPException

from app.schemas.batch import AddInvoicesRequest, UpdateBatchInvoiceRequest


def _make_user(db, username):
    from app.models.user import User
    user = User(username=username, password_hash="hash")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_invoice(db, user_id, status="confirmed", amount=100.0, **kwargs):
    from app.models.invoice import Invoice
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


def _add_invoice_to_batch(db, user_id, batch_id, invoice_id):
    from app.services.batch_service import add_invoices
    return add_invoices(db, user_id, batch_id, AddInvoicesRequest(invoice_ids=[invoice_id]))


class TestUpdateBatchInvoiceQuantity:
    def test_update_quantity_recalculates_unit_price(self, db):
        from app.services.batch_service import update_batch_invoice

        user = _make_user(db, "update_q1")
        inv = _make_invoice(db, user.id, status="confirmed", amount=100.0)
        batch = _make_batch(db, user.id)
        _add_invoice_to_batch(db, user.id, batch.id, inv.id)

        result = update_batch_invoice(
            db, user.id, batch.id, inv.id,
            UpdateBatchInvoiceRequest(quantity=4),
        )
        assert result["quantity"] == 4.0
        assert result["unit_price"] == 25.0

    def test_update_quantity_round_to_two_decimals(self, db):
        from app.services.batch_service import update_batch_invoice

        user = _make_user(db, "update_q2")
        inv = _make_invoice(db, user.id, status="confirmed", amount=37.0)
        batch = _make_batch(db, user.id)
        _add_invoice_to_batch(db, user.id, batch.id, inv.id)

        result = update_batch_invoice(
            db, user.id, batch.id, inv.id,
            UpdateBatchInvoiceRequest(quantity=2),
        )
        assert result["quantity"] == 2.0
        assert result["unit_price"] == 18.5

    def test_update_quantity_zero_returns_400(self, db):
        from app.services.batch_service import update_batch_invoice

        user = _make_user(db, "update_q3")
        inv = _make_invoice(db, user.id, status="confirmed", amount=100.0)
        batch = _make_batch(db, user.id)
        _add_invoice_to_batch(db, user.id, batch.id, inv.id)

        with pytest.raises(HTTPException) as exc:
            update_batch_invoice(
                db, user.id, batch.id, inv.id,
                UpdateBatchInvoiceRequest(quantity=0),
            )
        assert exc.value.status_code == 400

    def test_update_quantity_negative_returns_400(self, db):
        from app.services.batch_service import update_batch_invoice

        user = _make_user(db, "update_q4")
        inv = _make_invoice(db, user.id, status="confirmed", amount=100.0)
        batch = _make_batch(db, user.id)
        _add_invoice_to_batch(db, user.id, batch.id, inv.id)

        with pytest.raises(HTTPException) as exc:
            update_batch_invoice(
                db, user.id, batch.id, inv.id,
                UpdateBatchInvoiceRequest(quantity=-1),
            )
        assert exc.value.status_code == 400

    def test_amount_unchanged_after_quantity_update(self, db):
        from app.services.batch_service import update_batch_invoice

        user = _make_user(db, "update_q5")
        inv = _make_invoice(db, user.id, status="confirmed", amount=100.0)
        batch = _make_batch(db, user.id)
        _add_invoice_to_batch(db, user.id, batch.id, inv.id)

        update_batch_invoice(
            db, user.id, batch.id, inv.id,
            UpdateBatchInvoiceRequest(quantity=5),
        )

        from app.models.invoice import Invoice
        refreshed = db.query(Invoice).filter(Invoice.id == inv.id).first()
        assert refreshed.amount == 100.0


class TestUpdateBatchInvoiceAdvanceAmount:
    def test_update_advance_amount(self, db):
        from app.services.batch_service import update_batch_invoice

        user = _make_user(db, "update_aa1")
        inv = _make_invoice(db, user.id, status="confirmed", amount=100.0)
        batch = _make_batch(db, user.id)
        _add_invoice_to_batch(db, user.id, batch.id, inv.id)

        result = update_batch_invoice(
            db, user.id, batch.id, inv.id,
            UpdateBatchInvoiceRequest(advance_amount=80.0),
        )
        assert result["advance_amount"] == 80.0
        assert result["unit_price"] == 100.0

    def test_advance_amount_persists_after_quantity_change(self, db):
        from app.services.batch_service import update_batch_invoice

        user = _make_user(db, "update_aa2")
        inv = _make_invoice(db, user.id, status="confirmed", amount=100.0)
        batch = _make_batch(db, user.id)
        _add_invoice_to_batch(db, user.id, batch.id, inv.id)

        update_batch_invoice(
            db, user.id, batch.id, inv.id,
            UpdateBatchInvoiceRequest(advance_amount=80.0),
        )
        result = update_batch_invoice(
            db, user.id, batch.id, inv.id,
            UpdateBatchInvoiceRequest(quantity=5),
        )
        assert result["advance_amount"] == 80.0


class TestUpdateBatchInvoiceRemark:
    def test_update_remark(self, db):
        from app.services.batch_service import update_batch_invoice

        user = _make_user(db, "update_rm1")
        inv = _make_invoice(db, user.id, status="confirmed", amount=100.0)
        batch = _make_batch(db, user.id)
        _add_invoice_to_batch(db, user.id, batch.id, inv.id)

        result = update_batch_invoice(
            db, user.id, batch.id, inv.id,
            UpdateBatchInvoiceRequest(remark="出差交通费"),
        )
        assert result["remark"] == "出差交通费"

    def test_original_invoice_remark_unchanged(self, db):
        from app.services.batch_service import update_batch_invoice

        user = _make_user(db, "update_rm2")
        inv = _make_invoice(db, user.id, status="confirmed", amount=100.0, remark="原始备注")
        batch = _make_batch(db, user.id)
        _add_invoice_to_batch(db, user.id, batch.id, inv.id)

        update_batch_invoice(
            db, user.id, batch.id, inv.id,
            UpdateBatchInvoiceRequest(remark="台账备注"),
        )

        from app.models.invoice import Invoice
        refreshed = db.query(Invoice).filter(Invoice.id == inv.id).first()
        assert refreshed.remark == "原始备注"


class TestUpdateBatchInvoiceErrors:
    def test_batch_not_found(self, db):
        from app.services.batch_service import update_batch_invoice

        user = _make_user(db, "update_err1")
        with pytest.raises(HTTPException) as exc:
            update_batch_invoice(
                db, user.id, 99999, 1,
                UpdateBatchInvoiceRequest(quantity=2),
            )
        assert exc.value.status_code == 404

    def test_invoice_not_in_batch(self, db):
        from app.services.batch_service import update_batch_invoice

        user = _make_user(db, "update_err2")
        batch = _make_batch(db, user.id)

        with pytest.raises(HTTPException) as exc:
            update_batch_invoice(
                db, user.id, batch.id, 99999,
                UpdateBatchInvoiceRequest(quantity=2),
            )
        assert exc.value.status_code == 404

    def test_original_invoice_amount_unchanged(self, db):
        from app.services.batch_service import update_batch_invoice

        user = _make_user(db, "update_err3")
        inv = _make_invoice(db, user.id, status="confirmed", amount=100.0)
        batch = _make_batch(db, user.id)
        _add_invoice_to_batch(db, user.id, batch.id, inv.id)

        update_batch_invoice(
            db, user.id, batch.id, inv.id,
            UpdateBatchInvoiceRequest(quantity=4),
        )

        from app.models.invoice import Invoice
        refreshed = db.query(Invoice).filter(Invoice.id == inv.id).first()
        assert refreshed.amount == 100.0
        assert refreshed.remark is None