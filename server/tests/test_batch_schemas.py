from datetime import date

import pytest
from pydantic import ValidationError


class TestBatchSchemasNewFields:
    def test_create_batch_request_has_report_date(self):
        from app.schemas.batch import CreateBatchRequest

        req = CreateBatchRequest(
            department="产教融合",
            reporter="程瑞",
            report_date=date.today(),
        )
        assert req.report_date == date.today()

    def test_create_batch_request_report_date_defaults_none(self):
        from app.schemas.batch import CreateBatchRequest

        req = CreateBatchRequest(department="产教融合", reporter="程瑞")
        assert req.report_date is None

    def test_update_batch_request_has_report_date(self):
        from app.schemas.batch import UpdateBatchRequest

        req = UpdateBatchRequest(report_date=date.today())
        assert req.report_date == date.today()


class TestAddInvoicesRequest:
    def test_add_invoices_request_accepts_ids(self):
        from app.schemas.batch import AddInvoicesRequest

        req = AddInvoicesRequest(invoice_ids=[1, 2, 3])
        assert req.invoice_ids == [1, 2, 3]

    def test_add_invoices_request_rejects_empty(self):
        from app.schemas.batch import AddInvoicesRequest

        req = AddInvoicesRequest(invoice_ids=[])
        assert req.invoice_ids == []

    def test_add_invoices_request_max_50(self):
        from app.schemas.batch import AddInvoicesRequest

        with pytest.raises(ValidationError):
            AddInvoicesRequest(invoice_ids=list(range(51)))


class TestBatchListItem:
    def test_batch_list_item_has_invoice_count(self):
        from app.schemas.batch import BatchListItem

        item = BatchListItem(
            id=1,
            department="产教融合",
            reporter="程瑞",
            total_amount=100.0,
            status="draft",
            created_at="2026-05-18T10:00:00",
            updated_at="2026-05-18T10:00:00",
            invoice_count=5,
        )
        assert item.invoice_count == 5

    def test_batch_list_item_has_report_date(self):
        from app.schemas.batch import BatchListItem

        item = BatchListItem(
            id=1,
            department="产教融合",
            reporter="程瑞",
            report_date=date.today(),
            total_amount=100.0,
            status="draft",
            created_at="2026-05-18T10:00:00",
            updated_at="2026-05-18T10:00:00",
            invoice_count=0,
        )
        assert item.report_date == date.today()


class TestBatchListResponse:
    def test_batch_list_response_holds_items(self):
        from app.schemas.batch import BatchListItem, BatchListResponse

        item = BatchListItem(
            id=1,
            department="产教融合",
            reporter="程瑞",
            total_amount=0.0,
            status="draft",
            created_at="2026-05-18T10:00:00",
            updated_at="2026-05-18T10:00:00",
            invoice_count=0,
        )
        resp = BatchListResponse(items=[item], total=1)
        assert resp.total == 1
        assert len(resp.items) == 1


class TestLedgerRowResponse:
    def test_ledger_row_has_all_fields(self):
        from app.schemas.batch import LedgerRowResponse

        row = LedgerRowResponse(
            id=1,
            invoice_id=10,
            invoice_date=date.today(),
            category="高铁票",
            amount=34.0,
            quantity=1.0,
            unit_price=34.0,
            advance_amount=34.0,
            remark="合肥→淮南南",
            invoice_no="12345",
            vendor="铁路总公司",
            is_substitute=False,
        )
        assert row.amount == 34.0
        assert row.quantity == 1.0
        assert row.unit_price == 34.0
        assert row.advance_amount == 34.0
        assert row.category == "高铁票"
        assert row.remark == "合肥→淮南南"

    def test_ledger_row_substitute_for_defaults_none(self):
        from app.schemas.batch import LedgerRowResponse

        row = LedgerRowResponse(
            id=1,
            invoice_id=10,
            invoice_date=date.today(),
            category="高铁票",
            amount=34.0,
            quantity=1.0,
            unit_price=34.0,
            advance_amount=34.0,
            remark="",
            invoice_no="",
            vendor="",
            is_substitute=False,
        )
        assert row.substitute_for is None


class TestAvailableInvoiceItem:
    def test_available_invoice_item_fields(self):
        from app.schemas.batch import AvailableInvoiceItem

        item = AvailableInvoiceItem(
            id=10,
            invoice_no="12345678",
            amount=34.0,
            invoice_date=date.today(),
            category="高铁票",
            vendor="铁路总公司",
            file_path="/uploads/1/test.pdf",
            file_original_name="高铁票.pdf",
        )
        assert item.id == 10
        assert item.file_original_name == "高铁票.pdf"


