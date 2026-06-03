import pytest
from pydantic import ValidationError


class TestPdfExportRequest:
    def test_constructs_with_layouts_dict(self):
        from app.schemas.export import PdfExportRequest

        req = PdfExportRequest(
            invoice_ids=[1, 2],
            layouts={"增值税电子发票": "portrait", "高铁票": "landscape"},
        )
        assert req.invoice_ids == [1, 2]
        assert req.layouts == {"增值税电子发票": "portrait", "高铁票": "landscape"}

    def test_layouts_defaults_to_empty_dict(self):
        from app.schemas.export import PdfExportRequest

        req = PdfExportRequest(invoice_ids=[1])
        assert req.layouts == {}

    def test_rejects_invalid_layout_value(self):
        from app.schemas.export import PdfExportRequest

        with pytest.raises(ValidationError):
            PdfExportRequest(invoice_ids=[1], layouts={"xxx": "invalid"})

    def test_accepts_portrait_layout_value(self):
        from app.schemas.export import PdfExportRequest

        req = PdfExportRequest(invoice_ids=[1], layouts={"a": "portrait"})
        assert req.layouts["a"] == "portrait"

    def test_accepts_landscape_layout_value(self):
        from app.schemas.export import PdfExportRequest

        req = PdfExportRequest(invoice_ids=[1], layouts={"a": "landscape"})
        assert req.layouts["a"] == "landscape"

    def test_rejects_missing_invoice_ids(self):
        from app.schemas.export import PdfExportRequest

        with pytest.raises(ValidationError):
            PdfExportRequest()

    def test_layout_field_type_is_dict_str_str(self):
        from app.schemas.export import PdfExportRequest

        req = PdfExportRequest(invoice_ids=[1], layouts={"发票A": "portrait"})
        assert isinstance(req.layouts, dict)
        for k, v in req.layouts.items():
            assert isinstance(k, str)
            assert isinstance(v, str)


class TestBatchPdfExportRequest:
    def test_constructs_with_empty_layouts(self):
        from app.schemas.export import BatchPdfExportRequest

        req = BatchPdfExportRequest(layouts={})
        assert req.layouts == {}

    def test_constructs_with_layouts(self):
        from app.schemas.export import BatchPdfExportRequest

        req = BatchPdfExportRequest(
            layouts={"增值税电子发票": "portrait", "高铁票": "landscape"}
        )
        assert req.layouts["增值税电子发票"] == "portrait"
        assert req.layouts["高铁票"] == "landscape"

    def test_layouts_defaults_to_empty_dict(self):
        from app.schemas.export import BatchPdfExportRequest

        req = BatchPdfExportRequest()
        assert req.layouts == {}

    def test_rejects_invalid_layout_value(self):
        from app.schemas.export import BatchPdfExportRequest

        with pytest.raises(ValidationError):
            BatchPdfExportRequest(layouts={"xxx": "abc"})