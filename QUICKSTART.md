# Quick Start Guide

## 🚀 5 分钟启动 Text-to-CAD 项目

### 1. 克隆项目

```bash
git clone https://github.com/FranciXing/text-to-cad.git
cd text-to-cad
```

### 2. 启动基础设施

```bash
# 使用 Docker Compose 启动所有服务
docker-compose up -d postgres redis minio

# 等待服务启动
sleep 10
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥
```

### 4. 安装后端依赖

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 5. 运行后端

```bash
# 终端 1: 启动 API 服务器
uvicorn app.main:app --reload --port 8000
```

### 6. 运行前端

```bash
# 终端 2
cd frontend
npm install
npm run dev
```

### 7. 启动 Worker

```bash
# 终端 3
cd backend
celery -A worker.celery_app worker --loglevel=info
```

### 8. 访问应用

打开浏览器访问: http://localhost:5173

---

## 📁 项目结构

```
text-to-cad/
├── ARCHITECTURE.md     # 完整系统架构设计
├── README.md           # 项目说明
├── docker-compose.yml  # 基础设施配置
├── backend/            # FastAPI 后端
├── frontend/           # React 前端
├── worker/             # Celery 任务队列
└── docs/               # 文档
```

---

## 🔧 开发工作流

### 添加新功能

1. 创建新分支: `git checkout -b feature/new-feature`
2. 编写代码
3. 提交更改: `git commit -m "Add new feature"`
4. 推送分支: `git push origin feature/new-feature`
5. 创建 Pull Request

### 运行测试

```bash
cd backend
pytest
```

---

## 📚 下一步

- 阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 了解完整系统设计
- 查看 API 文档: http://localhost:8000/docs
- 开始实现 MVP 功能

## 🆘 常见问题

**Q: 数据库连接失败？**
A: 确保 PostgreSQL 容器正在运行: `docker-compose ps`

**Q: CadQuery 安装失败？**
A: 需要安装 OpenCascade 依赖，查看 CadQuery 官方文档

**Q: 前端无法连接后端？**
A: 检查 `.env` 中的 `VITE_API_URL` 配置

---

## 📝 重要链接

- GitHub 仓库: https://github.com/FranciXing/text-to-cad
- 问题反馈: https://github.com/FranciXing/text-to-cad/issues
- CadQuery 文档: https://cadquery.readthedocs.io/
