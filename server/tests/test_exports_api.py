from datetime import date
from io import BytesIO
from pathlib import Path

import pytest
from PyPDF2 import PdfReader
from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.models.batch import BatchInvoice, ReimbursementBatch
from app.models.invoice import Invoice


def _create_test_pdf(output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=A4)
    c.drawString(100, 750, "Invoice PDF")
    c.save()
    return output_path


def _create_test_image(output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img = PILImage.new("RGB", (200, 300), color=(200, 200, 255))
    img.save(str(output_path), "PNG")
    return output_path


class TestExportInvoicePdf:
    def test_success_returns_pdf(self, client, auth_headers, tmp_path, db):
        img_path = _create_test_image(tmp_path / "inv.png")
        inv = Invoice(user_id=1, file_path=str(img_path), status="confirmed", amount=100.0)
        db.add(inv)
        db.commit()
        db.refresh(inv)

        response = client.post(
            "/api/exports/invoice-pdf",
            json={"invoice_ids": [inv.id], "layouts": {}},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]

    def test_empty_invoice_ids_returns_400(self, client, auth_headers):
        response = client.post(
            "/api/exports/invoice-pdf",
            json={"invoice_ids": [], "layouts": {}},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "EMPTY_INVOICES"

    def test_invoice_not_found_returns_404(self, client, auth_headers, test_user, db):
        other_user = type("obj", (object,), {"id": 999})()
        response = client.post(
            "/api/exports/invoice-pdf",
            json={"invoice_ids": [99999], "layouts": {}},
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "INVOICE_NOT_FOUND"

    def test_other_user_invoice_returns_404(self, client, auth_headers, tmp_path, db):
        img_path = _create_test_image(tmp_path / "other.png")
        inv = Invoice(user_id=999, file_path=str(img_path), status="confirmed", amount=100.0)
        db.add(inv)
        db.commit()
        db.refresh(inv)

        response = client.post(
            "/api/exports/invoice-pdf",
            json={"invoice_ids": [inv.id], "layouts": {}},
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "INVOICE_NOT_FOUND"

    def test_unauthorized_returns_401(self, client):
        response = client.post(
            "/api/exports/invoice-pdf",
            json={"invoice_ids": [1], "layouts": {}},
        )
        assert response.status_code == 401

    def test_invalid_layout_returns_422(self, client, auth_headers):
        response = client.post(
            "/api/exports/invoice-pdf",
            json={"invoice_ids": [1], "layouts": {"xx": "invalid"}},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_multiple_invoices_generates_pdf(self, client, auth_headers, tmp_path, db):
        invoices = []
        for i in range(3):
            p = _create_test_image(tmp_path / f"multi_{i}.png")
            inv = Invoice(user_id=1, file_path=str(p), status="confirmed", amount=100.0)
            db.add(inv)
            db.commit()
            db.refresh(inv)
            invoices.append(inv)

        response = client.post(
            "/api/exports/invoice-pdf",
            json={"invoice_ids": [inv.id for inv in invoices], "layouts": {}},
            headers=auth_headers,
        )
        assert response.status_code == 200
        reader = PdfReader(BytesIO(response.content))
        assert len(reader.pages) >= 1


class TestExportBatchInvoicePdf:
    @pytest.fixture
    def batch_and_invoices(self, db, test_user, tmp_path):
        batch = ReimbursementBatch(
            user_id=test_user.id, department="测试部", reporter="测试人", status="draft"
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)

        invoices = []
        for i in range(2):
            p = _create_test_image(tmp_path / f"batch_inv_{i}.png")
            inv = Invoice(
                user_id=test_user.id, file_path=str(p), status="confirmed", amount=100.0
            )
            db.add(inv)
            db.commit()
            db.refresh(inv)
            invoices.append(inv)

            bi = BatchInvoice(batch_id=batch.id, invoice_id=inv.id, source_type="invoice")
            db.add(bi)
        db.commit()
        return batch, invoices

    def test_success_returns_pdf(self, client, auth_headers, batch_and_invoices):
        batch, _ = batch_and_invoices
        response = client.post(
            f"/api/batches/{batch.id}/export-invoice-pdf",
            json={"layouts": {}},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]

    def test_nonexistent_batch_returns_404(self, client, auth_headers):
        response = client.post(
            "/api/batches/99999/export-invoice-pdf",
            json={"layouts": {}},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_other_user_batch_returns_404(self, client, auth_headers, db, tmp_path):
        batch = ReimbursementBatch(
            user_id=999, department="其他部", reporter="其他人", status="draft"
        )
        db.add(batch)
        db.commit()

        response = client.post(
            f"/api/batches/{batch.id}/export-invoice-pdf",
            json={"layouts": {}},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_empty_batch_returns_400(self, client, auth_headers, db, test_user):
        batch = ReimbursementBatch(
            user_id=test_user.id, department="空批次", reporter="测试人", status="draft"
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)

        response = client.post(
            f"/api/batches/{batch.id}/export-invoice-pdf",
            json={"layouts": {}},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "EMPTY_BATCH"

    def test_unauthorized_returns_401(self, client, batch_and_invoices):
        batch, _ = batch_and_invoices
        response = client.post(
            f"/api/batches/{batch.id}/export-invoice-pdf",
            json={"layouts": {}},
        )
        assert response.status_code == 401

    def test_substitute_invoice_included(self, client, auth_headers, db, test_user, tmp_path):
        batch = ReimbursementBatch(
            user_id=test_user.id, department="替票测试", reporter="测试人", status="draft"
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)

        p = _create_test_image(tmp_path / "sub.png")
        inv = Invoice(
            user_id=test_user.id, file_path=str(p), status="confirmed", amount=100.0
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)

        bi = BatchInvoice(
            batch_id=batch.id, invoice_id=inv.id, source_type="invoice", is_substitute=True
        )
        db.add(bi)
        db.commit()

        response = client.post(
            f"/api/batches/{batch.id}/export-invoice-pdf",
            json={"layouts": {}},
            headers=auth_headers,
        )
        assert response.status_code == 200
        reader = PdfReader(BytesIO(response.content))
        assert len(reader.pages) == 1

    def test_multiple_pages_pdf(self, client, auth_headers, db, test_user, tmp_path):
        batch = ReimbursementBatch(
            user_id=test_user.id, department="多页测试", reporter="测试人", status="draft"
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)

        invoices = []
        for i in range(3):
            p = _create_test_image(tmp_path / f"batch_pg_{i}.png")
            inv = Invoice(
                user_id=test_user.id, file_path=str(p), status="confirmed", amount=100.0
            )
            db.add(inv)
            db.commit()
            db.refresh(inv)
            invoices.append(inv)

            bi = BatchInvoice(batch_id=batch.id, invoice_id=inv.id, source_type="invoice")
            db.add(bi)
        db.commit()

        response = client.post(
            f"/api/batches/{batch.id}/export-invoice-pdf",
            json={"layouts": {}},
            headers=auth_headers,
        )
        assert response.status_code == 200
        reader = PdfReader(BytesIO(response.content))
        assert len(reader.pages) >= 1


class TestReimbursementPreviewAPI:
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
            user_id=test_user.id, amount=34.00, category="交通费",
            file_path="/fake/path1.jpg", status="confirmed",
        )
        inv2 = Invoice(
            user_id=test_user.id, amount=56.00, category="交通费",
            file_path="/fake/path2.jpg", status="confirmed",
        )
        inv3 = Invoice(
            user_id=test_user.id, amount=78.00, category="交通费",
            file_path="/fake/path3.jpg", status="confirmed",
        )
        inv4 = Invoice(
            user_id=test_user.id, amount=100.00, category="餐饮费",
            file_path="/fake/path4.jpg", status="confirmed",
        )
        inv5 = Invoice(
            user_id=test_user.id, amount=200.00, category="餐饮费",
            file_path="/fake/path5.jpg", status="confirmed",
        )
        db.add_all([inv1, inv2, inv3, inv4, inv5])
        db.commit()
        for inv in [inv1, inv2, inv3, inv4, inv5]:
            db.refresh(inv)

        for inv in [inv1, inv2, inv3, inv4, inv5]:
            bi = BatchInvoice(
                batch_id=batch.id, invoice_id=inv.id, source_type="invoice",
            )
            db.add(bi)
        db.commit()

        return batch

    def test_success_returns_preview(self, client, auth_headers, batch_with_invoices):
        response = client.get(
            f"/api/exports/reimbursement-preview/{batch_with_invoices.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["department"] == "产教融合"
        assert data["reporter"] == "程瑞"
        assert data["total_amount"] == 468.00
        assert data["total_amount_cn"] == "肆佰陆拾捌元整"
        assert len(data["items"]) == 2
        item_dict = {i["expense_item"]: i["amount"] for i in data["items"]}
        assert item_dict["交通费"] == 168.00
        assert item_dict["餐饮费"] == 300.00

    def test_batch_not_found_returns_404(self, client, auth_headers):
        response = client.get(
            "/api/exports/reimbursement-preview/99999",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_other_user_batch_returns_404(self, client, auth_headers, db):
        batch = ReimbursementBatch(
            user_id=999, department="其他", reporter="某人", status="draft",
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)

        response = client.get(
            f"/api/exports/reimbursement-preview/{batch.id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_empty_batch_returns_400(self, client, auth_headers, db, test_user):
        batch = ReimbursementBatch(
            user_id=test_user.id, department="空", reporter="空", status="draft",
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)

        response = client.get(
            f"/api/exports/reimbursement-preview/{batch.id}",
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_unauthorized_returns_401(self, client, batch_with_invoices):
        response = client.get(
            f"/api/exports/reimbursement-preview/{batch_with_invoices.id}",
        )
        assert response.status_code == 401

    def test_manual_rows_merge_correctly(self, client, auth_headers, db, batch_with_invoices):
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

        response = client.get(
            f"/api/exports/reimbursement-preview/{batch_with_invoices.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        item_dict = {i["expense_item"]: i["amount"] for i in data["items"]}
        assert item_dict["交通费"] == 218.00
        assert item_dict["餐饮费"] == 300.00