# EasyBX - 智能发票管理与报销整理助手

一站式发票上传 OCR 识别 → 台账自动生成 → PDF 发票整理 → 费用报销单预览的智能报销管理工具。

## 技术栈

- **前端**: React 18 + TypeScript + Vite + Tailwind CSS
- **后端**: Python FastAPI + PaddleOCR + SQLAlchemy
- **数据库**: SQLite

## 快速启动

### 1. 环境准备

```bash
# 安装 Python 依赖
cd server
pip install -r requirements.txt

# 初始化数据库
python -m alembic upgrade head

# 安装前端依赖
cd ../web
npm install
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env
# 编辑 .env 填入实际配置
```

### 3. 启动

```bash
# 方式一: 一键启动
start.bat

# 方式二: 分别启动
# 终端 1 - 后端 (端口 0220)
cd server
python -m uvicorn main:app --host 0.0.0.0 --port 0220 --reload

# 终端 2 - 前端 (端口 5180)
cd web
npm run dev
```

### 4. 访问

- 前端页面: [http://localhost:5180](http://localhost:5173)
- API 文档: <http://localhost:0220/docs>

## 项目结构

```
EasyBX/
├── server/          # 后端 Python FastAPI
├── web/             # 前端 React + TypeScript
├── data/            # SQLite 数据库文件
├── uploads/         # 上传的发票文件
├── specs/           # 项目定义文档
└── docs/            # 项目文档
```

详见 `specs/` 目录下的完整定义文档。
