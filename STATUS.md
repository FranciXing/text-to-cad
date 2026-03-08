# Text-to-CAD 部署状态

## 📊 当前状态

### ✅ 已完成 (90%)

- 完整的后端 API 开发
- 部署到腾讯云服务器 (43.165.66.85)
- Python 环境配置
- 所有依赖安装
- GitHub 仓库更新

### ⏳ 待完成 (10%)

**服务稳定运行** - 需要手动完成最后一步

---

## 🚀 手动启动服务

请 SSH 登录服务器执行：

```bash
ssh ubuntu@43.165.66.85
# 密码: .FranciServer1

cd ~/text-to-cad/backend
source venv/bin/activate

# 设置环境变量
export OPENAI_API_KEY="你的-api-key"
export DEFAULT_LLM_PROVIDER="openai"

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

**GitHub**: https://github.com/FranciXing/text-to-cad