class TestAvailableInvoiceListResponse:
    def test_available_invoice_list_pagination(self):
        from app.schemas.batch import AvailableInvoiceItem, AvailableInvoiceListResponse

        items = [
            AvailableInvoiceItem(
                id=i,
                invoice_no=str(i),
                amount=10.0,
                invoice_date=date.today(),
                category="测试",
                vendor="测试",
                file_path="/tmp/test.pdf",
                file_original_name="test.pdf",
            )
            for i in range(3)
        ]
        resp = AvailableInvoiceListResponse(items=items, total=3, page=1, page_size=50)
        assert resp.total == 3
        assert resp.page == 1
        assert resp.page_size == 50


class TestUpdateBatchInvoiceRequest:
    def test_update_batch_invoice_request_accepts_quantity(self):
        from app.schemas.batch import UpdateBatchInvoiceRequest

        req = UpdateBatchInvoiceRequest(quantity=4.0)
        assert req.quantity == 4.0

    def test_update_batch_invoice_request_accepts_any_quantity(self):
        from app.schemas.batch import UpdateBatchInvoiceRequest

        req = UpdateBatchInvoiceRequest(quantity=0.5)
        assert req.quantity == 0.5

        req2 = UpdateBatchInvoiceRequest(quantity=0)
        assert req2.quantity == 0

        req3 = UpdateBatchInvoiceRequest(quantity=-1)
        assert req3.quantity == -1

    def test_update_batch_invoice_request_all_fields_optional(self):
        from app.schemas.batch import UpdateBatchInvoiceRequest

        req = UpdateBatchInvoiceRequest()
        assert req.quantity is None
        assert req.advance_amount is None
        assert req.remark is None

    def test_update_batch_invoice_request_advance_and_remark(self):
        from app.schemas.batch import UpdateBatchInvoiceRequest

        req = UpdateBatchInvoiceRequest(advance_amount=80.0, remark="出差费")
        assert req.advance_amount == 80.0
        assert req.remark == "出差费"

    def test_update_batch_invoice_request_remark_max_length(self):
        from app.schemas.batch import UpdateBatchInvoiceRequest

        long_remark = "x" * 501
        with pytest.raises(ValidationError):
            UpdateBatchInvoiceRequest(remark=long_remark)


class TestDeleteBatchResponse:
    def test_delete_batch_response(self):
        from app.schemas.batch import DeleteBatchResponse

        resp = DeleteBatchResponse(deleted=True, released_invoice_count=5)
        assert resp.deleted is True
        assert resp.released_invoice_count == 5


class TestManualRowCreateRequest:
    def test_create_manual_row_basic(self):
        from app.schemas.batch import ManualRowCreateRequest

        req = ManualRowCreateRequest(expense_item="奖金", row_amount=1000.0)
        assert req.expense_item == "奖金"
        assert req.row_amount == 1000.0
        assert req.quantity == 1.0
        assert req.advance_amount is None
        assert req.remark is None
        assert req.row_date is None

    def test_create_manual_row_requires_expense_item(self):
        from app.schemas.batch import ManualRowCreateRequest

        with pytest.raises(ValidationError):
            ManualRowCreateRequest(row_amount=1000.0)

    def test_create_manual_row_amount_must_be_positive(self):
        from app.schemas.batch import ManualRowCreateRequest

        with pytest.raises(ValidationError):
            ManualRowCreateRequest(expense_item="奖金", row_amount=0)

    def test_create_manual_row_full_fields(self):
        from app.schemas.batch import ManualRowCreateRequest

        req = ManualRowCreateRequest(
            row_date=date(2025, 12, 1),
            expense_item="团建费",
            row_amount=1000.0,
            quantity=2.0,
            advance_amount=800.0,
            remark="部门团建",
        )
        assert req.row_date == date(2025, 12, 1)
        assert req.expense_item == "团建费"
        assert req.row_amount == 1000.0
        assert req.quantity == 2.0
        assert req.advance_amount == 800.0
        assert req.remark == "部门团建"


