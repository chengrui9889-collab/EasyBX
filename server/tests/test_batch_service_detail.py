from datetime import date

import pytest
from fastapi import HTTPException

from app.schemas.batch import AddInvoicesRequest, SubstituteCreateRequest


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


def _make_manual_row(db, batch_id, expense_item, row_amount):
    from app.models.batch import BatchInvoice
    row = BatchInvoice(
        batch_id=batch_id,
        source_type="manual",
        expense_item=expense_item,
        row_amount=row_amount,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _make_substitution(db, batch_id, sub_invoice_id, target_row_id, mode="one_to_one"):
    from app.models.substitute import SubstituteRelation
    rel = SubstituteRelation(
        batch_id=batch_id,
        substitute_invoice_id=sub_invoice_id,
        target_row_id=target_row_id,
        mode=mode,
    )
    db.add(rel)
    db.commit()
    db.refresh(rel)
    return rel


def _create_substitute_placeholder(db, batch_id, invoice_id):
    from app.models.batch import BatchInvoice
    placeholder = BatchInvoice(
        batch_id=batch_id,
        invoice_id=invoice_id,
        source_type="invoice",
        is_substitute=True,
    )
    db.add(placeholder)
    db.commit()
    db.refresh(placeholder)
    return placeholder


class TestGetBatchDetail:
    def test_returns_batch_info(self, db):
        user = _make_user(db, "detail1")
        batch = _make_batch(db, user.id, "研发部", "张三")

        from app.services.batch_service import get_batch_detail
        result = get_batch_detail(db, user.id, batch.id)

        assert result.department == "研发部"
        assert result.reporter == "张三"
        assert result.ledger_rows == []

    def test_with_invoices(self, db):
        user = _make_user(db, "detail2")
        inv = _make_invoice(db, user.id, status="confirmed", amount=34.0,
                            invoice_date=date(2026, 5, 15), category="交通")
        batch = _make_batch(db, user.id)

        from app.services.batch_service import add_invoices, get_batch_detail
        add_invoices(db, user.id, batch.id, AddInvoicesRequest(invoice_ids=[inv.id]))

        result = get_batch_detail(db, user.id, batch.id)
        assert len(result.ledger_rows) == 1
        row = result.ledger_rows[0]
        assert row.invoice_date == date(2026, 5, 15)
        assert row.amount == 34.0
        assert row.quantity == 1.0
        assert row.unit_price == 34.0
        assert row.category == "交通"

    def test_empty_invoices(self, db):
        user = _make_user(db, "detail3")
        batch = _make_batch(db, user.id)

        from app.services.batch_service import get_batch_detail
        result = get_batch_detail(db, user.id, batch.id)

        assert result.ledger_rows == []

    def test_batch_not_found(self, db):
        user = _make_user(db, "detail4")

        from app.services.batch_service import get_batch_detail
        with pytest.raises(HTTPException) as exc:
            get_batch_detail(db, user.id, 99999)
        assert exc.value.status_code == 404

    def test_wrong_user(self, db):
        user1 = _make_user(db, "detail5a")
        user2 = _make_user(db, "detail5b")
        batch = _make_batch(db, user1.id)

        from app.services.batch_service import get_batch_detail
        with pytest.raises(HTTPException) as exc:
            get_batch_detail(db, user2.id, batch.id)
        assert exc.value.status_code == 404

    def test_filters_out_substitute_placeholders(self, db):
        user = _make_user(db, "detail6")
        batch = _make_batch(db, user.id)
        inv1 = _make_invoice(db, user.id, status="confirmed", amount=500.0, invoice_no="INV001")
        inv2 = _make_invoice(db, user.id, status="confirmed", amount=300.0, invoice_no="SUBINV")

        from app.services.batch_service import add_invoices, get_batch_detail
        add_invoices(db, user.id, batch.id, AddInvoicesRequest(invoice_ids=[inv1.id]))

        _create_substitute_placeholder(db, batch.id, inv2.id)

        result = get_batch_detail(db, user.id, batch.id)

        assert len(result.ledger_rows) == 1
        assert result.ledger_rows[0].invoice_no == "INV001"

    def test_manual_substituted_row_still_visible(self, db):
        user = _make_user(db, "detail7")
        batch = _make_batch(db, user.id)
        sub_inv = _make_invoice(db, user.id, status="confirmed", amount=500.0, invoice_no="SUB001")

        row = _make_manual_row(db, batch.id, "奖金", 500.0)
        _make_substitution(db, batch.id, sub_inv.id, row.id)
        _create_substitute_placeholder(db, batch.id, sub_inv.id)

        from app.models.batch import BatchInvoice
        row.is_substitute = True
        row.substitute_for = "替票SUB001"
        db.commit()

        from app.services.batch_service import get_batch_detail
        result = get_batch_detail(db, user.id, batch.id)

        assert len(result.ledger_rows) == 1
        assert result.ledger_rows[0].expense_item == "奖金"
        assert result.ledger_rows[0].is_substitute is True
        assert result.ledger_rows[0].substitute_for == "替票SUB001"