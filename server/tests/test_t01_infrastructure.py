
from app.config import settings
from app.models.invoice import Invoice


class TestInvoiceModel:
    def test_status_default_processing(self, db):
        invoice = Invoice(
            user_id=1,
            file_path="/tmp/test.jpg",
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        assert invoice.status == "processing"

    def test_file_original_name_readable_writable(self, db):
        invoice = Invoice(
            user_id=1,
            file_path="/tmp/test.jpg",
            file_original_name="测试发票.jpg",
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        assert invoice.file_original_name == "测试发票.jpg"

    def test_deleted_at_defaults_none(self, db):
        invoice = Invoice(
            user_id=1,
            file_path="/tmp/test.jpg",
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        assert invoice.deleted_at is None

    def test_all_new_fields_writable(self, db):
        invoice = Invoice(
            user_id=1,
            file_path="/tmp/test.jpg",
            file_original_name="发票.jpg",
            buyer_name="测试购买方",
            invoice_type="增值税电子普通发票",
            project_name="咨询服务",
            train_no="G1234",
            departure_station="北京南",
            arrival_station="上海虹桥",
            departure_location="北京市朝阳区",
            arrival_location="上海市浦东新区",
            flight_no="CA1234",
            departure_city="北京",
            arrival_city="上海",
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        assert invoice.buyer_name == "测试购买方"
        assert invoice.invoice_type == "增值税电子普通发票"
        assert invoice.project_name == "咨询服务"
        assert invoice.train_no == "G1234"
        assert invoice.departure_station == "北京南"
        assert invoice.arrival_station == "上海虹桥"
        assert invoice.departure_location == "北京市朝阳区"
        assert invoice.arrival_location == "上海市浦东新区"
        assert invoice.flight_no == "CA1234"
        assert invoice.departure_city == "北京"
        assert invoice.arrival_city == "上海"

    def test_new_fields_nullable(self, db):
        invoice = Invoice(
            user_id=1,
            file_path="/tmp/test.jpg",
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        assert invoice.buyer_name is None
        assert invoice.invoice_type is None
        assert invoice.project_name is None
        assert invoice.train_no is None
        assert invoice.departure_station is None
        assert invoice.arrival_station is None
        assert invoice.departure_location is None
        assert invoice.arrival_location is None
        assert invoice.flight_no is None
        assert invoice.departure_city is None
        assert invoice.arrival_city is None
        assert invoice.file_original_name is None


class TestInvoiceSchema:
    def test_invoice_response_contains_user_id(self, db):
        from app.schemas.invoice import InvoiceResponse

        invoice = Invoice(
            user_id=1,
            file_path="/tmp/test.jpg",
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        response = InvoiceResponse.model_validate(invoice)
        assert response.user_id == 1

    def test_invoice_response_contains_all_new_fields(self, db):
        from app.schemas.invoice import InvoiceResponse

        invoice = Invoice(
            user_id=1,
            file_path="/tmp/test.jpg",
            file_original_name="test.jpg",
            buyer_name="买方",
            invoice_type="增值税",
            project_name="项目",
            train_no="G1",
            departure_station="出发站",
            arrival_station="到达站",
            departure_location="出发地",
            arrival_location="到达地",
            flight_no="CA1",
            departure_city="出发城",
            arrival_city="到达城",
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        response = InvoiceResponse.model_validate(invoice)
        assert response.file_original_name == "test.jpg"
        assert response.buyer_name == "买方"
        assert response.invoice_type == "增值税"
        assert response.project_name == "项目"
        assert response.train_no == "G1"
        assert response.departure_station == "出发站"
        assert response.arrival_station == "到达站"
        assert response.departure_location == "出发地"
        assert response.arrival_location == "到达地"
        assert response.flight_no == "CA1"
        assert response.departure_city == "出发城"
        assert response.arrival_city == "到达城"

    def test_upload_file_result_schema(self):
        from app.schemas.invoice import UploadFileResult

        result = UploadFileResult(filename="test.jpg", success=True, invoice_id=1)
        assert result.filename == "test.jpg"
        assert result.success is True
        assert result.invoice_id == 1
        assert result.error is None

        fail_result = UploadFileResult(filename="bad.doc", success=False, error="不支持的文件格式")
        assert fail_result.error == "不支持的文件格式"
        assert fail_result.invoice_id is None

    def test_upload_response_schema(self):
        from app.schemas.invoice import UploadFileResult, UploadResponse

        results = [
            UploadFileResult(filename="a.jpg", success=True, invoice_id=1),
            UploadFileResult(filename="b.doc", success=False, error="不支持的文件格式"),
        ]
        response = UploadResponse(results=results, skipped_count=3)
        assert len(response.results) == 2
        assert response.skipped_count == 3

    def test_invoice_list_response_schema(self, db):
        from app.schemas.invoice import InvoiceListResponse, InvoiceResponse

        invoice = Invoice(user_id=1, file_path="/tmp/test.jpg")
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        items = [InvoiceResponse.model_validate(invoice)]
        response = InvoiceListResponse(
            items=items,
            total=1,
            page=1,
            page_size=20,
            total_pages=1,
        )
        assert response.total == 1
        assert response.page == 1
        assert response.page_size == 20
        assert response.total_pages == 1


class TestConfig:
    def test_max_upload_size_mb_is_50(self):
        assert settings.max_upload_size_mb == 50

    def test_max_upload_size_bytes_correct(self):
        assert settings.max_upload_size_bytes == 50 * 1024 * 1024

    def test_ocr_max_workers(self):
        assert settings.ocr_max_workers == 2

    def test_ocr_timeout_seconds(self):
        assert settings.ocr_timeout_seconds == 120


class TestAPIHealthCheck:
    def test_invoice_list_returns_200(self, client, auth_headers):
        response = client.get("/api/invoices/", headers=auth_headers)
        assert response.status_code == 200