class TestManualRowResponse:
    def test_manual_row_response_fields(self):
        from app.schemas.batch import ManualRowResponse

        row = ManualRowResponse(
            id=1,
            batch_id=1,
            source_type="manual",
            row_date=date(2025, 12, 1),
            expense_item="奖金",
            row_amount=1000.0,
            quantity=1.0,
            unit_price=1000.0,
            advance_amount=1000.0,
            remark="",
            is_substitute=False,
            substitute_for=None,
        )
        assert row.id == 1
        assert row.source_type == "manual"
        assert row.row_date == date(2025, 12, 1)
        assert row.row_amount == 1000.0
        assert row.unit_price == 1000.0

    def test_manual_row_response_substitute_for_none(self):
        from app.schemas.batch import ManualRowResponse

        row = ManualRowResponse(
            id=1,
            batch_id=1,
            source_type="manual",
            expense_item="奖金",
            row_amount=1000.0,
            quantity=1.0,
            unit_price=1000.0,
            advance_amount=1000.0,
            remark="",
            is_substitute=False,
        )
        assert row.substitute_for is None
        assert row.row_date is None


class TestManualRowUpdateRequest:
    def test_update_all_fields_optional(self):
        from app.schemas.batch import ManualRowUpdateRequest

        req = ManualRowUpdateRequest()
        assert req.row_amount is None
        assert req.quantity is None
        assert req.advance_amount is None
        assert req.remark is None
        assert req.row_date is None
        assert req.expense_item is None

    def test_update_partial_fields(self):
        from app.schemas.batch import ManualRowUpdateRequest

        req = ManualRowUpdateRequest(row_amount=1200.0, quantity=2.0)
        assert req.row_amount == 1200.0
        assert req.quantity == 2.0
        assert req.advance_amount is None


class TestManualRowDeleteResponse:
    def test_delete_response(self):
        from app.schemas.batch import ManualRowDeleteResponse

        resp = ManualRowDeleteResponse(deleted=True, released_substitute_count=2)
        assert resp.deleted is True
        assert resp.released_substitute_count == 2


class TestLedgerRowResponseExtension:
    def test_ledger_row_has_source_type(self):
        from app.schemas.batch import LedgerRowResponse

        row = LedgerRowResponse(
            id=1,
            invoice_id=10,
            source_type="invoice",
            invoice_date=date.today(),
            category="高铁票",
            amount=34.0,
            quantity=1.0,
            unit_price=34.0,
            advance_amount=34.0,
            remark="",
            invoice_no="",
            vendor="",
            is_substitute=False,
        )
        assert row.source_type == "invoice"

    def test_ledger_row_manual_with_row_amount(self):
        from app.schemas.batch import LedgerRowResponse

        row = LedgerRowResponse(
            id=1,
            invoice_id=None,
            source_type="manual",
            row_date=date(2025, 12, 1),
            row_amount=1000.0,
            expense_item="奖金",
            quantity=1.0,
            unit_price=1000.0,
            advance_amount=1000.0,
            remark="奖金（替票1011）",
            is_substitute=True,
            substitute_for="替票1011",
        )
        assert row.source_type == "manual"
        assert row.invoice_id is None
        assert row.row_amount == 1000.0
        assert row.row_date == date(2025, 12, 1)
        assert row.substitute_for == "替票1011"


class TestUserDefaultsSchema:
    def test_update_user_defaults_request(self):
        from app.schemas.user import UpdateUserDefaultsRequest

        req = UpdateUserDefaultsRequest(
            default_department="产教融合",
            default_payee="程瑞",
        )
        assert req.default_department == "产教融合"
        assert req.default_payee == "程瑞"
        assert req.default_reporter is None
        assert req.default_bank_account is None

    def test_update_user_defaults_request_all_optional(self):
        from app.schemas.user import UpdateUserDefaultsRequest

        req = UpdateUserDefaultsRequest()
        assert req.default_department is None
        assert req.default_reporter is None


class TestSubstituteCreateRequest:
    def test_one_to_one_mode(self):
        from app.schemas.batch import SubstituteCreateRequest

        req = SubstituteCreateRequest(
            mode="one_to_one",
            substitute_invoice_ids=[10],
            target_row_ids=[1],
        )
        assert req.mode == "one_to_one"
        assert req.substitute_invoice_ids == [10]
        assert req.target_row_ids == [1]

    def test_one_to_many_mode(self):
        from app.schemas.batch import SubstituteCreateRequest

        req = SubstituteCreateRequest(
            mode="one_to_many",
            substitute_invoice_ids=[10],
            target_row_ids=[1, 2, 3],
        )
        assert req.mode == "one_to_many"
        assert len(req.target_row_ids) == 3

    def test_many_to_one_mode(self):
        from app.schemas.batch import SubstituteCreateRequest

        req = SubstituteCreateRequest(
            mode="many_to_one",
            substitute_invoice_ids=[10, 20, 30],
            target_row_ids=[1],
        )
        assert req.mode == "many_to_one"
        assert len(req.substitute_invoice_ids) == 3


