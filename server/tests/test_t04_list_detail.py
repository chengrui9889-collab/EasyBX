from datetime import date
from io import BytesIO

from app.models.invoice import Invoice
from app.models.user import User
from app.services.auth_service import create_access_token, hash_password


class TestListInvoices:
    def test_list_returns_all_own_invoices(self, db, client, auth_headers):
        for i in range(3):
            content = BytesIO(b"content")
            files = [("files", (f"invoice-{i}.jpg", content, "image/jpeg"))]
            client.post("/api/invoices/", files=files, headers=auth_headers)

        response = client.get("/api/invoices/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3

    def test_list_sorted_by_invoice_date_desc(self, db, client, auth_headers):
        dates = [date(2026, 5, 1), date(2026, 5, 10), date(2026, 5, 5)]
        for d in dates:
            invoice = Invoice(
                user_id=1,
                file_path=f"/tmp/{d}.jpg",
                invoice_date=d,
            )
            db.add(invoice)
        db.commit()

        response = client.get("/api/invoices/", headers=auth_headers)
        items = response.json()["items"]
        assert len(items) >= 3
        own_items = [i for i in items if i["invoice_date"] is not None]
        if len(own_items) >= 2:
            for j in range(len(own_items) - 1):
                assert own_items[j]["invoice_date"] >= own_items[j + 1]["invoice_date"]

    def test_list_pagination_structure(self, db, client, auth_headers):
        for i in range(5):
            invoice = Invoice(user_id=1, file_path=f"/tmp/{i}.jpg")
            db.add(invoice)
        db.commit()

        response = client.get("/api/invoices/?page=1&page_size=20", headers=auth_headers)
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total_pages"] >= 1

    def test_list_filter_by_state(self, db, client, auth_headers):
        for _ in range(2):
            invoice = Invoice(user_id=1, file_path="/tmp/p.jpg", status="pending")
            db.add(invoice)
        for _ in range(3):
            invoice = Invoice(user_id=1, file_path="/tmp/pr.jpg", status="processing")
            db.add(invoice)
        db.commit()

        response = client.get("/api/invoices/?state=processing", headers=auth_headers)
        items = response.json()["items"]
        assert all(i["status"] == "processing" for i in items)

        response2 = client.get("/api/invoices/?state=pending", headers=auth_headers)
        items2 = response2.json()["items"]
        assert all(i["status"] == "pending" for i in items2)

    def test_list_page_size_100_and_200(self, db, client, auth_headers):
        for i in range(5):
            invoice = Invoice(user_id=1, file_path=f"/tmp/{i}.jpg")
            db.add(invoice)
        db.commit()

        r1 = client.get("/api/invoices/?page_size=100", headers=auth_headers)
        assert r1.status_code == 200

        r2 = client.get("/api/invoices/?page_size=200", headers=auth_headers)
        assert r2.status_code == 200

    def test_list_invalid_page_size_returns_422(self, db, client, auth_headers):
        response = client.get("/api/invoices/?page_size=15", headers=auth_headers)
        assert response.status_code == 422

    def test_list_only_returns_own_invoices(self, db, client, auth_headers):
        other_user = User(
            username="other",
            password_hash=hash_password("pass"),
            display_name="Other",
        )
        db.add(other_user)
        db.commit()

        invoice_a = Invoice(user_id=1, file_path="/tmp/a.jpg")
        invoice_b = Invoice(user_id=other_user.id, file_path="/tmp/b.jpg")
        db.add_all([invoice_a, invoice_b])
        db.commit()

        response = client.get("/api/invoices/", headers=auth_headers)
        items = response.json()["items"]
        assert all(i["user_id"] == 1 for i in items)

    def test_list_without_token_returns_401(self, client):
        response = client.get("/api/invoices/")
        assert response.status_code == 401


class TestGetInvoiceDetail:
    def test_get_detail_returns_full_fields(self, db, client, auth_headers):
        content = BytesIO(b"fake")
        files = [("files", ("detail.jpg", content, "image/jpeg"))]
        upload_resp = client.post("/api/invoices/", files=files, headers=auth_headers)
        invoice_id = upload_resp.json()["results"][0]["invoice_id"]

        response = client.get(f"/api/invoices/{invoice_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == invoice_id
        assert data["file_original_name"] == "detail.jpg"
        assert "status" in data

    def test_get_detail_other_user_returns_404(self, db, client, auth_headers):
        other_user = User(
            username="other2",
            password_hash=hash_password("pass"),
            display_name="Other2",
        )
        db.add(other_user)
        db.commit()

        other_token = create_access_token(other_user.id)
        other_headers = {"Authorization": f"Bearer {other_token}"}

        content = BytesIO(b"fake")
        files = [("files", ("mine.jpg", content, "image/jpeg"))]
        upload_resp = client.post("/api/invoices/", files=files, headers=auth_headers)
        invoice_id = upload_resp.json()["results"][0]["invoice_id"]

        response = client.get(f"/api/invoices/{invoice_id}", headers=other_headers)
        assert response.status_code == 404


class TestGetInvoiceFile:
    def test_get_file_returns_200_with_correct_content_type(self, db, client, auth_headers):
        content = BytesIO(b"image-content")
        files = [("files", ("file.jpg", content, "image/jpeg"))]
        upload_resp = client.post("/api/invoices/", files=files, headers=auth_headers)
        invoice_id = upload_resp.json()["results"][0]["invoice_id"]

        response = client.get(f"/api/invoices/{invoice_id}/file", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] in ("image/jpeg", "image/jpg", "application/octet-stream")

    def test_get_file_other_user_returns_404(self, db, client, auth_headers):
        other_user = User(
            username="other3",
            password_hash=hash_password("pass"),
            display_name="Other3",
        )
        db.add(other_user)
        db.commit()

        other_token = create_access_token(other_user.id)
        other_headers = {"Authorization": f"Bearer {other_token}"}

        content = BytesIO(b"fake")
        files = [("files", ("mine2.jpg", content, "image/jpeg"))]
        upload_resp = client.post("/api/invoices/", files=files, headers=auth_headers)
        invoice_id = upload_resp.json()["results"][0]["invoice_id"]

        response = client.get(f"/api/invoices/{invoice_id}/file", headers=other_headers)
        assert response.status_code == 404
