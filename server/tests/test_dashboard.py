import pytest
from datetime import date, datetime

from app.models.invoice import Invoice
from app.models.batch import ReimbursementBatch


class TestDashboardSchema:
    def test_recent_batch_item_schema(self):
        from app.schemas.dashboard import RecentBatchItem

        item = RecentBatchItem(
            id=1,
            department="研发部",
            period_start=date(2025, 12, 1),
            period_end=date(2025, 12, 31),
            report_date=date(2025, 12, 15),
            reporter="张三",
            total_amount=3280.50,
            status="draft",
            invoice_count=12,
            created_at=datetime(2025, 12, 15, 10, 30, 0),
        )
        assert item.id == 1
        assert item.department == "研发部"
        assert item.total_amount == 3280.50
        assert item.invoice_count == 12
        assert item.status == "draft"
        assert item.reporter == "张三"

    def test_recent_batch_item_nullable_fields(self):
        from app.schemas.dashboard import RecentBatchItem

        item = RecentBatchItem(
            id=1,
            department="研发部",
            reporter="张三",
            total_amount=0.0,
            status="draft",
            invoice_count=0,
            created_at=datetime.now(),
        )
        assert item.period_start is None
        assert item.period_end is None
        assert item.report_date is None

    def test_dashboard_stats_response_schema(self):
        from app.schemas.dashboard import DashboardStatsResponse, RecentBatchItem

        batches = [
            RecentBatchItem(
                id=1,
                department="研发部",
                reporter="张三",
                total_amount=3280.50,
                status="draft",
                invoice_count=12,
                created_at=datetime(2025, 12, 15, 10, 30, 0),
            )
        ]
        stats = DashboardStatsResponse(
            pending_invoice_count=12,
            monthly_total_amount=3280.50,
            active_batch_count=3,
            recent_batches=batches,
        )
        assert stats.pending_invoice_count == 12
        assert stats.monthly_total_amount == 3280.50
        assert stats.active_batch_count == 3
        assert len(stats.recent_batches) == 1

    def test_dashboard_stats_empty_batches(self):
        from app.schemas.dashboard import DashboardStatsResponse

        stats = DashboardStatsResponse(
            pending_invoice_count=0,
            monthly_total_amount=0.0,
            active_batch_count=0,
            recent_batches=[],
        )
        assert stats.pending_invoice_count == 0
        assert stats.monthly_total_amount == 0.0
        assert stats.active_batch_count == 0
        assert stats.recent_batches == []


class TestDashboardService:
    def test_get_dashboard_stats_empty(self, db, test_user):
        from app.services.dashboard_service import get_dashboard_stats

        stats = get_dashboard_stats(db, test_user.id)
        assert stats.pending_invoice_count == 0
        assert stats.monthly_total_amount == 0.0
        assert stats.active_batch_count == 0
        assert stats.recent_batches == []

    def test_pending_invoice_count(self, db, test_user):
        from app.services.dashboard_service import get_dashboard_stats

        for _ in range(3):
            db.add(Invoice(user_id=test_user.id, file_path="/tmp/test.jpg", status="pending"))
        for _ in range(2):
            db.add(Invoice(user_id=test_user.id, file_path="/tmp/test.jpg", status="confirmed"))
        db.commit()

        stats = get_dashboard_stats(db, test_user.id)
        assert stats.pending_invoice_count == 3, "Should count only pending invoices"

    def test_monthly_total_amount_excludes_non_current_month(self, db, test_user):
        from app.services.dashboard_service import get_dashboard_stats

        today = date.today()
        this_month = today.replace(day=15)
        last_month = date(today.year - 1 if today.month == 1 else today.year, today.month - 1 if today.month > 1 else 12, 15)

        db.add(Invoice(user_id=test_user.id, file_path="/tmp/t1.jpg", status="confirmed",
                       invoice_date=this_month, amount=100.50))
        db.add(Invoice(user_id=test_user.id, file_path="/tmp/t2.jpg", status="confirmed",
                       invoice_date=this_month, amount=200.00))
        db.add(Invoice(user_id=test_user.id, file_path="/tmp/t3.jpg", status="confirmed",
                       invoice_date=last_month, amount=300.00))
        db.commit()

        stats = get_dashboard_stats(db, test_user.id)
        assert stats.monthly_total_amount == 300.50, "Should sum only this month's confirmed invoices"

    def test_monthly_total_excludes_deleted(self, db, test_user):
        from datetime import datetime, timezone
        from app.services.dashboard_service import get_dashboard_stats

        today = date.today()
        db.add(Invoice(user_id=test_user.id, file_path="/tmp/t1.jpg", status="confirmed",
                       invoice_date=today, amount=500.00))
        deleted = Invoice(user_id=test_user.id, file_path="/tmp/t2.jpg", status="confirmed",
                          invoice_date=today, amount=999.00)
        db.add(deleted)
        db.flush()
        deleted.deleted_at = datetime.now(timezone.utc)
        db.commit()

        stats = get_dashboard_stats(db, test_user.id)
        assert stats.monthly_total_amount == 500.00, "Should exclude soft-deleted invoices"

    def test_active_batch_count(self, db, test_user):
        from app.services.dashboard_service import get_dashboard_stats

        for _ in range(3):
            db.add(ReimbursementBatch(user_id=test_user.id, department="研发部", reporter="张三"))
        db.commit()

        stats = get_dashboard_stats(db, test_user.id)
        assert stats.active_batch_count == 3

    def test_recent_batches_returns_at_most_5(self, db, test_user):
        from app.services.dashboard_service import get_dashboard_stats

        for i in range(7):
            db.add(ReimbursementBatch(
                user_id=test_user.id,
                department=f"部门{i}",
                reporter="张三",
                total_amount=float(i * 100),
                created_at=datetime(2025, 12, 10 + i, 10, 0, 0),
            ))
        db.commit()

        stats = get_dashboard_stats(db, test_user.id)
        assert len(stats.recent_batches) == 5, "Should return at most 5 recent batches"

    def test_recent_batches_ordered_by_created_at_desc(self, db, test_user):
        from app.services.dashboard_service import get_dashboard_stats

        for i in range(3):
            db.add(ReimbursementBatch(
                user_id=test_user.id,
                department=f"批次{i}",
                reporter="张三",
                total_amount=float(i * 100),
                created_at=datetime(2025, 12, 10 + i, 10, 0, 0),
            ))
        db.commit()

        stats = get_dashboard_stats(db, test_user.id)
        assert stats.recent_batches[0].department == "批次2"
        assert stats.recent_batches[1].department == "批次1"
        assert stats.recent_batches[2].department == "批次0"


class TestDashboardAPI:
    def test_stats_returns_200_with_valid_token(self, client, auth_headers):
        response = client.get("/api/dashboard/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "pending_invoice_count" in data
        assert "monthly_total_amount" in data
        assert "active_batch_count" in data
        assert "recent_batches" in data

    def test_stats_returns_401_without_token(self, client):
        response = client.get("/api/dashboard/stats")
        assert response.status_code == 401

    def test_stats_returns_401_with_invalid_token(self, client):
        response = client.get("/api/dashboard/stats", headers={"Authorization": "Bearer invalid"})
        assert response.status_code == 401