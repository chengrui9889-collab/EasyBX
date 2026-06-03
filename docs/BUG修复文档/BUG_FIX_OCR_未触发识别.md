# BUG 修复报告：发票内容一直处于"识别中"，OCR 未触发

## 基本信息

| 项目 | 内容 |
|------|------|
| **BUG ID** | BUG-OCR-001 |
| **发现日期** | 2026-05-16 |
| **修复日期** | 2026-05-18 |
| **严重程度** | 🔴 高 — 核心功能完全失效 |
| **影响模块** | 后端 — 发票上传 & OCR 识别 |
| **修复状态** | ✅ 已修复（两轮修复） |

> **修复分为两轮**：第一轮修复了 OcrTaskManager 的接线问题（任务调度链路断连）；第二轮修复了 PaddleOCR 引擎本身的安装、版本对齐和 API 适配问题。

---

## 第一轮修复：OcrTaskManager 接线修复

## 根因分析

### 代码回顾

OCR 识别相关代码分布在 3 个文件中：

**1. OCR 任务管理器已实现** (`server/app/services/ocr_service.py`)

```python
class OcrTaskManager:
    def __init__(self, max_workers: int = 2):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def submit_task(self, invoice_id, file_path, session_factory):
        self.executor.submit(_do_ocr, invoice_id, file_path, session_factory)

    def shutdown(self, wait=True):
        self.executor.shutdown(wait=wait)
```

**2. 上传服务已预留 task_manager 参数** (`server/app/services/invoice_service.py:23-88`)

```python
def upload_batch(
    db, user_id, files, upload_dir,
    task_manager=None,    # ✅ 参数已定义
) -> UploadResponse:
    ...
    if task_manager is not None:
        task_manager.submit_task(invoice.id, storage_path, None)  # ✅ 调用已写好
    ...
```

**3. API 端点未传入 task_manager** (`server/app/api/invoices.py`) — **🔴 断点**

```python
async def upload_invoice(
    files: list[FastAPIUploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # ❌ 没有获取 task_manager 并传给 upload_batch
    return upload_batch(db, current_user.id, files, settings.upload_dir)
```

### 根因总结

`OcrTaskManager` 已完整实现，`upload_batch()` 也已预留 `task_manager` 参数，但 **API 端点从未获取并传递 task_manager**。这导致 `if task_manager is not None:` 分支从未被执行，OCR 从未触发，发票永久停留在 `processing` 状态。

```
                    ┌──────────────────┐
                    │ OcrTaskManager   │   ✅ 已实现
                    │ (ThreadPool)     │
                    └────────┬─────────┘
                             │ submit_task()
                    ┌────────▼─────────┐
                    │ upload_batch()   │   ✅ task_manager 参数已预留
                    │                  │   ✅ if task_manager ... 分支已写好
                    └────────┬─────────┘
                             │ task_manager=???
                    ┌────────▼─────────┐
                    │ upload_invoice() │   🔴 从未获取/传入 task_manager
                    │ (API endpoint)   │   🔴 画了线但没接上！
                    └──────────────────┘
```

## 修复方案

### 修改 1：`server/main.py` — 启动时创建 OcrTaskManager

在应用启动时实例化 `OcrTaskManager` 并挂载到 `app.state`，在关闭时优雅停止线程池：

```python
from app.services.ocr_service import OcrTaskManager

# 模块级创建（受 ocr_enabled 配置控制）
ocr_task_manager = OcrTaskManager(max_workers=settings.ocr_max_workers) if settings.ocr_enabled else None
if ocr_task_manager is not None:
    app.state.ocr_task_manager = ocr_task_manager

@app.on_event("shutdown")
async def shutdown():
    if ocr_task_manager is not None:
        ocr_task_manager.shutdown(wait=False)
```

### 修改 2：`server/app/api/invoices.py` — 端点传入 task_manager

注入 `Request` 对象，从 `app.state` 中获取 `ocr_task_manager` 并传递给 `upload_batch`：

