import concurrent.futures
import logging
import re
from datetime import date

from app.config import settings
from app.models.invoice import Invoice

logger = logging.getLogger(__name__)

OCR_TIMEOUT = settings.ocr_timeout_seconds


def _call_paddleocr(file_path: str) -> str:
    try:
        from paddleocr import PaddleOCR
    except ImportError:
        logger.warning("PaddleOCR 未安装，OCR 功能不可用")
        return ""
    try:
        ocr = PaddleOCR(use_angle_cls=True, lang="ch")
    except Exception as e:
        logger.error(f"PaddleOCR 初始化失败: {e}")
        return ""
    try:
        result = ocr.predict(file_path)
    except Exception as e:
        logger.error(f"PaddleOCR 识别失败: {e}")
        return ""
    if not result:
        return ""
    all_lines = []
    for page in result:
        page_data = page.json if isinstance(page.json, dict) else {}
        res = page_data.get("res", {})
        rec_texts = res.get("rec_texts", [])
        all_lines.extend(rec_texts)
    return "\n".join(all_lines)


def _infer_category(invoice_type: str | None, project_name: str | None) -> str:
    if invoice_type in ("高铁", "飞机"):
        return "交通费"
    if invoice_type == "滴滴":
        return "打车费"
    if invoice_type and "增值税" in invoice_type:
        pn = (project_name or "").lower()
        if any(kw in pn for kw in ("住宿", "酒店", "宾馆", "旅店")):
            return "住宿费"
        if any(kw in pn for kw in ("打印", "复印", "印刷")):
            return "打印费"
        if any(kw in pn for kw in ("餐饮", "食品", "餐费", "外卖")):
            return "餐饮费"
        if any(kw in pn for kw in ("办公", "文具", "耗材")):
            return "办公费"
        if any(kw in pn for kw in ("快递", "物流", "运输")):
            return "快递费"
        return "办公费"
    return "办公费"


def _extract_fields(ocr_text: str) -> dict:
    fields: dict = {}

    amounts = re.findall(r"[¥￥元]\s*([\d,]+\.?\d*)", ocr_text)
    if amounts:
        parsed = []
        for a in amounts:
            try:
                parsed.append(float(a.replace(",", "")))
            except ValueError:
                pass
        if parsed:
            fields["amount"] = max(parsed)

    dates = re.findall(r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)", ocr_text)
    if dates:
        raw = dates[0]
        raw = raw.replace("年", "-").replace("月", "-").replace("日", "")
        try:
            parts = raw.replace("/", "-").split("-")
            fields["invoice_date"] = date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            pass

    invoice_no_match = re.search(r"(?:发票号码|发票号)[：:]\s*(\d{6,20})", ocr_text)
    if invoice_no_match:
        fields["invoice_no"] = invoice_no_match.group(1).strip()
    else:
        invoice_nos = re.findall(r"(?<!\d)(\d{8,20})(?!\d)", ocr_text)
        if invoice_nos:
            longest = max(invoice_nos, key=len)
            fields["invoice_no"] = longest

    if "铁路电子客票" in ocr_text:
        fields["invoice_type"] = "高铁"
        fields["vendor"] = "中国国家铁路集团有限公司"

        dep_match = re.search(r"(\S{2,8})站", ocr_text)
        if dep_match:
            fields["departure_station"] = dep_match.group(1)

        arr_match = re.search(r"(\S{2,8})\n([GCDZ]\d+)\n站", ocr_text)
        if arr_match:
            fields["arrival_station"] = arr_match.group(1)

        train_no_match = re.search(r"([GCDZ]\d+)", ocr_text)
        if train_no_match:
            fields["train_no"] = train_no_match.group(1)

        buyer_match = re.search(r"购买方名称[：:]\s*(.+)$", ocr_text, re.M)
        if buyer_match:
            fields["buyer_name"] = buyer_match.group(1).strip()

        dep = fields.get("departure_station", "")
        arr = fields.get("arrival_station", "")
        if dep and arr:
            fields["project_name"] = f"铁路电子客票 {dep}站--{arr}站"

        return fields

    vendor_match = re.search(r"(?:销售方|销售方名称)\s*[：:]\s*(.+)$", ocr_text, re.M)
    if vendor_match:
        fields["vendor"] = vendor_match.group(1).strip()
    else:
        name_matches = list(re.finditer(r"(?:名称)\s*[：:]\s*(.+)$", ocr_text, re.M))
        if name_matches:
            fields["vendor"] = name_matches[-1].group(1).strip()

    if "增值税" in ocr_text:
        fields["invoice_type"] = "增值税电子普通发票"

    project_section = ocr_text.split("项目名称")[-1] if "项目名称" in ocr_text else ocr_text
    project_match = re.search(r"\*([^*]+?)\*", project_section)
    if project_match:
        project_name = project_match.group(1).strip()
        if len(project_name) <= 20:
            fields["project_name"] = project_name

    return fields


def _do_ocr(invoice_id: int, file_path: str, db_session):
    from app.database import SessionLocal

    if db_session is not None:
        db = db_session
    else:
        db = SessionLocal()
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return

        try:
            ocr_text = _call_paddleocr(file_path)
        except Exception as e:
            invoice.status = "failed"
            invoice.remark = str(e)
            db.commit()
            return

        invoice.ocr_raw_data = {"raw_text": ocr_text}

        fields = _extract_fields(ocr_text)

        if not fields:
            invoice.status = "failed"
            invoice.remark = "图片质量过低，无法识别"
        else:
            fields["category"] = _infer_category(
                fields.get("invoice_type"), fields.get("project_name")
            )
            invoice.status = "pending"
            for key, value in fields.items():
                setattr(invoice, key, value)

        db.commit()
    finally:
        if db_session is None:
            db.close()


def _run_ocr_inline(invoice_id: int, file_path: str, db):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        return

    def _run_ocr_call():
        return _call_paddleocr(file_path)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run_ocr_call)
        try:
            ocr_text = future.result(timeout=OCR_TIMEOUT)
        except concurrent.futures.TimeoutError:
            invoice.status = "failed"
            invoice.remark = "OCR 识别超时"
            db.commit()
            return
        except Exception as e:
            invoice.status = "failed"
            invoice.remark = str(e)
            db.commit()
            return

    try:
        invoice.ocr_raw_data = {"raw_text": ocr_text}
        fields = _extract_fields(ocr_text)

        if not fields:
            invoice.status = "failed"
            invoice.remark = "图片质量过低，无法识别"
        else:
            fields["category"] = _infer_category(
                fields.get("invoice_type"), fields.get("project_name")
            )
            invoice.status = "pending"
            for key, value in fields.items():
                setattr(invoice, key, value)

        db.commit()
    except Exception as e:
        invoice.status = "failed"
        invoice.remark = str(e)
        db.commit()


class OcrTaskManager:
    def __init__(self, max_workers: int = 2):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def submit_task(self, invoice_id: int, file_path: str, session_factory):
        self.executor.submit(_do_ocr, invoice_id, file_path, session_factory)

    def shutdown(self, wait: bool = True):
        self.executor.shutdown(wait=wait)
