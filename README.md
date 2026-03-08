# Text-to-CAD

一个基于大型语言模型的自然语言转 CAD 系统。用户通过网页输入自然语言描述，系统自动生成可导出、可预览的 STEP 格式 3D 模型。

![Architecture](docs/architecture.png)

## 项目概述

本项目旨在构建一个完整的自动化流程，将自然语言机械设计需求转换为精确的 STEP CAD 模型：

用户输入 → 需求解析 → 复杂度评估 → 任务拆分 → LLM 生成 JSON 建模计划 → CAD 执行 → STEP 导出 → 3D 预览

## 核心特性

- **自然语言建模**：通过简单的文字描述生成 3D CAD 模型
- **智能任务拆分**：复杂设计自动拆分为可管理的子任务
- **结构化 JSON Schema**：严格的建模计划格式，确保可执行性
- **参数化设计**：支持可调整的参数，便于后续修改
- **网页 3D 预览**：无需安装 CAD 软件即可查看模型
- **STEP 导出**：生成工业标准的 CAD 文件格式

## 系统架构

详见 [ARCHITECTURE.md](ARCHITECTURE.md) 了解完整的系统设计：

- 系统整体架构设计
- 网页交互设计
- 复杂需求自动拆分策略
- CAD JSON Schema 设计
- LLM 建模规划策略
- CAD 几何执行引擎选型
- 3D 模型预览方案
- 进度展示与任务状态系统

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端** | Python 3.11 + FastAPI + Celery |
| **前端** | React 18 + TypeScript + React Three Fiber |
| **CAD 引擎** | CadQuery (OpenCascade) |
| **LLM** | Claude 3.5 Sonnet / GPT-4 |
| **数据库** | PostgreSQL + Redis |
| **文件存储** | MinIO |

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/text-to-cad.git
cd text-to-cad

# 2. 复制环境变量模板
cp .env.example .env
# 编辑 .env 文件，填入必要的 API 密钥

# 3. 启动基础设施
docker-compose up -d postgres redis minio

# 4. 安装后端依赖
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 5. 运行后端开发服务器
uvicorn app.main:app --reload

# 6. 安装前端依赖 (新终端)
cd frontend
npm install

# 7. 运行前端开发服务器
npm run dev

# 8. 启动 Celery Worker (新终端)
cd backend
celery -A worker.celery_app worker --loglevel=info
```

访问 http://localhost:5173 查看前端界面

## 使用示例

### 简单设计

```
创建一个铝合金支架，底部是100x80mm的矩形板，
厚度5mm，四角有M6螺栓孔，中心有一个直径30mm的圆孔。
```

### 复杂设计（自动拆分）

```
设计一个减速器外壳，包含底座、轴承座、上盖和加强筋。
底座尺寸为200x150x20mm，有两个直径50mm的轴承孔，
间距100mm。上盖通过6个M8螺栓固定。
```

## 项目路线图

### Phase 1: MVP (进行中)
- [x] 系统架构设计
- [ ] 基础后端 API
- [ ] 前端界面原型
- [ ] 简单 Prompt → CadQuery 代码
- [ ] 基础 STEP 导出

### Phase 2: 增强功能
- [ ] JSON Schema 完整实现
- [ ] 复杂度评估 + 任务拆分
- [ ] 自动修复机制
- [ ] 参数化设计支持

### Phase 3: 工程级功能
- [ ] 多用户支持
- [ ] 历史版本管理
- [ ] 设计模板库
- [ ] 装配体支持

## 贡献指南

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何参与项目。

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 致谢

- [CadQuery](https://cadquery.readthedocs.io/) - Python CAD 库
- [React Three Fiber](https://docs.pmnd.rs/react-three-fiber) - React 3D 渲染
- [OpenCascade](https://www.opencascade.com/) - CAD 内核

## 联系方式

- 项目 Issues: https://github.com/yourusername/text-to-cad/issues
- 邮件: your.email@example.com

---

**注意**: 本项目处于早期开发阶段，API 和架构可能会发生变化。