```python
from fastapi import Request

@router.post("/", response_model=UploadResponse)
async def upload_invoice(
    request: Request,                                        # ← 新增：注入 Request
    files: list[FastAPIUploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task_manager = getattr(request.app.state, "ocr_task_manager", None)  # ← 获取
    return upload_batch(db, current_user.id, files, settings.upload_dir,
                        task_manager=task_manager)                        # ← 传入
```

### 修改 3：`server/tests/conftest.py` — 测试环境禁用 OCR

测试中使用 `_run_ocr_inline` 直接调用 OCR，不需要后台线程池。设置 `app.state.ocr_task_manager = None` 确保上传端点不触发异步 OCR：

```python
app.dependency_overrides[get_db] = override_get_db

# 测试中禁用后台 OCR（测试通过 mock 直接调用 _run_ocr_inline）
app.state.ocr_task_manager = None
```

### 修复后的完整链路

```
 ┌─────────────────┐
 │  main.py        │   ✅ startup 时创建 OcrTaskManager
 │  OcrTaskManager │     挂载到 app.state
 └────────┬────────┘
          │ request.app.state.ocr_task_manager
 ┌────────▼────────┐
 │  invoices.py    │   ✅ 通过 Request 获取 task_manager
 │  upload_invoice │     传入 upload_batch(task_manager=...)
 └────────┬────────┘
          │ task_manager is not None  →  True
 ┌────────▼────────┐
 │ invoice_service │   ✅ task_manager.submit_task(...)
 │  upload_batch   │     异步线程池执行 OCR
 └────────┬────────┘
          │ 异步提交
 ┌────────▼────────┐
 │  ocr_service    │   ✅ PaddleOCR → 字段提取 → 状态更新
 │  _do_ocr()      │     processing → pending/failed
 └─────────────────┘
```

## 测试验证

**68 个测试全部通过**（0 失败，0 跳过）：

```
tests/test_t01_infrastructure.py .... 15 passed
tests/test_t02_upload.py .........     9 passed
tests/test_t03_ocr.py ......          6 passed
tests/test_t04_list_detail.py ...    11 passed
tests/test_t05_update_confirm.py ..  14 passed
tests/test_t06_delete_trash.py ..    13 passed
=========================================
                  68 passed in 14.43s
```

### 验证策略

| 测试文件 | 验证内容 | 策略 |
|---------|---------|------|
| test_t02 | 上传后发票状态为 `processing` | conftest 禁用 task_manager，OCR 不走线程池 |
| test_t03 | OCR 识别字段 → `pending`/`failed` | 直接调用 `_run_ocr_inline` + mock PaddleOCR |
| test_t04~t06 | 上传后正常列表/详情/编辑/删除 | 独立于 OCR 状态 |

## 影响范围

| 维度 | 说明 |
|------|------|
| **向后兼容** | ✅ 完全兼容，task_manager 为 None 时行为不变 |
| **配置控制** | ✅ `ocr_enabled=false` 时 TaskManager 不创建 |
| **测试影响** | ✅ conftest 隔离，测试环境不触发异步 OCR |
| **API 接口** | ✅ 仅上传端点 `POST /api/invoices/` 新增 `request` 参数（FastAPI 自动注入） |

## 相关文件

| 文件 | 操作 |
|------|------|
| `server/main.py` | ✏️ 修改 — 新增 OcrTaskManager 实例化和生命周期管理 |
| `server/app/api/invoices.py` | ✏️ 修改 — 注入 Request，传入 task_manager |
| `server/tests/conftest.py` | ✏️ 修改 — 禁用后台 OCR |
| `server/app/services/ocr_service.py` | 📖 无修改 — 原有实现 |
| `server/app/services/invoice_service.py` | 📖 无修改 — 原有接口 |

---

## 第二轮修复：PaddleOCR 引擎修复

第一轮修复完成后，OcrTaskManager 已经正确接线，但实际运行中发票仍然停留在 `processing` 状态。经排查发现 PaddleOCR 引擎本身存在多个层面问题。

### 问题 1：PaddleOCR 未安装

**现象**：OCR 任务提交后静默失败，日志无输出。

**根因**：`paddleocr` 包未安装到当前 Python 环境，`_do_ocr()` 捕获 `ImportError` 后静默返回，发票状态从未更新。

