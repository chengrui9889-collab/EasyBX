from datetime import date

import pytest
from fastapi import HTTPException

from app.models.batch import BatchInvoice, ReimbursementBatch
from app.models.user import User
from app.schemas.batch import ManualRowCreateRequest, ManualRowUpdateRequest


def _create_test_batch(db, user_id):
    batch = ReimbursementBatch(
        user_id=user_id,
        department="测试部门",
        reporter="测试人",
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


class TestAddManualRow:
    def test_add_manual_row_basic(self, db):
        from app.services.batch_service import add_manual_row

        user = User(username="mr_test1", password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)
        batch = _create_test_batch(db, user.id)

        req = ManualRowCreateRequest(expense_item="奖金", row_amount=1000.0)
        row = add_manual_row(db, user.id, batch.id, req)

        assert row.id is not None
        assert row.source_type == "manual"
        assert row.expense_item == "奖金"
        assert row.row_amount == 1000.0
        assert row.quantity == 1.0
        assert row.unit_price == 1000.0
        assert row.advance_amount == 1000.0
        assert row.is_substitute is False

        bi = db.query(BatchInvoice).filter(BatchInvoice.id == row.id).first()
        assert bi is not None
        assert bi.invoice_id is None

    def test_add_manual_row_calculates_unit_price(self, db):
        from app.services.batch_service import add_manual_row

        user = User(username="mr_test2", password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)
        batch = _create_test_batch(db, user.id)

        req = ManualRowCreateRequest(expense_item="团建", row_amount=1000.0, quantity=4.0)
        row = add_manual_row(db, user.id, batch.id, req)

        assert row.unit_price == 250.0

    def test_add_manual_row_advance_amount_defaults_to_row_amount(self, db):
        from app.services.batch_service import add_manual_row

        user = User(username="mr_test3", password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)
        batch = _create_test_batch(db, user.id)

        req = ManualRowCreateRequest(expense_item="奖金", row_amount=1000.0)
        row = add_manual_row(db, user.id, batch.id, req)

        assert row.advance_amount == 1000.0

    def test_add_manual_row_explicit_advance_amount(self, db):
        from app.services.batch_service import add_manual_row

        user = User(username="mr_test4", password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)
        batch = _create_test_batch(db, user.id)

        req = ManualRowCreateRequest(expense_item="奖金", row_amount=1000.0, advance_amount=800.0)
        row = add_manual_row(db, user.id, batch.id, req)

        assert row.advance_amount == 800.0

    def test_add_manual_row_date_defaults_today(self, db):
        from app.services.batch_service import add_manual_row

        user = User(username="mr_test5", password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)
        batch = _create_test_batch(db, user.id)

        req = ManualRowCreateRequest(expense_item="奖金", row_amount=1000.0)
        row = add_manual_row(db, user.id, batch.id, req)

        assert row.row_date == date.today()

    def test_add_manual_row_explicit_date(self, db):
        from app.services.batch_service import add_manual_row

        user = User(username="mr_test6", password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)
        batch = _create_test_batch(db, user.id)

        req = ManualRowCreateRequest(
            row_date=date(2025, 12, 1),
            expense_item="奖金",
            row_amount=1000.0,
        )
        row = add_manual_row(db, user.id, batch.id, req)

        assert row.row_date == date(2025, 12, 1)

    def test_add_manual_row_remark(self, db):
        from app.services.batch_service import add_manual_row

        user = User(username="mr_test7", password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)
        batch = _create_test_batch(db, user.id)

        req = ManualRowCreateRequest(expense_item="奖金", row_amount=1000.0, remark="测试备注")
        row = add_manual_row(db, user.id, batch.id, req)

        assert row.remark == "测试备注"

    def test_add_manual_row_amount_zero_raises_400(self, db):
        from pydantic import ValidationError

        user = User(username="mr_test8", password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)
        batch = _create_test_batch(db, user.id)

        with pytest.raises(ValidationError):
            ManualRowCreateRequest(expense_item="奖金", row_amount=0)

    def test_add_manual_row_batch_not_found(self, db):
        from app.services.batch_service import add_manual_row

        user = User(username="mr_test9", password_hash="hash")
        db.add(user)
        db.commit()

        with pytest.raises(HTTPException) as exc:
            add_manual_row(db, user.id, 999, ManualRowCreateRequest(expense_item="奖金", row_amount=1000.0))
        assert exc.value.status_code == 404

    def test_add_manual_row_batch_wrong_user(self, db):
        from app.services.batch_service import add_manual_row

        user_a = User(username="mr_a", password_hash="hash")
        user_b = User(username="mr_b", password_hash="hash")
        db.add_all([user_a, user_b])
        db.commit()
        db.refresh(user_a)
        batch = _create_test_batch(db, user_a.id)

        with pytest.raises(HTTPException) as exc:
            add_manual_row(db, user_b.id, batch.id, ManualRowCreateRequest(expense_item="奖金", row_amount=1000.0))
        assert exc.value.status_code == 404


class TestUpdateManualRow:
    def test_update_manual_row_amount_recalculates_unit_price(self, db):
        from app.services.batch_service import add_manual_row, update_manual_row

        user = User(username="mu_test1", password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)
        batch = _create_test_batch(db, user.id)

        row = add_manual_row(db, user.id, batch.id, ManualRowCreateRequest(expense_item="奖金", row_amount=1000.0))

        req = ManualRowUpdateRequest(row_amount=1200.0)
        updated = update_manual_row(db, user.id, batch.id, row.id, req)
        assert updated.row_amount == 1200.0
        assert updated.unit_price == 1200.0

    def test_update_manual_row_quantity_recalculates_unit_price(self, db):
        from app.services.batch_service import add_manual_row, update_manual_row

        user = User(username="mu_test2", password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)
        batch = _create_test_batch(db, user.id)

        row = add_manual_row(db, user.id, batch.id, ManualRowCreateRequest(expense_item="奖金", row_amount=1000.0))

        req = ManualRowUpdateRequest(quantity=4.0)
        updated = update_manual_row(db, user.id, batch.id, row.id, req)
        assert updated.quantity == 4.0
        assert updated.unit_price == 250.0

    def test_update_manual_row_advance_amount_does_not_affect_unit_price(self, db):
        from app.services.batch_service import add_manual_row, update_manual_row

        user = User(username="mu_test3", password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)
        batch = _create_test_batch(db, user.id)

        row = add_manual_row(db, user.id, batch.id, ManualRowCreateRequest(expense_item="奖金", row_amount=1000.0))

        req = ManualRowUpdateRequest(advance_amount=800.0)
        updated = update_manual_row(db, user.id, batch.id, row.id, req)
        assert updated.advance_amount == 800.0
        assert updated.unit_price == 1000.0

    def test_update_manual_row_remark(self, db):
        from app.services.batch_service import add_manual_row, update_manual_row

        user = User(username="mu_test4", password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)
        batch = _create_test_batch(db, user.id)

        row = add_manual_row(db, user.id, batch.id, ManualRowCreateRequest(expense_item="奖金", row_amount=1000.0))

        req = ManualRowUpdateRequest(remark="新备注")
        updated = update_manual_row(db, user.id, batch.id, row.id, req)
        assert updated.remark == "新备注"

    def test_update_manual_row_cannot_update_invoice_row(self, db):
        from app.services.batch_service import update_manual_row

        user = User(username="mu_test5", password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)
        batch = _create_test_batch(db, user.id)

        from app.models.invoice import Invoice
        invoice = Invoice(
            user_id=user.id,
            file_path="/tmp/test.pdf",
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        bi = BatchInvoice(
            batch_id=batch.id,
            invoice_id=invoice.id,
        )
        db.add(bi)
        db.commit()
        db.refresh(bi)

        req = ManualRowUpdateRequest(row_amount=999.0)
        with pytest.raises(HTTPException) as exc:
            update_manual_row(db, user.id, batch.id, bi.id, req)
        assert exc.value.status_code == 400
        assert "手动" in exc.value.detail

    def test_update_manual_row_not_found(self, db):
        from app.services.batch_service import update_manual_row

        user = User(username="mu_test6", password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)
        batch = _create_test_batch(db, user.id)

        req = ManualRowUpdateRequest(row_amount=999.0)
        with pytest.raises(HTTPException) as exc:
            update_manual_row(db, user.id, batch.id, 9999, req)
        assert exc.value.status_code == 404


class TestDeleteManualRow:
    def test_delete_manual_row_success(self, db):
        from app.services.batch_service import add_manual_row, delete_manual_row

        user = User(username="md_test1", password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)
        batch = _create_test_batch(db, user.id)

        row = add_manual_row(db, user.id, batch.id, ManualRowCreateRequest(expense_item="奖金", row_amount=1000.0))

        result = delete_manual_row(db, user.id, batch.id, row.id)
        assert result.deleted is True
        assert result.released_substitute_count == 0

        deleted = db.query(BatchInvoice).filter(BatchInvoice.id == row.id).first()
        assert deleted is None

    def test_delete_manual_row_no_effect_on_invoices_table(self, db):
        from app.services.batch_service import add_manual_row, delete_manual_row

        user = User(username="md_test2", password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)
        batch = _create_test_batch(db, user.id)

        from app.models.invoice import Invoice
        invoice_before_count = db.query(Invoice).count()

        row = add_manual_row(db, user.id, batch.id, ManualRowCreateRequest(expense_item="奖金", row_amount=1000.0))
        delete_manual_row(db, user.id, batch.id, row.id)

        invoice_after_count = db.query(Invoice).count()
        assert invoice_before_count == invoice_after_count

    def test_delete_manual_row_cannot_delete_invoice_row(self, db):
        from app.services.batch_service import delete_manual_row

        user = User(username="md_test3", password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)
        batch = _create_test_batch(db, user.id)

        from app.models.invoice import Invoice
        invoice = Invoice(
            user_id=user.id,
            file_path="/tmp/test.pdf",
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        bi = BatchInvoice(
            batch_id=batch.id,
            invoice_id=invoice.id,
        )
        db.add(bi)
        db.commit()
        db.refresh(bi)

        with pytest.raises(HTTPException) as exc:
            delete_manual_row(db, user.id, batch.id, bi.id)
        assert exc.value.status_code == 400

    def test_delete_manual_row_not_found(self, db):
        from app.services.batch_service import delete_manual_row

        user = User(username="md_test4", password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)
        batch = _create_test_batch(db, user.id)

        with pytest.raises(HTTPException) as exc:
            delete_manual_row(db, user.id, batch.id, 9999)
        assert exc.value.status_code == 404