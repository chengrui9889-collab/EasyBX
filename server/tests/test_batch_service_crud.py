from datetime import date

import pytest
from fastapi import HTTPException

from app.models.batch import ReimbursementBatch
from app.models.user import User
from app.schemas.batch import CreateBatchRequest


class TestCreateBatch:
    def test_create_batch_basic(self, db):
        from app.services.batch_service import create_batch

        user = User(
            username="batch_test",
            password_hash="hash",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        req = CreateBatchRequest(
            department="研发部",
            reporter="张三",
        )
        batch = create_batch(db, user.id, req)
        assert batch.id is not None
        assert batch.department == "研发部"
        assert batch.reporter == "张三"
        assert batch.status == "draft"
        assert batch.total_amount == 0.0

    def test_create_batch_fills_user_defaults(self, db):
        from app.services.batch_service import create_batch

        user = User(
            username="batch_test2",
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

        req = CreateBatchRequest()
        batch = create_batch(db, user.id, req)
        assert batch.department == "产教融合"
        assert batch.reporter == "程瑞"
        assert batch.payee == "程瑞"
        assert batch.bank_account == "6222000000000000"
        assert batch.bank_name == "中国工商银行"

    def test_create_batch_explicit_overrides_defaults(self, db):
        from app.services.batch_service import create_batch

        user = User(
            username="batch_test3",
            password_hash="hash",
            default_department="产教融合",
            default_reporter="程瑞",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        req = CreateBatchRequest(department="研发部")
        batch = create_batch(db, user.id, req)
        assert batch.department == "研发部"
        assert batch.reporter == "程瑞"

    def test_create_batch_report_date_defaults_today(self, db):
        from app.services.batch_service import create_batch

        user = User(
            username="batch_test4",
            password_hash="hash",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        req = CreateBatchRequest()
        batch = create_batch(db, user.id, req)
        assert batch.report_date == date.today()

    def test_create_batch_report_date_explicit(self, db):
        from app.services.batch_service import create_batch

        user = User(
            username="batch_test5",
            password_hash="hash",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        req = CreateBatchRequest(report_date=date(2026, 1, 15))
        batch = create_batch(db, user.id, req)
        assert batch.report_date == date(2026, 1, 15)


class TestListBatches:
    def test_list_batches_empty(self, db):
        from app.services.batch_service import list_batches

        user = User(
            username="list_test",
            password_hash="hash",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        resp = list_batches(db, user.id)
        assert resp.total == 0
        assert resp.items == []

    def test_list_batches_returns_invoice_count(self, db):
        from app.services.batch_service import create_batch, list_batches

        user = User(
            username="list_test2",
            password_hash="hash",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        create_batch(db, user.id, CreateBatchRequest(department="部门A", reporter="人A"))
        create_batch(db, user.id, CreateBatchRequest(department="部门B", reporter="人B"))

        resp = list_batches(db, user.id)
        assert resp.total == 2
        assert len(resp.items) == 2
        for item in resp.items:
            assert item.invoice_count == 0

    def test_list_batches_desc_order(self, db):
        from app.services.batch_service import create_batch, list_batches

        user = User(
            username="list_test3",
            password_hash="hash",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        create_batch(db, user.id, CreateBatchRequest(department="部门A", reporter="人A"))
        create_batch(db, user.id, CreateBatchRequest(department="部门B", reporter="人B"))

        resp = list_batches(db, user.id)
        assert resp.items[0].created_at >= resp.items[1].created_at

    def test_list_batches_data_isolation(self, db):
        from app.services.batch_service import create_batch, list_batches

        user_a = User(username="user_a", password_hash="hash")
        user_b = User(username="user_b", password_hash="hash")
        db.add_all([user_a, user_b])
        db.commit()

        create_batch(db, user_a.id, CreateBatchRequest(department="A部门", reporter="A"))
        create_batch(db, user_a.id, CreateBatchRequest(department="A部门2", reporter="A2"))

        resp_b = list_batches(db, user_b.id)
        assert resp_b.total == 0