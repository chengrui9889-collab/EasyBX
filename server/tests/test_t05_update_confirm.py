from datetime import date
from io import BytesIO

from app.models.invoice import Invoice
from app.models.user import User
from app.services.auth_service import create_access_token, hash_password


def _upload_one(client, auth_headers):
    files = [("files", ("test.jpg", BytesIO(b"content"), "image/jpeg"))]
    resp = client.post("/api/invoices/", files=files, headers=auth_headers)
    return resp.json()["results"][0]["invoice_id"]


class TestUpdateInvoice:
    def test_update_pending_invoice_amount(self, db, client, auth_headers):
        invoice_id = _upload_one(client, auth_headers)
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        invoice.status = "pending"
        db.commit()

        payload = {"amount": 100.0}
        response = client.put(f"/api/invoices/{invoice_id}", json=payload, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["amount"] == 100.0

    def test_update_failed_invoice_vendor(self, db, client, auth_headers):
        invoice_id = _upload_one(client, auth_headers)
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        invoice.status = "failed"
        db.commit()

        payload = {"vendor": "测试公司"}
        response = client.put(f"/api/invoices/{invoice_id}", json=payload, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["vendor"] == "测试公司"

    def test_update_processing_invoice_returns_400(self, db, client, auth_headers):
        invoice_id = _upload_one(client, auth_headers)
        payload = {"amount": 100.0}
        response = client.put(f"/api/invoices/{invoice_id}", json=payload, headers=auth_headers)
        assert response.status_code == 400

    def test_update_confirmed_invoice_succeeds(self, db, client, auth_headers):
        invoice_id = _upload_one(client, auth_headers)
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        invoice.status = "confirmed"
        db.commit()

        payload = {"amount": 100.0}
        response = client.put(f"/api/invoices/{invoice_id}", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "confirmed"
        assert float(data["amount"]) == 100.0

    def test_update_other_user_invoice_returns_404(self, db, client, auth_headers):
        other_user = User(username="t05other", password_hash=hash_password("pass"), display_name="O")
        db.add(other_user)
        db.commit()
        other_headers = {"Authorization": f"Bearer {create_access_token(other_user.id)}"}

        invoice_id = _upload_one(client, auth_headers)
        response = client.put(f"/api/invoices/{invoice_id}", json={"amount": 100}, headers=other_headers)
        assert response.status_code == 404

    def test_update_without_token_returns_401(self, client):
        response = client.put("/api/invoices/1", json={"amount": 100})
        assert response.status_code == 401


class TestConfirmInvoice:
    def test_confirm_updates_state_to_confirmed(self, db, client, auth_headers):
        invoice = Invoice(
            user_id=1, file_path="/tmp/c.jpg", status="pending",
            invoice_date=date(2026, 5, 10), amount=200.0,
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        response = client.post(f"/api/invoices/{invoice.id}/confirm", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "confirmed"

    def test_confirm_updates_updated_at(self, db, client, auth_headers):
        invoice = Invoice(
            user_id=1, file_path="/tmp/d.jpg", status="pending",
            invoice_date=date(2026, 5, 10), amount=200.0,
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        old_updated_at = invoice.updated_at

        response = client.post(f"/api/invoices/{invoice.id}/confirm", headers=auth_headers)
        assert response.status_code == 200

        db.refresh(invoice)
        assert invoice.updated_at >= old_updated_at

    def test_confirm_without_date_returns_422(self, db, client, auth_headers):
        invoice = Invoice(user_id=1, file_path="/tmp/e.jpg", status="pending", amount=200.0)
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        response = client.post(f"/api/invoices/{invoice.id}/confirm", headers=auth_headers)
        assert response.status_code == 422

    def test_confirm_without_amount_returns_422(self, db, client, auth_headers):
        invoice = Invoice(
            user_id=1, file_path="/tmp/f.jpg", status="pending",
            invoice_date=date(2026, 5, 10), amount=None,
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        response = client.post(f"/api/invoices/{invoice.id}/confirm", headers=auth_headers)
        assert response.status_code == 422

    def test_confirm_with_zero_amount_returns_422(self, db, client, auth_headers):
        invoice = Invoice(
            user_id=1, file_path="/tmp/g.jpg", status="pending",
            invoice_date=date(2026, 5, 10), amount=0.0,
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        response = client.post(f"/api/invoices/{invoice.id}/confirm", headers=auth_headers)
        assert response.status_code == 422

    def test_confirm_processing_invoice_returns_400(self, db, client, auth_headers):
        invoice = Invoice(
            user_id=1, file_path="/tmp/h.jpg", status="processing",
            invoice_date=date(2026, 5, 10), amount=200.0,
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        response = client.post(f"/api/invoices/{invoice.id}/confirm", headers=auth_headers)
        assert response.status_code == 400

    def test_confirm_already_confirmed_succeeds(self, db, client, auth_headers):
        invoice = Invoice(
            user_id=1, file_path="/tmp/i.jpg", status="confirmed",
            invoice_date=date(2026, 5, 10), amount=200.0,
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        response = client.post(f"/api/invoices/{invoice.id}/confirm", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "confirmed"