**修复**：
```bash
pip install paddlepaddle paddleocr
```

---

### 问题 2：PaddleOCR 2.x → 3.x API 不兼容

**现象**：安装 PaddleOCR 后调用报错：
- `PaddleOCR() got an unexpected keyword argument 'show_log'`
- `PaddleOCR.predict() got an unexpected keyword argument 'cls'`
- OCR 识别返回乱码（如 `"n\na\no\nt\no\ne..."`）

**根因**：`ocr_service.py` 中的 `_call_paddleocr()` 函数使用的是 PaddleOCR 2.x 的 API，而 pip 安装的是最新的 3.x 版本。3.x 版本有以下破坏性变更：

| 变更项 | 旧 API (2.x) | 新 API (3.x) |
|--------|-------------|-------------|
| 构造参数 | `PaddleOCR(show_log=False, use_angle_cls=True, lang="ch")` | `PaddleOCR(use_angle_cls=True, lang="ch")` — `show_log` 已移除 |
| 识别方法 | `ocr.ocr(file_path, cls=True)` | `ocr.predict(file_path)` — 方法名和参数完全不同 |
| 返回结构 | `[[[box], (text, score)], ...]` | `OCRResult` 对象，文本在 `.json['res']['rec_texts']` 中 |

**修复** — 重写 `_call_paddleocr()` 函数：

```python
import logging
logger = logging.getLogger(__name__)

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
```

---

### 问题 3：PaddleOCR 版本链不兼容

**现象**：API 适配后调用仍然报错：
- `PaddlePredictorOption.__init__() takes 1 positional argument but 2 were given`
- `(Unimplemented) ConvertPirAttribute2RuntimeAttribute not support [pir::ArrayAttribute<pir::DoubleAttribute>]`

**根因**：`paddlepaddle`、`paddleocr`、`paddlex` 三个包的版本必须严格对齐，否则模型推理引擎会失败。pip 默认安装的最新版本互相不兼容。

**版本兼容关系**：

| 组合 | 结果 |
|------|------|
| `paddlepaddle 3.3.1` + `paddleocr 3.5.0` | ❌ oneDNN CPU bug |
| `paddleocr 3.1.0` + `paddlex 3.5.2` | ❌ `PaddlePredictorOption` 参数错误 |
| `paddlepaddle 3.1.0` + `paddleocr 3.1.0` + `paddlex 3.1.1` | ✅ 工作正常 |

**修复**：降级到经过验证的兼容版本组合：
```bash
pip install paddlepaddle==3.1.0 paddleocr==3.1.0 paddlex==3.1.1
```

---

### 第二轮修复涉及文件

| 文件 | 操作 |
|------|------|
| `server/app/services/ocr_service.py` | ✏️ 重写 `_call_paddleocr()` — API 从 2.x 迁移到 3.x，输出解析适配 `OCRResult` 结构，添加结构化日志 |
| `server/requirements.txt` | ✏️ 添加 — `paddlepaddle==3.1.0`, `paddleocr==3.1.0`, `paddlex==3.1.1`（pin 版本防断裂） |

### 修复后验证

1. 清理旧 `__pycache__` 后重启后端服务器
2. 重新处理 2 张卡住的发票，均成功识别：
   - 发票 1：发票号=91440118，金额=735元，日期=2026-05-13，销方=安徽图联科技有限公司
   - 发票 2：发票号=92341700，金额=998元，日期=2026-05-15，销方=安徽图联科技有限公司
3. 运行全部 68 个后端测试：**68 passed in 14.03s，0 失败**

---

## 预防措施

1. **依赖版本锁定**：`requirements.txt` 中 pinned PaddleOCR 系列版本，防止 `pip install` 自动升级导致断裂
2. **编写集成测试**：模拟完整上传→OCR→状态变更链路（在有 PaddleOCR 的环境中）
3. **日志增强**：`_call_paddleocr()` 现在对安装失败、初始化失败、识别失败三级分别记录日志
4. **健康检查**：添加 OCR 引擎状态检查接口
5. **Circuit Breaker**：如 OCR 持续失败可自动降级