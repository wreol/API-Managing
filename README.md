# API Vault — AI API 用量管理与监控平台

> 统一管理第三方 AI API Key，实时检测 Key 健康状态，告警通知，团队共享。

## 功能

- **Key 保险库** — AES-256-GCM 加密存储，掩码展示，一键复制
- **健康监控** — 实时测试 Key 连接状态，Worker 定时自动检测
- **故障告警** — Key 失效时自动邮件通知，站内事件记录
- **团队共享** — read/use 权限，安全分享 Key 不泄露明文
- **多 Provider 支持** — 内置 OpenAI / Anthropic / DeepSeek，可自定义添加

## 快速启动

```bash
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost |
| API 文档 | http://localhost:8000/docs |
| MailHog（开发邮件） | http://localhost:8025 |

### 本地开发

```bash
cd backend && pip install -r requirements.txt && cp .env.example .env
uvicorn app.main:app --reload --port 8000

cd frontend && npm install && npm run dev
```

### 测试

```bash
cd backend && python -m pytest tests/ -v    # 219 tests
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| DATABASE_URL | PostgreSQL 连接 | postgresql+asyncpg://... |
| REDIS_URL | Redis 连接 | redis://redis:6379/0 |
| JWT_SECRET_KEY | JWT 签名密钥 | 修改 |
| KEY_ENCRYPTION_KEY | AES-256 加密密钥 | 修改 |
| SMTP_HOST/PORT/USER/PASSWORD/FROM | 邮件服务 | MailHog (开发) |

## 技术栈

Python / FastAPI / PostgreSQL / Redis / ARQ / React / TypeScript / Docker

## 文档

- `SPEC.md` — 设计文档
- `PLAN.md` — 实现计划
- `SPEC_PROCESS.md` — 冷启动验证与过程记录
- `AGENT_LOG.md` — Subagent 使用日志
- `REFLECTION.md` — 反思报告

## API 端点

| 模块 | 端点 |
|------|------|
| Auth | POST /register, /login, /refresh, GET /me |
| Keys | GET/POST /keys, GET/PATCH/DELETE /keys/{id}, POST /keys/{id}/copy, /test |
| Alerts | GET/POST /alerts/rules, PATCH/DELETE /alerts/rules/{id}, GET /alerts/events |
| Team | POST /team/share, GET /team/shares, PATCH/DELETE /team/share/{id} |
| Providers | GET /providers, POST /providers/custom, DELETE /providers/custom/{name} |
