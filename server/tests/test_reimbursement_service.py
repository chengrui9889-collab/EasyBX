from datetime import date

import pytest
from fastapi import HTTPException

from app.models.batch import BatchInvoice, ReimbursementBatch
from app.models.invoice import Invoice


class TestAmountToChinese:
    def test_integer_amount(self):
        from app.services.reimbursement_service import amount_to_chinese

        assert amount_to_chinese(468.00) == "肆佰陆拾捌元整"

    def test_zero_amount(self):
        from app.services.reimbursement_service import amount_to_chinese

        assert amount_to_chinese(0.00) == "零元整"

    def test_amount_with_jiao(self):
        from app.services.reimbursement_service import amount_to_chinese

        assert amount_to_chinese(100.50) == "壹佰元伍角整"

    def test_amount_with_fen(self):
        from app.services.reimbursement_service import amount_to_chinese

        assert amount_to_chinese(0.03) == "零元叁分"

    def test_amount_with_jiao_only(self):
        from app.services.reimbursement_service import amount_to_chinese

        assert amount_to_chinese(0.30) == "零元叁角整"

    def test_thousand_amount(self):
        from app.services.reimbursement_service import amount_to_chinese

        assert amount_to_chinese(1000.00) == "壹仟元整"

    def test_ten_thousand_with_zero(self):
        from app.services.reimbursement_service import amount_to_chinese

        assert amount_to_chinese(10001.00) == "壹万零壹元整"

    def test_million_amount(self):
        from app.services.reimbursement_service import amount_to_chinese

        assert amount_to_chinese(1234567.89) == "壹佰贰拾叁万肆仟伍佰陆拾柒元捌角玖分"


class TestGetReimbursementPreview:
    @pytest.fixture
    def batch_with_invoices(self, db, test_user):
        batch = ReimbursementBatch(
            user_id=test_user.id,
            department="产教融合",
            reporter="程瑞",
            report_date=date(2025, 12, 20),
            status="draft",
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)

        inv1 = Invoice(
            user_id=test_user.id,
            amount=34.00,
            category="交通费",
            file_path="/fake/path1.jpg",
            status="confirmed",
        )
        inv2 = Invoice(
            user_id=test_user.id,
            amount=56.00,
            category="交通费",
            file_path="/fake/path2.jpg",
            status="confirmed",
        )
        inv3 = Invoice(
            user_id=test_user.id,
            amount=78.00,
            category="交通费",
            file_path="/fake/path3.jpg",
            status="confirmed",
        )
        inv4 = Invoice(
            user_id=test_user.id,
            amount=100.00,
            category="餐饮费",
            file_path="/fake/path4.jpg",
            status="confirmed",
        )
        inv5 = Invoice(
            user_id=test_user.id,
            amount=200.00,
            category="餐饮费",
            file_path="/fake/path5.jpg",
            status="confirmed",
        )
        db.add_all([inv1, inv2, inv3, inv4, inv5])
        db.commit()
        for inv in [inv1, inv2, inv3, inv4, inv5]:
            db.refresh(inv)

        for inv in [inv1, inv2, inv3, inv4, inv5]:
            bi = BatchInvoice(
                batch_id=batch.id,
                invoice_id=inv.id,
                source_type="invoice",
            )
            db.add(bi)
        db.commit()

        return batch

    def test_groups_by_category(self, db, test_user, batch_with_invoices):
        from app.services.reimbursement_service import get_reimbursement_preview

        result = get_reimbursement_preview(db, test_user.id, batch_with_invoices.id)

        assert result.department == "产教融合"
        assert result.reporter == "程瑞"
        assert result.total_amount == 468.00
        assert result.total_amount_cn == "肆佰陆拾捌元整"

        items = result.items
        assert len(items) == 2

        item_dict = {i.expense_item: i.amount for i in items}
        assert item_dict["交通费"] == 168.00
        assert item_dict["餐饮费"] == 300.00

    def test_manual_rows_merge_with_invoice_rows(self, db, test_user, batch_with_invoices):
        from app.services.reimbursement_service import get_reimbursement_preview

        bi_manual = BatchInvoice(
            batch_id=batch_with_invoices.id,
            invoice_id=None,
            source_type="manual",
            expense_item="交通费",
            row_amount=50.00,
            quantity=1.0,
            unit_price=50.00,
            advance_amount=50.00,
        )
        db.add(bi_manual)
        db.commit()

        result = get_reimbursement_preview(db, test_user.id, batch_with_invoices.id)

        item_dict = {i.expense_item: i.amount for i in result.items}
        assert item_dict["交通费"] == 218.00
        assert item_dict["餐饮费"] == 300.00

    def test_batch_not_found(self, db, test_user):
        from app.services.reimbursement_service import get_reimbursement_preview

        with pytest.raises(HTTPException) as exc:
            get_reimbursement_preview(db, test_user.id, 99999)
        assert exc.value.status_code == 404

    def test_other_user_batch(self, db):
        from app.services.reimbursement_service import get_reimbursement_preview

        batch = ReimbursementBatch(
            user_id=999, department="其他", reporter="某人", status="draft"
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)

        with pytest.raises(HTTPException) as exc:
            get_reimbursement_preview(db, 1, batch.id)
        assert exc.value.status_code == 404

    def test_empty_batch_returns_400(self, db, test_user):
        from app.services.reimbursement_service import get_reimbursement_preview

        batch = ReimbursementBatch(
            user_id=test_user.id, department="空", reporter="空", status="draft"
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)

        with pytest.raises(HTTPException) as exc:
            get_reimbursement_preview(db, test_user.id, batch.id)
        assert exc.value.status_code == 400

    def test_invoice_with_none_category(self, db, test_user):
        from app.services.reimbursement_service import get_reimbursement_preview

        batch = ReimbursementBatch(
            user_id=test_user.id, department="测试", reporter="测试", status="draft"
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)

        inv = Invoice(
            user_id=test_user.id, amount=100.00, category=None,
            file_path="/fake.jpg", status="confirmed",
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)

        bi = BatchInvoice(batch_id=batch.id, invoice_id=inv.id, source_type="invoice")
        db.add(bi)
        db.commit()

        result = get_reimbursement_preview(db, test_user.id, batch.id)
        assert len(result.items) == 1
        assert result.items[0].expense_item == "其他"
        assert result.items[0].amount == 100.00

    def test_manual_row_none_expense_item(self, db, test_user):
        from app.services.reimbursement_service import get_reimbursement_preview

        batch = ReimbursementBatch(
            user_id=test_user.id, department="测试", reporter="测试", status="draft"
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)

        bi = BatchInvoice(
            batch_id=batch.id, invoice_id=None, source_type="manual",
            expense_item=None, row_amount=50.00, quantity=1.0, unit_price=50.00,
        )
        db.add(bi)
        db.commit()

        result = get_reimbursement_preview(db, test_user.id, batch.id)
        assert len(result.items) == 1
        assert result.items[0].expense_item == "其他"
        assert result.items[0].amount == 50.00