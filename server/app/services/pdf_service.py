from io import BytesIO
from pathlib import Path
from typing import Optional

import fitz
from PIL import Image as PILImage
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4, landscape as A4_landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.models.invoice import Invoice


def _calc_cell_positions(pw: float, ph: float, layout: str) -> list[tuple[float, float, float, float]]:
    margin = 20.0
    gap = 12.0
    cells: list[tuple[float, float, float, float]] = []

    if layout == "landscape":
        cols = 2
        rows = 2
        cell_w = (pw - 2 * margin - gap * (cols - 1)) / cols
        cell_h = (ph - 2 * margin - gap * (rows - 1)) / rows
        for row in range(rows):
            for col in range(cols):
                x = margin + col * (cell_w + gap)
                y = margin + (rows - 1 - row) * (cell_h + gap)
                cells.append((x, y, cell_w, cell_h))
    else:
        rows = 2
        cell_w = pw - 2 * margin
        cell_h = (ph - 2 * margin - gap * (rows - 1)) / rows
        for row in range(rows):
            x = margin
            y = margin + (rows - 1 - row) * (cell_h + gap)
            cells.append((x, y, cell_w, cell_h))

    return cells


def _fit_inside(img_w: float, img_h: float, cell_w: float, cell_h: float) -> tuple[float, float]:
    scale = min(cell_w / img_w, cell_h / img_h)
    return img_w * scale, img_h * scale


def _draw_placeholder(c: canvas.Canvas, x: float, y: float, cw: float, ch: float) -> None:
    c.setFillColorRGB(0.898, 0.902, 0.922)
    c.rect(x, y, cw, ch, fill=1, stroke=0)
    c.setFillColorRGB(0.612, 0.639, 0.686)
    c.setFont("Helvetica", 12)
    text = "文件不可用"
    tw = c.stringWidth(text, "Helvetica", 12)
    tx = x + (cw - tw) / 2
    ty = y + (ch - 12) / 2
    c.drawString(tx, ty, text)


def _load_invoice_image(file_path: str, upload_dir: Path) -> Optional[PILImage.Image]:
    full_path = Path(file_path)
    if not full_path.exists():
        full_path = upload_dir / file_path
    if not full_path.exists():
        return None

    suffix = full_path.suffix.lower()
    try:
        if suffix == ".pdf":
            reader = PdfReader(str(full_path))
            if len(reader.pages) == 0:
                return None
            page = reader.pages[0]
            temp_buffer = BytesIO()
            writer = PdfWriter()
            writer.add_page(page)
            writer.write(temp_buffer)
            temp_buffer.seek(0)
            doc = fitz.open(stream=temp_buffer, filetype="pdf")
            if len(doc) == 0:
                doc.close()
                return None
            pix = doc[0].get_pixmap(dpi=200)
            img = PILImage.frombytes("RGB", [pix.width, pix.height], pix.samples)
            doc.close()
            return img
        else:
            img = PILImage.open(full_path)
            if img.mode != "RGB":
                img = img.convert("RGB")
            return img
    except Exception:
        return None


def generate_invoice_pdf(
    db: Session,
    invoices: list[Invoice],
    layouts: dict[str, str],
    upload_dir: Path,
) -> bytes:
    groups: dict[str, list[Invoice]] = {}
    for inv in invoices:
        t = inv.invoice_type or "其他"
        groups.setdefault(t, []).append(inv)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    for inv_type, inv_list in groups.items():
        layout = layouts.get(inv_type, "portrait")
        per_page = 2 if layout == "portrait" else 4
        page_size = A4 if layout == "portrait" else A4_landscape(A4)
        c.setPageSize(page_size)
        pw, ph = page_size
        cell_positions = _calc_cell_positions(pw, ph, layout)

        for i, inv in enumerate(inv_list):
            pos_in_page = i % per_page
            if pos_in_page == 0 and i > 0:
                c.showPage()
                c.setPageSize(page_size)

            x, y, cw, ch = cell_positions[pos_in_page]
            img = _load_invoice_image(inv.file_path, upload_dir)

            if img is None:
                _draw_placeholder(c, x, y, cw, ch)
            else:
                scaled_w, scaled_h = _fit_inside(img.width, img.height, cw, ch)
                cx = x + (cw - scaled_w) / 2
                cy = y + (ch - scaled_h) / 2
                c.drawImage(ImageReader(img), cx, cy, scaled_w, scaled_h)
                img.close()

        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer.read()