class TestSubstituteInvoiceItem:
    def test_remaining_amount(self):
        from app.schemas.batch import SubstituteInvoiceItem

        item = SubstituteInvoiceItem(
            id=1,
            invoice_no="12345678",
            amount=3000.0,
            invoice_date=date.today(),
            category="咨询费",
            vendor="XX公司",
            file_path="/tmp/a.pdf",
            file_original_name="a.pdf",
            used_as_substitute=1000.0,
            remaining_amount=2000.0,
        )
        assert item.amount == 3000.0
        assert item.remaining_amount == 2000.0
        assert item.used_as_substitute == 1000.0

    def test_no_prior_usage(self):
        from app.schemas.batch import SubstituteInvoiceItem

        item = SubstituteInvoiceItem(
            id=2,
            invoice_no="87654321",
            amount=500.0,
            invoice_date=date.today(),
            category="餐饮",
            vendor="YY餐厅",
            file_path="/tmp/b.pdf",
            file_original_name="b.pdf",
            used_as_substitute=0.0,
            remaining_amount=500.0,
        )
        assert item.used_as_substitute == 0.0
        assert item.remaining_amount == 500.0


class TestSubstituteRelationResponse:
    def test_full_response(self, db):
        from app.schemas.batch import (
            ManualRowResponse,
            SubstituteInvoiceItem,
            SubstituteRelationResponse,
        )

        invoice = SubstituteInvoiceItem(
            id=10,
            invoice_no="87654321",
            amount=1000.0,
            invoice_date=date.today(),
            category="交通",
            vendor="XX交通",
            file_path="/tmp/c.pdf",
            file_original_name="c.pdf",
            used_as_substitute=0.0,
            remaining_amount=1000.0,
        )
        target_row = ManualRowResponse(
            id=1,
            batch_id=1,
            source_type="manual",
            expense_item="奖金",
            row_amount=1000.0,
            quantity=1.0,
            unit_price=1000.0,
            advance_amount=1000.0,
            remark="奖金（替票87654321）",
            is_substitute=True,
            substitute_for="替票87654321",
        )
        rel = SubstituteRelationResponse(
            id=1,
            batch_id=1,
            substitute_invoice_id=10,
            target_row_id=1,
            mode="one_to_one",
            substitute_invoice=invoice,
            target_row=target_row,
        )
        assert rel.mode == "one_to_one"
        assert rel.substitute_invoice.invoice_no == "87654321"
        assert rel.target_row.expense_item == "奖金"


class TestSubstituteCreatedResponse:
    def test_created_response(self):
        from app.schemas.batch import (
            ManualRowResponse,
            SubstituteCreatedResponse,
            SubstituteInvoiceItem,
            SubstituteRelationResponse,
        )

        invoice = SubstituteInvoiceItem(
            id=10,
            invoice_no="12345678",
            amount=1000.0,
            invoice_date=date.today(),
            category="交通",
            vendor="XX交通",
            file_path="/tmp/c.pdf",
            file_original_name="c.pdf",
            used_as_substitute=0.0,
            remaining_amount=1000.0,
        )
        target = ManualRowResponse(
            id=1,
            batch_id=1,
            source_type="manual",
            expense_item="奖金",
            row_amount=1000.0,
            quantity=1.0,
            unit_price=1000.0,
            advance_amount=1000.0,
            remark="奖金（替票12345678）",
            is_substitute=True,
            substitute_for="替票12345678",
        )
        rel = SubstituteRelationResponse(
            id=1,
            batch_id=1,
            substitute_invoice_id=10,
            target_row_id=1,
            mode="one_to_one",
            substitute_invoice=invoice,
            target_row=target,
        )

        resp = SubstituteCreatedResponse(
            relations=[rel],
            updated_target_rows=[target],
        )
        assert len(resp.relations) == 1
        assert len(resp.updated_target_rows) == 1