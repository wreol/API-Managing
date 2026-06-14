# API Vault — AI API 用量管理与监控平台

> 统一管理所有第三方 AI API Key，自动拉取用量，预算告警，团队共享。

## 功能

- **Key 保险库** — AES-256-GCM 加密存储，掩码展示，复制审计
- **用量仪表盘** — 自动对接 OpenAI/Anthropic/DeepSeek 等拉取用量
- **预算告警** — 费用/调用量阈值，邮件通知
- **团队共享** — 只读/可使用权限，安全分享

## 快速启动

```bash
docker compose up -d         # 一键启动全栈
```
访问 http://localhost

### 本地开发

```bash
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000
cd frontend && npm install && npm run dev
```

### 测试

```bash
cd backend && python -m pytest tests/ -v    # 219 tests
```

## 技术栈

Python / FastAPI / PostgreSQL / Redis / React / TypeScript / Docker

## 文档

- `SPEC.md` — 设计文档
- `PLAN.md` — 实现计划
- `SPEC_PROCESS.md` — 冷启动验证与过程记录
- `AGENT_LOG.md` — Subagent 使用日志
- `REFLECTION.md` — 反思报告
