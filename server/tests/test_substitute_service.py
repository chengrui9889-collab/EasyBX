import pytest
from fastapi import HTTPException


class _Helpers:
    @staticmethod
    def _create_user(db, username):
        from app.models.user import User

        user = User(username=username, password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def _create_batch(db, user_id, department="测试部"):
        from app.models.batch import ReimbursementBatch

        batch = ReimbursementBatch(
            user_id=user_id,
            department=department,
            reporter="测试人",
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        return batch

    @staticmethod
    def _create_confirmed_invoice(db, user_id, amount=500.0, vendor="测试公司"):
        from app.models.invoice import Invoice

        import uuid
        invoice = Invoice(
            user_id=user_id,
            file_path="/tmp/test.pdf",
            status="confirmed",
            amount=amount,
            vendor=vendor,
            invoice_no=str(uuid.uuid4())[:8],
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def _add_invoice_to_batch(db, batch_id, invoice_id):
        from app.models.batch import BatchInvoice

        bi = BatchInvoice(
            batch_id=batch_id,
            invoice_id=invoice_id,
        )
        db.add(bi)
        db.commit()


class TestListSubstituteInvoices:
    def test_returns_only_confirmed_invoices(self, db):
        from app.services.substitute_service import list_substitute_invoices
        from app.models.invoice import Invoice

        user = _Helpers._create_user(db, "si_test1")

        conf = _Helpers._create_confirmed_invoice(db, user.id, amount=500.0)
        pending = Invoice(
            user_id=user.id,
            file_path="/tmp/pending.pdf",
            status="processing",
            amount=300.0,
        )
        db.add(pending)
        db.commit()

        batch = _Helpers._create_batch(db, user.id)

        result = list_substitute_invoices(db, user.id, batch.id)
        confirmed_ids = {item.id for item in result.items}
        assert conf.id in confirmed_ids
        assert pending.id not in confirmed_ids

    def test_excludes_already_used_invoices(self, db):
        from app.services.substitute_service import list_substitute_invoices

        user = _Helpers._create_user(db, "si_test2")

        used = _Helpers._create_confirmed_invoice(db, user.id, amount=500.0)
        free = _Helpers._create_confirmed_invoice(db, user.id, amount=300.0)

        batch = _Helpers._create_batch(db, user.id)
        _Helpers._add_invoice_to_batch(db, batch.id, used.id)

        result = list_substitute_invoices(db, user.id, batch.id)
        ids = {item.id for item in result.items}
        assert used.id not in ids
        assert free.id in ids

    def test_calculates_remaining_amount(self, db):
        from app.models.batch import BatchInvoice
        from app.models.substitute import SubstituteRelation
        from app.services.batch_service import add_manual_row
        from app.services.substitute_service import list_substitute_invoices
        from app.schemas.batch import ManualRowCreateRequest

        user = _Helpers._create_user(db, "si_test3")
        batch = _Helpers._create_batch(db, user.id)

        invoice = _Helpers._create_confirmed_invoice(db, user.id, amount=3000.0)

        row = add_manual_row(
            db, user.id, batch.id,
            ManualRowCreateRequest(expense_item="奖金", row_amount=1000.0),
        )

        placeholder = BatchInvoice(
            batch_id=batch.id,
            invoice_id=invoice.id,
            source_type="invoice",
            is_substitute=True,
        )
        db.add(placeholder)
        db.commit()

        rel = SubstituteRelation(
            batch_id=batch.id,
            substitute_invoice_id=invoice.id,
            target_row_id=row.id,
            mode="one_to_one",
        )
        db.add(rel)
        db.commit()

        result = list_substitute_invoices(db, user.id, batch.id)
        for item in result.items:
            if item.id == invoice.id:
                assert item.used_as_substitute >= 1000.0
                assert item.remaining_amount <= 2000.0

    def test_keyword_filter(self, db):
        from app.services.substitute_service import list_substitute_invoices

        user = _Helpers._create_user(db, "si_test4")

        match = _Helpers._create_confirmed_invoice(db, user.id, vendor="咨询公司")
        no_match = _Helpers._create_confirmed_invoice(db, user.id, vendor="交通公司")

        batch = _Helpers._create_batch(db, user.id)

        result = list_substitute_invoices(db, user.id, batch.id, keyword="咨询")
        ids = {item.id for item in result.items}
        assert match.id in ids
        assert no_match.id not in ids

    def test_empty_when_no_available(self, db):
        from app.services.substitute_service import list_substitute_invoices

        user = _Helpers._create_user(db, "si_test5")
        batch = _Helpers._create_batch(db, user.id)

        result = list_substitute_invoices(db, user.id, batch.id)
        assert result.total == 0
        assert len(result.items) == 0

    def test_pagination(self, db):
        from app.services.substitute_service import list_substitute_invoices

        user = _Helpers._create_user(db, "si_test6")
        batch = _Helpers._create_batch(db, user.id)

        for i in range(5):
            _Helpers._create_confirmed_invoice(db, user.id, amount=100.0, vendor=f"公司{i}")

        result = list_substitute_invoices(db, user.id, batch.id, page=1, page_size=3)
        assert result.total == 5
        assert len(result.items) == 3
        assert result.page == 1
        assert result.page_size == 3


class _SubHelpers:
    @staticmethod
    def _create(user, db, batch, invoice, row):
        from app.models.batch import BatchInvoice
        from app.models.substitute import SubstituteRelation
        from app.services.batch_service import add_manual_row
        from app.schemas.batch import ManualRowCreateRequest

        row_obj = add_manual_row(
            db, user.id, batch.id,
            ManualRowCreateRequest(
                expense_item=row["expense_item"],
                row_amount=row["row_amount"],
            ),
        )

        placeholder = BatchInvoice(
            batch_id=batch.id,
            invoice_id=invoice.id,
            source_type="invoice",
            is_substitute=True,
        )
        db.add(placeholder)
        db.commit()

        rel = SubstituteRelation(
            batch_id=batch.id,
            substitute_invoice_id=invoice.id,
            target_row_id=row_obj.id,
            mode="one_to_one",
        )
        db.add(rel)
        db.commit()
        return row_obj


class TestCreateSubstitution:
    def test_one_to_one_success(self, db):
        from app.services.batch_service import add_manual_row
        from app.services.substitute_service import create_substitution
        from app.schemas.batch import ManualRowCreateRequest, SubstituteCreateRequest

        user = _Helpers._create_user(db, "cs_test1")
        batch = _Helpers._create_batch(db, user.id)
        invoice = _Helpers._create_confirmed_invoice(db, user.id, amount=1000.0)

        row = add_manual_row(
            db, user.id, batch.id,
            ManualRowCreateRequest(expense_item="奖金", row_amount=1000.0),
        )

        req = SubstituteCreateRequest(
            mode="one_to_one",
            substitute_invoice_ids=[invoice.id],
            target_row_ids=[row.id],
        )
        result = create_substitution(db, user.id, batch.id, req)

        assert len(result.relations) == 1
        assert result.relations[0].mode == "one_to_one"
        assert len(result.updated_target_rows) == 1
        updated = result.updated_target_rows[0]
        assert updated.is_substitute is True
        assert updated.substitute_for is not None
        assert invoice.invoice_no in updated.remark

    def test_one_to_many_success(self, db):
        from app.services.batch_service import add_manual_row
        from app.services.substitute_service import create_substitution
        from app.schemas.batch import ManualRowCreateRequest, SubstituteCreateRequest

        user = _Helpers._create_user(db, "cs_test2")
        batch = _Helpers._create_batch(db, user.id)
        invoice = _Helpers._create_confirmed_invoice(db, user.id, amount=3000.0)

        row1 = add_manual_row(db, user.id, batch.id, ManualRowCreateRequest(expense_item="A", row_amount=1000.0))
        row2 = add_manual_row(db, user.id, batch.id, ManualRowCreateRequest(expense_item="B", row_amount=1000.0))
        row3 = add_manual_row(db, user.id, batch.id, ManualRowCreateRequest(expense_item="C", row_amount=500.0))

        req = SubstituteCreateRequest(
            mode="one_to_many",
            substitute_invoice_ids=[invoice.id],
            target_row_ids=[row1.id, row2.id, row3.id],
        )
        result = create_substitution(db, user.id, batch.id, req)

        assert len(result.relations) == 3
        assert len(result.updated_target_rows) == 3
        for r in result.updated_target_rows:
            assert r.is_substitute is True
            assert invoice.invoice_no in r.remark

    def test_many_to_one_success(self, db):
        from app.services.batch_service import add_manual_row
        from app.services.substitute_service import create_substitution
        from app.schemas.batch import ManualRowCreateRequest, SubstituteCreateRequest

        user = _Helpers._create_user(db, "cs_test3")
        batch = _Helpers._create_batch(db, user.id)

        inv1 = _Helpers._create_confirmed_invoice(db, user.id, amount=400.0)
        inv2 = _Helpers._create_confirmed_invoice(db, user.id, amount=300.0)
        inv3 = _Helpers._create_confirmed_invoice(db, user.id, amount=300.0)

        row = add_manual_row(db, user.id, batch.id, ManualRowCreateRequest(expense_item="团建", row_amount=1000.0))

        req = SubstituteCreateRequest(
            mode="many_to_one",
            substitute_invoice_ids=[inv1.id, inv2.id, inv3.id],
            target_row_ids=[row.id],
        )
        result = create_substitution(db, user.id, batch.id, req)

        assert len(result.relations) == 3
        updated = result.updated_target_rows[0]
        assert "替票" in updated.remark
        assert updated.is_substitute is True

    def test_insufficient_amount_returns_400(self, db):
        from app.services.batch_service import add_manual_row
        from app.services.substitute_service import create_substitution
        from app.schemas.batch import ManualRowCreateRequest, SubstituteCreateRequest

        user = _Helpers._create_user(db, "cs_test4")
        batch = _Helpers._create_batch(db, user.id)
        invoice = _Helpers._create_confirmed_invoice(db, user.id, amount=500.0)

        row = add_manual_row(db, user.id, batch.id, ManualRowCreateRequest(expense_item="奖金", row_amount=1000.0))

        req = SubstituteCreateRequest(
            mode="one_to_one",
            substitute_invoice_ids=[invoice.id],
            target_row_ids=[row.id],
        )
        with pytest.raises(HTTPException) as exc:
            create_substitution(db, user.id, batch.id, req)
        assert exc.value.status_code == 400
        assert "不足" in exc.value.detail

    def test_invoice_already_occupied_returns_400(self, db):
        from app.models.batch import BatchInvoice
        from app.services.batch_service import add_manual_row
        from app.services.substitute_service import create_substitution
        from app.schemas.batch import ManualRowCreateRequest, SubstituteCreateRequest

        user = _Helpers._create_user(db, "cs_test5")
        batch = _Helpers._create_batch(db, user.id)
        invoice = _Helpers._create_confirmed_invoice(db, user.id, amount=1000.0)

        _Helpers._add_invoice_to_batch(db, batch.id, invoice.id)

        from app.models.batch import BatchInvoice
        row = add_manual_row(db, user.id, batch.id, ManualRowCreateRequest(expense_item="奖金", row_amount=500.0))

        req = SubstituteCreateRequest(
            mode="one_to_one",
            substitute_invoice_ids=[invoice.id],
            target_row_ids=[row.id],
        )
        with pytest.raises(HTTPException) as exc:
            create_substitution(db, user.id, batch.id, req)
        assert exc.value.status_code == 400

    def test_mode_mismatch_returns_400(self, db):
        from app.services.batch_service import add_manual_row
        from app.services.substitute_service import create_substitution
        from app.schemas.batch import ManualRowCreateRequest, SubstituteCreateRequest

        user = _Helpers._create_user(db, "cs_test6")
        batch = _Helpers._create_batch(db, user.id)
        invoice = _Helpers._create_confirmed_invoice(db, user.id, amount=1000.0)

        row = add_manual_row(db, user.id, batch.id, ManualRowCreateRequest(expense_item="奖金", row_amount=1000.0))

        req = SubstituteCreateRequest(
            mode="one_to_one",
            substitute_invoice_ids=[invoice.id, 999],
            target_row_ids=[row.id],
        )
        with pytest.raises(HTTPException) as exc:
            create_substitution(db, user.id, batch.id, req)
        assert exc.value.status_code == 400

    def test_target_row_not_in_batch_returns_400(self, db):
        from app.services.batch_service import add_manual_row
        from app.services.substitute_service import create_substitution
        from app.schemas.batch import ManualRowCreateRequest, SubstituteCreateRequest

        user = _Helpers._create_user(db, "cs_test7")
        batch1 = _Helpers._create_batch(db, user.id, department="A")
        batch2 = _Helpers._create_batch(db, user.id, department="B")

        invoice = _Helpers._create_confirmed_invoice(db, user.id, amount=1000.0)
        row = add_manual_row(db, user.id, batch1.id, ManualRowCreateRequest(expense_item="奖金", row_amount=1000.0))

        req = SubstituteCreateRequest(
            mode="one_to_one",
            substitute_invoice_ids=[invoice.id],
            target_row_ids=[row.id],
        )
        with pytest.raises(HTTPException) as exc:
            create_substitution(db, user.id, batch2.id, req)
        assert exc.value.status_code == 400

    def test_placeholder_batch_invoice_created(self, db):
        from app.models.batch import BatchInvoice
        from app.services.batch_service import add_manual_row
        from app.services.substitute_service import create_substitution
        from app.schemas.batch import ManualRowCreateRequest, SubstituteCreateRequest

        user = _Helpers._create_user(db, "cs_test8")
        batch = _Helpers._create_batch(db, user.id)
        invoice = _Helpers._create_confirmed_invoice(db, user.id, amount=1000.0)

        row = add_manual_row(db, user.id, batch.id, ManualRowCreateRequest(expense_item="奖金", row_amount=1000.0))

        req = SubstituteCreateRequest(
            mode="one_to_one",
            substitute_invoice_ids=[invoice.id],
            target_row_ids=[row.id],
        )
        create_substitution(db, user.id, batch.id, req)

        placeholder = db.query(BatchInvoice).filter(
            BatchInvoice.batch_id == batch.id,
            BatchInvoice.invoice_id == invoice.id,
            BatchInvoice.is_substitute == True,
        ).first()
        assert placeholder is not None
        assert placeholder.source_type == "invoice"

    def test_remaining_amount_allows_partial_reuse(self, db):
        from app.services.batch_service import add_manual_row
        from app.services.substitute_service import create_substitution
        from app.schemas.batch import ManualRowCreateRequest, SubstituteCreateRequest

        user = _Helpers._create_user(db, "cs_test9")
        batch = _Helpers._create_batch(db, user.id)
        invoice = _Helpers._create_confirmed_invoice(db, user.id, amount=3000.0)

        row = add_manual_row(db, user.id, batch.id, ManualRowCreateRequest(expense_item="奖金", row_amount=1000.0))

        req = SubstituteCreateRequest(
            mode="one_to_one",
            substitute_invoice_ids=[invoice.id],
            target_row_ids=[row.id],
        )
        create_substitution(db, user.id, batch.id, req)

        row2 = add_manual_row(db, user.id, batch.id, ManualRowCreateRequest(expense_item="团建", row_amount=1500.0))

        req2 = SubstituteCreateRequest(
            mode="one_to_one",
            substitute_invoice_ids=[invoice.id],
            target_row_ids=[row2.id],
        )
        result = create_substitution(db, user.id, batch.id, req2)
        assert len(result.relations) == 1
        assert result.updated_target_rows[0].is_substitute is True


class TestListSubstitutions:
    def test_list_substitutions_returns_relations(self, db):
        from app.services.substitute_service import list_substitutions

        user = _Helpers._create_user(db, "ls_test1")
        batch = _Helpers._create_batch(db, user.id)
        invoice = _Helpers._create_confirmed_invoice(db, user.id, amount=1000.0)

        _SubHelpers._create(user, db, batch, invoice, {"expense_item": "奖金", "row_amount": 1000.0})

        result = list_substitutions(db, user.id, batch.id)
        assert len(result.relations) == 1
        r = result.relations[0]
        assert r.mode == "one_to_one"
        assert r.substitute_invoice is not None
        assert r.target_row is not None

    def test_list_substitutions_empty(self, db):
        from app.services.substitute_service import list_substitutions

        user = _Helpers._create_user(db, "ls_test2")
        batch = _Helpers._create_batch(db, user.id)

        result = list_substitutions(db, user.id, batch.id)
        assert len(result.relations) == 0

    def test_list_substitutions_multiple(self, db):
        from app.services.substitute_service import list_substitutions

        user = _Helpers._create_user(db, "ls_test3")
        batch = _Helpers._create_batch(db, user.id)

        inv1 = _Helpers._create_confirmed_invoice(db, user.id, amount=500.0)
        inv2 = _Helpers._create_confirmed_invoice(db, user.id, amount=500.0)

        _SubHelpers._create(user, db, batch, inv1, {"expense_item": "A", "row_amount": 500.0})
        _SubHelpers._create(user, db, batch, inv2, {"expense_item": "B", "row_amount": 500.0})

        result = list_substitutions(db, user.id, batch.id)
        assert len(result.relations) == 2


class TestRemoveSubstitution:
    def test_remove_substitution_clears_remark(self, db):
        from app.services.substitute_service import (
            create_substitution,
            list_substitutions,
            remove_substitution,
        )
        from app.services.batch_service import add_manual_row
        from app.schemas.batch import ManualRowCreateRequest, SubstituteCreateRequest

        user = _Helpers._create_user(db, "rm_test1")
        batch = _Helpers._create_batch(db, user.id)
        invoice = _Helpers._create_confirmed_invoice(db, user.id, amount=1000.0)

        row = add_manual_row(
            db, user.id, batch.id,
            ManualRowCreateRequest(expense_item="奖金", row_amount=1000.0),
        )
        create_substitution(
            db, user.id, batch.id,
            SubstituteCreateRequest(
                mode="one_to_one",
                substitute_invoice_ids=[invoice.id],
                target_row_ids=[row.id],
            ),
        )

        relations = list_substitutions(db, user.id, batch.id)
        sub_id = relations.relations[0].id
        remove_substitution(db, user.id, batch.id, sub_id)

        from app.models.batch import BatchInvoice
        updated = db.query(BatchInvoice).filter(BatchInvoice.id == row.id).first()
        assert updated.is_substitute is False
        assert updated.substitute_for is None
        assert "替票" not in (updated.remark or "")

    def test_remove_substitution_keeps_multiple(self, db):
        from app.services.substitute_service import (
            create_substitution,
            list_substitutions,
            remove_substitution,
        )
        from app.services.batch_service import add_manual_row
        from app.schemas.batch import ManualRowCreateRequest, SubstituteCreateRequest

        user = _Helpers._create_user(db, "rm_test2")
        batch = _Helpers._create_batch(db, user.id)
        inv1 = _Helpers._create_confirmed_invoice(db, user.id, amount=500.0)
        inv2 = _Helpers._create_confirmed_invoice(db, user.id, amount=500.0)

        row = add_manual_row(
            db, user.id, batch.id,
            ManualRowCreateRequest(expense_item="团建", row_amount=1000.0),
        )
        create_substitution(
            db, user.id, batch.id,
            SubstituteCreateRequest(
                mode="many_to_one",
                substitute_invoice_ids=[inv1.id, inv2.id],
                target_row_ids=[row.id],
            ),
        )

        relations = list_substitutions(db, user.id, batch.id)
        assert len(relations.relations) == 2

        remove_substitution(db, user.id, batch.id, relations.relations[0].id)

        from app.models.batch import BatchInvoice
        updated = db.query(BatchInvoice).filter(BatchInvoice.id == row.id).first()
        assert updated.is_substitute is True
        assert "替票" in (updated.remark or "")

    def test_remove_substitution_releases_placeholder(self, db):
        from app.services.substitute_service import (
            create_substitution,
            list_substitutions,
            remove_substitution,
        )
        from app.services.batch_service import add_manual_row
        from app.schemas.batch import ManualRowCreateRequest, SubstituteCreateRequest

        user = _Helpers._create_user(db, "rm_test3")
        batch = _Helpers._create_batch(db, user.id)
        invoice = _Helpers._create_confirmed_invoice(db, user.id, amount=1000.0)

        row = add_manual_row(
            db, user.id, batch.id,
            ManualRowCreateRequest(expense_item="奖金", row_amount=1000.0),
        )
        create_substitution(
            db, user.id, batch.id,
            SubstituteCreateRequest(
                mode="one_to_one",
                substitute_invoice_ids=[invoice.id],
                target_row_ids=[row.id],
            ),
        )

        relations = list_substitutions(db, user.id, batch.id)
        sub_id = relations.relations[0].id
        remove_substitution(db, user.id, batch.id, sub_id)

        from app.models.batch import BatchInvoice
        placeholder = db.query(BatchInvoice).filter(
            BatchInvoice.batch_id == batch.id,
            BatchInvoice.invoice_id == invoice.id,
            BatchInvoice.is_substitute == True,
        ).first()
        assert placeholder is None

    def test_remove_substitution_not_found(self, db):
        from app.services.substitute_service import remove_substitution

        user = _Helpers._create_user(db, "rm_test4")
        batch = _Helpers._create_batch(db, user.id)

        with pytest.raises(HTTPException) as exc:
            remove_substitution(db, user.id, batch.id, 999)
        assert exc.value.status_code == 404