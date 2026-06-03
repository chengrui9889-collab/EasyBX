from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path

from app.models.invoice import Invoice
from app.models.user import User
from app.services.auth_service import create_access_token, hash_password


def _upload_one(client, auth_headers):
    files = [("files", ("test.jpg", BytesIO(b"content"), "image/jpeg"))]
    resp = client.post("/api/invoices/", files=files, headers=auth_headers)
    return resp.json()["results"][0]["invoice_id"]


class TestDeleteInvoice:
    def test_delete_processing_invoice_hard(self, db, client, auth_headers):
        invoice_id = _upload_one(client, auth_headers)
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        old_file = invoice.file_path

        response = client.delete(f"/api/invoices/{invoice_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True
        assert data["type"] == "hard"
        assert not Path(old_file).exists()
        db.expire_all()
        assert db.query(Invoice).filter(Invoice.id == invoice_id).first() is None

    def test_delete_pending_invoice_hard(self, db, client, auth_headers):
        invoice_id = _upload_one(client, auth_headers)
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        invoice.status = "pending"
        db.commit()
        old_file = invoice.file_path

        response = client.delete(f"/api/invoices/{invoice_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True
        assert data["type"] == "hard"
        assert not Path(old_file).exists()
        db.expire_all()
        assert db.query(Invoice).filter(Invoice.id == invoice_id).first() is None

    def test_delete_confirmed_invoice_soft(self, db, client, auth_headers):
        invoice_id = _upload_one(client, auth_headers)
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        invoice.status = "confirmed"
        db.commit()
        old_file = invoice.file_path

        response = client.delete(f"/api/invoices/{invoice_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True
        assert data["type"] == "soft"
        assert Path(old_file).exists()

        db.refresh(invoice)
        assert invoice.deleted_at is not None

    def test_delete_without_token_returns_401(self, client):
        response = client.delete("/api/invoices/1")
        assert response.status_code == 401


class TestTrashList:
    def test_trash_contains_soft_deleted(self, db, client, auth_headers):
        invoice_id = _upload_one(client, auth_headers)
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        invoice.status = "confirmed"
        invoice.deleted_at = datetime.now(UTC)
        db.commit()

        response = client.get("/api/invoices/trash", headers=auth_headers)
        assert response.status_code == 200
        item_ids = [item["id"] for item in response.json()["items"]]
        assert invoice_id in item_ids

    def test_trash_excludes_non_deleted(self, db, client, auth_headers):
        _upload_one(client, auth_headers)
        _upload_one(client, auth_headers)

        invoice = Invoice(
            user_id=1, file_path="/tmp/t6.jpg", status="confirmed",
            deleted_at=datetime.now(UTC),
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        response = client.get("/api/invoices/trash", headers=auth_headers)
        assert response.status_code == 200
        item_ids = [item["id"] for item in response.json()["items"]]
        assert invoice.id in item_ids
        assert len(item_ids) == 1


class TestRestoreInvoice:
    def test_restore_soft_deleted_invoice(self, db, client, auth_headers):
        invoice = Invoice(
            user_id=1, file_path="/tmp/r1.jpg", status="confirmed",
            deleted_at=datetime.now(UTC),
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        response = client.post(f"/api/invoices/{invoice.id}/restore", headers=auth_headers)
        assert response.status_code == 200

        db.refresh(invoice)
        assert invoice.deleted_at is None
        assert invoice.status == "confirmed"

    def test_restored_invoice_not_in_trash(self, db, client, auth_headers):
        invoice = Invoice(
            user_id=1, file_path="/tmp/r2.jpg", status="confirmed",
            deleted_at=datetime.now(UTC),
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        client.post(f"/api/invoices/{invoice.id}/restore", headers=auth_headers)

        response = client.get("/api/invoices/trash", headers=auth_headers)
        item_ids = [item["id"] for item in response.json()["items"]]
        assert invoice.id not in item_ids

    def test_restore_other_user_invoice_returns_404(self, db, client, auth_headers):
        other_user = User(username="t6other", password_hash=hash_password("pass"), display_name="O")
        db.add(other_user)
        db.commit()
        other_headers = {"Authorization": f"Bearer {create_access_token(other_user.id)}"}

        invoice = Invoice(
            user_id=1, file_path="/tmp/r3.jpg", status="confirmed",
            deleted_at=datetime.now(UTC),
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        response = client.post(f"/api/invoices/{invoice.id}/restore", headers=other_headers)
        assert response.status_code == 404

    def test_restore_expired_invoice_returns_400(self, db, client, auth_headers):
        invoice = Invoice(
            user_id=1, file_path="/tmp/r4.jpg", status="confirmed",
            deleted_at=datetime.now(UTC) - timedelta(days=31),
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        response = client.post(f"/api/invoices/{invoice.id}/restore", headers=auth_headers)
        assert response.status_code == 400

    def test_restore_non_deleted_invoice_returns_404(self, db, client, auth_headers):
        invoice_id = _upload_one(client, auth_headers)

        response = client.post(f"/api/invoices/{invoice_id}/restore", headers=auth_headers)
        assert response.status_code == 404


class TestCleanupExpired:
    def test_upload_triggers_cleanup_of_expired(self, db, client, auth_headers, tmp_path):
        expired = Invoice(
            user_id=1, file_path=str(tmp_path / "expired.jpg"), status="confirmed",
            deleted_at=datetime.now(UTC) - timedelta(days=31),
        )
        tmp_path.mkdir(parents=True, exist_ok=True)
        with open(expired.file_path, "w") as f:
            f.write("old")
        db.add(expired)
        db.commit()
        db.refresh(expired)
        expired_id = expired.id

        files = [("files", ("new.jpg", BytesIO(b"newcontent"), "image/jpeg"))]
        client.post("/api/invoices/", files=files, headers=auth_headers)

        db.expire_all()
        assert db.query(Invoice).filter(Invoice.id == expired_id).first() is None

    def test_cleanup_deletes_file(self, db, client, auth_headers, tmp_path):
        expired = Invoice(
            user_id=1, file_path=str(tmp_path / "expired2.jpg"), status="confirmed",
            deleted_at=datetime.now(UTC) - timedelta(days=31),
        )
        tmp_path.mkdir(parents=True, exist_ok=True)
        with open(expired.file_path, "w") as f:
            f.write("old")
        db.add(expired)
        db.commit()
        old_file = expired.file_path

        files = [("files", ("new2.jpg", BytesIO(b"newcontent"), "image/jpeg"))]
        client.post("/api/invoices/", files=files, headers=auth_headers)

        assert not Path(old_file).exists()
