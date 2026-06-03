from datetime import date

from app.models.batch import BatchInvoice, ReimbursementBatch
from app.models.user import User


class TestUserModelDefaults:
    def test_default_fields_exist_and_nullable(self, db):
        user = User(
            username="test_defaults",
            password_hash="hash",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        assert hasattr(user, "default_department")
        assert user.default_department is None
        assert hasattr(user, "default_reporter")
        assert user.default_reporter is None
        assert hasattr(user, "default_payee")
        assert user.default_payee is None
        assert hasattr(user, "default_bank_account")
        assert user.default_bank_account is None
        assert hasattr(user, "default_bank_name")
        assert user.default_bank_name is None

    def test_default_fields_writable(self, db):
        user = User(
            username="test_write",
            password_hash="hash",
            default_department="产教融合",
            default_reporter="程瑞",
            default_payee="程瑞",
            default_bank_account="6222000000000000",
            default_bank_name="中国工商银行",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        assert user.default_department == "产教融合"
        assert user.default_reporter == "程瑞"
        assert user.default_payee == "程瑞"
        assert user.default_bank_account == "6222000000000000"
        assert user.default_bank_name == "中国工商银行"


class TestReimbursementBatchReportDate:
    def test_report_date_field_exists_and_nullable(self, db):
        batch = ReimbursementBatch(
            user_id=1,
            department="测试部门",
            reporter="测试人",
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        assert hasattr(batch, "report_date")
        assert batch.report_date is None

    def test_report_date_writable(self, db):
        batch = ReimbursementBatch(
            user_id=1,
            department="测试部门",
            reporter="测试人",
            report_date=date.today(),
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        assert batch.report_date == date.today()


class TestBatchInvoiceNewFields:
    def test_quantity_default_value(self, db):
        bi = BatchInvoice(
            batch_id=1,
            invoice_id=1,
        )
        db.add(bi)
        db.commit()
        db.refresh(bi)
        assert hasattr(bi, "quantity")
        assert bi.quantity == 1.0

    def test_unit_price_default_value(self, db):
        bi = BatchInvoice(
            batch_id=1,
            invoice_id=1,
        )
        db.add(bi)
        db.commit()
        db.refresh(bi)
        assert hasattr(bi, "unit_price")
        assert bi.unit_price == 0.0

    def test_advance_amount_default_value(self, db):
        bi = BatchInvoice(
            batch_id=1,
            invoice_id=1,
        )
        db.add(bi)
        db.commit()
        db.refresh(bi)
        assert hasattr(bi, "advance_amount")
        assert bi.advance_amount == 0.0

    def test_new_fields_writable(self, db):
        bi = BatchInvoice(
            batch_id=1,
            invoice_id=1,
            quantity=3.0,
            unit_price=50.0,
            advance_amount=150.0,
        )
        db.add(bi)
        db.commit()
        db.refresh(bi)
        assert bi.quantity == 3.0
        assert bi.unit_price == 50.0
        assert bi.advance_amount == 150.0


class TestBatchInvoiceManualRow:
    def test_invoice_id_nullable(self, db):
        bi = BatchInvoice(
            batch_id=1,
        )
        db.add(bi)
        db.commit()
        db.refresh(bi)
        assert bi.invoice_id is None

    def test_source_type_default_value(self, db):
        bi = BatchInvoice(
            batch_id=1,
            invoice_id=1,
        )
        db.add(bi)
        db.commit()
        db.refresh(bi)
        assert hasattr(bi, "source_type")
        assert bi.source_type == "invoice"

    def test_manual_row_creation(self, db):
        from datetime import date
        bi = BatchInvoice(
            batch_id=1,
            source_type="manual",
            row_date=date(2025, 12, 1),
            row_amount=1000.0,
        )
        db.add(bi)
        db.commit()
        db.refresh(bi)
        assert bi.source_type == "manual"
        assert bi.invoice_id is None
        assert bi.row_date == date(2025, 12, 1)
        assert bi.row_amount == 1000.0

    def test_row_date_nullable(self, db):
        bi = BatchInvoice(
            batch_id=1,
            source_type="manual",
            row_amount=500.0,
        )
        db.add(bi)
        db.commit()
        db.refresh(bi)
        assert bi.row_date is None

    def test_row_amount_nullable(self, db):
        bi = BatchInvoice(
            batch_id=1,
            invoice_id=1,
            source_type="invoice",
        )
        db.add(bi)
        db.commit()
        db.refresh(bi)
        assert bi.row_amount is None