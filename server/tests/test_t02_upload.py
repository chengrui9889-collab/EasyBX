from io import BytesIO
from pathlib import Path

from app.config import settings
from app.models.invoice import Invoice
from app.utils.file_utils import generate_storage_path


class TestUploadSingleFile:
    def test_upload_one_valid_jpg(self, client, auth_headers, db):
        content = BytesIO(b"fake-jpeg-content")
        files = [("files", ("test-invoice.jpg", content, "image/jpeg"))]
        response = client.post("/api/invoices/", files=files, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["success"] is True
        assert data["results"][0]["invoice_id"] is not None
        assert data["results"][0]["filename"] == "test-invoice.jpg"

        invoice = db.query(Invoice).filter(Invoice.id == data["results"][0]["invoice_id"]).first()
        assert invoice is not None
        assert invoice.status == "processing"
        assert invoice.file_original_name == "test-invoice.jpg"


class TestUploadMultipleFiles:
    def test_upload_three_valid_files(self, client, auth_headers, db):
        files = [
            ("files", ("a.jpg", BytesIO(b"a-content"), "image/jpeg")),
            ("files", ("b.png", BytesIO(b"b-content"), "image/png")),
            ("files", ("c.pdf", BytesIO(b"c-content"), "application/pdf")),
        ]
        response = client.post("/api/invoices/", files=files, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 3
        assert all(r["success"] for r in data["results"])

        for r in data["results"]:
            invoice = db.query(Invoice).filter(Invoice.id == r["invoice_id"]).first()
            assert invoice is not None
            assert invoice.status == "processing"


class TestFileNaming:
    def test_upload_file_naming_contains_uuid(self, client, auth_headers, db):
        content = BytesIO(b"some-image-data")
        files = [("files", ("test-发票.jpg", content, "image/jpeg"))]
        response = client.post("/api/invoices/", files=files, headers=auth_headers)
        assert response.status_code == 200
        invoice_id = response.json()["results"][0]["invoice_id"]
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        assert invoice is not None
        assert "uuid_" not in invoice.file_path
        assert "test-发票" in invoice.file_path


class TestUnsupportedFormat:
    def test_upload_doc_file_rejected(self, client, auth_headers):
        content = BytesIO(b"document-content")
        files = [("files", ("report.doc", content, "application/msword"))]
        response = client.post("/api/invoices/", files=files, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["success"] is False
        assert "不支持的文件格式" in data["results"][0]["error"]


class TestFileSizeLimit:
    def test_upload_oversized_file_rejected(self, client, auth_headers, monkeypatch):
        original = settings.max_upload_size_bytes
        monkeypatch.setattr(type(settings), "max_upload_size_bytes", 10, raising=False)
        monkeypatch.setattr(type(settings), "max_upload_size_mb", 0, raising=False)
        content = BytesIO(b"x" * 100)
        files = [("files", ("big-file.jpg", content, "image/jpeg"))]
        response = client.post("/api/invoices/", files=files, headers=auth_headers)
        monkeypatch.setattr(type(settings), "max_upload_size_bytes", original, raising=False)
        assert response.status_code == 200
        data = response.json()
        assert data["results"][0]["success"] is False
        assert "大小" in data["results"][0]["error"] or "50" in data["results"][0]["error"] or "MB" in data["results"][0]["error"]


class TestFileCountLimit:
    def test_upload_25_files_truncated_to_20(self, client, auth_headers):
        files = []
        for i in range(25):
            files.append(("files", (f"invoice-{i}.jpg", BytesIO(b"content"), "image/jpeg")))
        response = client.post("/api/invoices/", files=files, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["skipped_count"] == 5
        assert len(data["results"]) == 20


class TestAuth:
    def test_upload_without_token_returns_401(self, client):
        files = [("files", ("invoice.jpg", BytesIO(b"content"), "image/jpeg"))]
        response = client.post("/api/invoices/", files=files)
        assert response.status_code == 401


class TestMixedUpload:
    def test_mixed_valid_and_invalid_files(self, client, auth_headers, monkeypatch):
        original = settings.max_upload_size_bytes
        monkeypatch.setattr(type(settings), "max_upload_size_bytes", 10, raising=False)
        monkeypatch.setattr(type(settings), "max_upload_size_mb", 0, raising=False)

        files = [
            ("files", ("valid1.jpg", BytesIO(b"ok"), "image/jpeg")),
            ("files", ("valid2.png", BytesIO(b"ok"), "image/png")),
            ("files", ("bad.doc", BytesIO(b"doc"), "application/msword")),
            ("files", ("too-big.jpg", BytesIO(b"x" * 100), "image/jpeg")),
        ]
        response = client.post("/api/invoices/", files=files, headers=auth_headers)
        monkeypatch.setattr(type(settings), "max_upload_size_bytes", original, raising=False)

        assert response.status_code == 200
        data = response.json()
        results = {r["filename"]: r for r in data["results"]}

        assert results["valid1.jpg"]["success"] is True
        assert results["valid2.png"]["success"] is True
        assert results["bad.doc"]["success"] is False
        assert "不支持的文件格式" in results["bad.doc"]["error"]
        assert results["too-big.jpg"]["success"] is False
        assert results["too-big.jpg"]["error"] != ""


class TestGenerateStoragePath:
    def test_generate_storage_path_includes_original_name(self):
        path = generate_storage_path(Path("./test_uploads"), user_id=1, original_filename="发票.jpg")
        assert "test_uploads" in path
        assert "发票.jpg" in path
        assert "1" in path
