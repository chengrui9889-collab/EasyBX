import time
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from app.models.invoice import Invoice


class TestOcrSuccess:
    def test_ocr_success_sets_state_to_pending(self, db, client, auth_headers):
        content = BytesIO(b"fake-image")
        files = [("files", ("invoice.jpg", content, "image/jpeg"))]
        response = client.post("/api/invoices/", files=files, headers=auth_headers)
        assert response.status_code == 200
        invoice_id = response.json()["results"][0]["invoice_id"]

        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        assert invoice.status == "processing"

        with patch("app.services.ocr_service._call_paddleocr") as mock_ocr:
            mock_ocr.return_value = "发票号码: 12345678 开票日期: 2025-06-15 金额: ¥156.80 销售方: 测试公司"

            from app.services.ocr_service import _run_ocr_inline
            _run_ocr_inline(invoice_id, invoice.file_path, db)

        db.refresh(invoice)
        assert invoice.status == "pending"
        assert invoice.amount == 156.80
        assert str(invoice.invoice_date) == "2025-06-15"
        assert invoice.ocr_raw_data is not None

    def test_ocr_no_fields_sets_failed(self, db, client, auth_headers):
        content = BytesIO(b"fake-image")
        files = [("files", ("invoice.jpg", content, "image/jpeg"))]
        response = client.post("/api/invoices/", files=files, headers=auth_headers)
        invoice_id = response.json()["results"][0]["invoice_id"]

        with patch("app.services.ocr_service._call_paddleocr") as mock_ocr:
            mock_ocr.return_value = "这是一张模糊的图片，什么都看不清"

            from app.services.ocr_service import _run_ocr_inline
            _run_ocr_inline(invoice_id, str(Path("test.jpg")), db)

        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        assert invoice.status == "failed"


class TestOcrError:
    def test_ocr_exception_sets_failed(self, db, client, auth_headers):
        content = BytesIO(b"fake-image")
        files = [("files", ("invoice.jpg", content, "image/jpeg"))]
        response = client.post("/api/invoices/", files=files, headers=auth_headers)
        invoice_id = response.json()["results"][0]["invoice_id"]

        with patch("app.services.ocr_service._call_paddleocr") as mock_ocr:
            mock_ocr.side_effect = RuntimeError("PaddleOCR crashed")

            from app.services.ocr_service import _run_ocr_inline
            _run_ocr_inline(invoice_id, str(Path("test.jpg")), db)

        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        assert invoice.status == "failed"
        assert invoice.remark is not None and "PaddleOCR crashed" in invoice.remark

    def test_ocr_timeout_sets_failed(self, db, client, auth_headers):
        content = BytesIO(b"fake-image")
        files = [("files", ("invoice.jpg", content, "image/jpeg"))]
        response = client.post("/api/invoices/", files=files, headers=auth_headers)
        invoice_id = response.json()["results"][0]["invoice_id"]

        original_timeout = None
        try:
            from app.config import settings as cfg
            original_timeout = cfg.ocr_timeout_seconds

            with patch("app.services.ocr_service._call_paddleocr") as mock_ocr:
                import app.services.ocr_service as ocr_mod
                ocr_mod.OCR_TIMEOUT = 0.1

                def slow_ocr(*args, **kwargs):
                    time.sleep(0.5)
                    return "result"

                mock_ocr.side_effect = slow_ocr

                from app.services.ocr_service import _run_ocr_inline
                _run_ocr_inline(invoice_id, str(Path("test.jpg")), db)

            invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
            assert invoice.status == "failed"
            assert invoice.remark is not None and "超时" in invoice.remark
        finally:
            if original_timeout is not None:
                import app.services.ocr_service as ocr_mod
                ocr_mod.OCR_TIMEOUT = original_timeout


class TestOcrIntegration:
    def test_upload_triggers_ocr_processing_then_pending(self, db, client, auth_headers):
        with patch("app.services.ocr_service._call_paddleocr") as mock_ocr:
            mock_ocr.return_value = "发票号码: 9999 开票日期: 2026-01-01 金额: ¥99.00"

            content = BytesIO(b"fake-image")
            files = [("files", ("invoice.jpg", content, "image/jpeg"))]
            response = client.post("/api/invoices/", files=files, headers=auth_headers)
            assert response.status_code == 200
            invoice_id = response.json()["results"][0]["invoice_id"]

            from app.services.ocr_service import _run_ocr_inline
            invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
            _run_ocr_inline(invoice_id, invoice.file_path, db)

            db.refresh(invoice)
            assert invoice.status == "pending"
            assert invoice.amount == 99.00

    def test_upload_ocr_failure_sets_failed_background(self, db, client, auth_headers):
        with patch("app.services.ocr_service._call_paddleocr") as mock_ocr:
            mock_ocr.side_effect = RuntimeError("OCR failure")

            content = BytesIO(b"fake-image")
            files = [("files", ("invoice.jpg", content, "image/jpeg"))]
            response = client.post("/api/invoices/", files=files, headers=auth_headers)
            assert response.status_code == 200
            invoice_id = response.json()["results"][0]["invoice_id"]

            from app.services.ocr_service import _run_ocr_inline
            invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
            _run_ocr_inline(invoice_id, invoice.file_path, db)

            db.refresh(invoice)
            assert invoice.status == "failed"
