import io
from pathlib import Path

import pytest
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image as PILImage

from app.models.invoice import Invoice


def _create_test_pdf(output_path: Path) -> Path:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=A4)
    c.drawString(100, 750, "Test Invoice PDF")
    c.save()
    return output_path


def _create_test_image(output_path: Path, width=800, height=600) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img = PILImage.new("RGB", (width, height), color=(200, 200, 255))
    img.save(str(output_path), "PNG")
    return output_path


def _make_test_invoice(db, user_id, invoice_type, file_path, **kwargs):
    inv = Invoice(
        user_id=user_id,
        file_path=str(file_path),
        invoice_type=invoice_type,
        status="confirmed",
        amount=100.0,
        **kwargs,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


class TestCalcCellPositions:
    def test_portrait_returns_two_cells(self):
        from app.services.pdf_service import _calc_cell_positions

        cells = _calc_cell_positions(595.28, 841.89, "portrait")
        assert len(cells) == 2

    def test_portrait_cell_width_approx_555(self):
        from app.services.pdf_service import _calc_cell_positions

        cells = _calc_cell_positions(595.28, 841.89, "portrait")
        for _, _, cw, _ in cells:
            assert abs(cw - 555.28) < 1.0

    def test_portrait_upper_cell_y_greater_than_lower(self):
        from app.services.pdf_service import _calc_cell_positions

        cells = _calc_cell_positions(595.28, 841.89, "portrait")
        assert cells[0][1] > cells[1][1]

    def test_landscape_returns_four_cells(self):
        from app.services.pdf_service import _calc_cell_positions

        cells = _calc_cell_positions(841.89, 595.28, "landscape")
        assert len(cells) == 4

    def test_landscape_no_overlap(self):
        from app.services.pdf_service import _calc_cell_positions

        cells = _calc_cell_positions(841.89, 595.28, "landscape")
        for i, (x1, y1, w1, h1) in enumerate(cells):
            for j, (x2, y2, w2, h2) in enumerate(cells):
                if i >= j:
                    continue
                overlap_x = x1 < x2 + w2 and x1 + w1 > x2
                overlap_y = y1 < y2 + h2 and y1 + h1 > y2
                assert not (overlap_x and overlap_y), f"cells {i} and {j} overlap"


class TestFitInside:
    def test_equal_aspect_ratio(self):
        from app.services.pdf_service import _fit_inside

        sw, sh = _fit_inside(1000, 1000, 500, 500)
        assert sw == pytest.approx(500.0)
        assert sh == pytest.approx(500.0)

    def test_width_constrained(self):
        from app.services.pdf_service import _fit_inside

        sw, sh = _fit_inside(2000, 1000, 500, 500)
        assert sw == pytest.approx(500.0)
        assert sh == pytest.approx(250.0)

    def test_height_constrained(self):
        from app.services.pdf_service import _fit_inside

        sw, sh = _fit_inside(1000, 2000, 500, 500)
        assert sw == pytest.approx(250.0)
        assert sh == pytest.approx(500.0)

    def test_smaller_than_cell(self):
        from app.services.pdf_service import _fit_inside

        sw, sh = _fit_inside(100, 100, 500, 500)
        assert sw == pytest.approx(500.0)
        assert sh == pytest.approx(500.0)


class TestDrawPlaceholder:
    def test_draws_rectangle_and_text(self, tmp_path):
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        from app.services.pdf_service import _draw_placeholder

        output = tmp_path / "placeholder.pdf"
        c = canvas.Canvas(str(output), pagesize=A4)
        _draw_placeholder(c, 20, 20, 300, 300)
        c.save()

        assert output.exists()
        size = output.stat().st_size
        assert size > 0


class TestLoadInvoiceImage:
    def test_loads_image_file(self, tmp_path):
        from app.services.pdf_service import _load_invoice_image

        img_path = _create_test_image(tmp_path / "test.png")
        img = _load_invoice_image(str(img_path), tmp_path)
        assert img is not None
        assert isinstance(img, PILImage.Image)
        img.close()

    def test_loads_pdf_file(self, tmp_path):
        from app.services.pdf_service import _load_invoice_image

        pdf_path = _create_test_pdf(tmp_path / "test.pdf")
        img = _load_invoice_image(str(pdf_path), tmp_path)
        assert img is not None
        assert isinstance(img, PILImage.Image)
        img.close()

    def test_returns_none_for_missing_file(self, tmp_path):
        from app.services.pdf_service import _load_invoice_image

        img = _load_invoice_image(str(tmp_path / "nonexistent.pdf"), tmp_path)
        assert img is None

    def test_file_path_already_contains_upload_dir(self, tmp_path):
        from app.services.pdf_service import _load_invoice_image

        img = _create_test_image(tmp_path / "1" / "abc123_test.png")
        full_path_str = str(img)
        img_loaded = _load_invoice_image(full_path_str, tmp_path)
        assert img_loaded is not None
        assert isinstance(img_loaded, PILImage.Image)
        img_loaded.close()


class TestGenerateInvoicePdf:
    def test_two_portrait_single_page(self, db, tmp_path):
        from app.services.pdf_service import generate_invoice_pdf

        user_id = 1
        img1 = _create_test_image(tmp_path / "invoice1.png")
        img2 = _create_test_image(tmp_path / "invoice2.png")
        inv1 = _make_test_invoice(db, user_id, "增值税电子发票", img1)
        inv2 = _make_test_invoice(db, user_id, "增值税电子发票", img2)

        pdf_bytes = generate_invoice_pdf(
            db, [inv1, inv2], {"增值税电子发票": "portrait"}, tmp_path
        )
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

        reader = PdfReader(io.BytesIO(pdf_bytes))
        assert len(reader.pages) == 1

    def test_three_portrait_two_pages(self, db, tmp_path):
        from app.services.pdf_service import generate_invoice_pdf

        user_id = 1
        invoices = []
        for i in range(3):
            img = _create_test_image(tmp_path / f"inv{i}.png")
            invoices.append(_make_test_invoice(db, user_id, "增值税电子发票", img))

        pdf_bytes = generate_invoice_pdf(
            db, [invoices[0], invoices[1], invoices[2]],
            {"增值税电子发票": "portrait"}, tmp_path
        )
        reader = PdfReader(io.BytesIO(pdf_bytes))
        assert len(reader.pages) == 2

    def test_four_landscape_single_page(self, db, tmp_path):
        from app.services.pdf_service import generate_invoice_pdf

        user_id = 1
        invoices = []
        for i in range(4):
            img = _create_test_image(tmp_path / f"inv{i}.png")
            invoices.append(_make_test_invoice(db, user_id, "高铁票", img))

        pdf_bytes = generate_invoice_pdf(
            db, invoices, {"高铁票": "landscape"}, tmp_path
        )
        reader = PdfReader(io.BytesIO(pdf_bytes))
        assert len(reader.pages) == 1

    def test_five_landscape_two_pages(self, db, tmp_path):
        from app.services.pdf_service import generate_invoice_pdf

        user_id = 1
        invoices = []
        for i in range(5):
            img = _create_test_image(tmp_path / f"inv{i}.png")
            invoices.append(_make_test_invoice(db, user_id, "高铁票", img))

        pdf_bytes = generate_invoice_pdf(
            db, invoices, {"高铁票": "landscape"}, tmp_path
        )
        reader = PdfReader(io.BytesIO(pdf_bytes))
        assert len(reader.pages) == 2

    def test_mixed_types_no_mixing(self, db, tmp_path):
        from app.services.pdf_service import generate_invoice_pdf

        user_id = 1
        inv_type_a = []
        inv_type_b = []
        for i in range(2):
            img = _create_test_image(tmp_path / f"a{i}.png")
            inv_type_a.append(_make_test_invoice(db, user_id, "增值税电子发票", img))
        for i in range(2):
            img = _create_test_image(tmp_path / f"b{i}.png")
            inv_type_b.append(_make_test_invoice(db, user_id, "高铁票", img))

        all_invoices = inv_type_a + inv_type_b
        pdf_bytes = generate_invoice_pdf(
            db, all_invoices,
            {"增值税电子发票": "portrait", "高铁票": "landscape"},
            tmp_path,
        )
        reader = PdfReader(io.BytesIO(pdf_bytes))
        assert len(reader.pages) == 2

    def test_single_invoice(self, db, tmp_path):
        from app.services.pdf_service import generate_invoice_pdf

        user_id = 1
        img = _create_test_image(tmp_path / "single.png")
        inv = _make_test_invoice(db, user_id, "增值税电子发票", img)

        pdf_bytes = generate_invoice_pdf(
            db, [inv], {"增值税电子发票": "portrait"}, tmp_path
        )
        reader = PdfReader(io.BytesIO(pdf_bytes))
        assert len(reader.pages) == 1

    def test_missing_file_shows_placeholder(self, db, tmp_path):
        from app.services.pdf_service import generate_invoice_pdf

        user_id = 1
        img = _create_test_image(tmp_path / "good.png")
        inv1 = _make_test_invoice(db, user_id, "增值税电子发票", img)
        inv2 = _make_test_invoice(
            db, user_id, "增值税电子发票",
            tmp_path / "does_not_exist.pdf"
        )

        pdf_bytes = generate_invoice_pdf(
            db, [inv1, inv2], {"增值税电子发票": "portrait"}, tmp_path
        )
        reader = PdfReader(io.BytesIO(pdf_bytes))
        assert len(reader.pages) == 1

    def test_no_headers_or_page_numbers(self, db, tmp_path):
        from app.services.pdf_service import generate_invoice_pdf

        user_id = 1
        img = _create_test_image(tmp_path / "noheader.png")
        inv = _make_test_invoice(db, user_id, "增值税电子发票", img)

        pdf_bytes = generate_invoice_pdf(
            db, [inv], {}, tmp_path
        )
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    def test_null_invoice_type_uses_other(self, db, tmp_path):
        from app.services.pdf_service import generate_invoice_pdf

        user_id = 1
        img = _create_test_image(tmp_path / "nulltype.png")
        inv = _make_test_invoice(db, user_id, None, img)

        pdf_bytes = generate_invoice_pdf(
            db, [inv], {}, tmp_path
        )
        reader = PdfReader(io.BytesIO(pdf_bytes))
        assert len(reader.pages) == 1