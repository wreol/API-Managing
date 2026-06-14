# AGENT_LOG.md — 智能体使用过程记录

## Commit 来源清单

> 满足课程要求：每个 commit 标注 subagent 实现或人工修改

| Commit | Phase | 来源 | 说明 |
|--------|-------|:--:|------|
| aa01dc1 | T0.1 | 人工 | Backend scaffold |
| bad2c45 | T0.2 | 人工 | Frontend scaffold |
| 4008ddd | T1.1 | Subagent | ORM Models |
| dccad5e | T1.2 | Subagent | Alembic migrations |
| (cold-start) | T2.1 | Subagent | Encryption service，与主 agent 不同类型 |
| ff41b33 | T2.2 | Subagent | Auth service + API |
| bbe37db | T3.1 | Subagent | Key Vault CRUD + 加密 |
| 82599ec | T4.1-T4.6 | Subagent | Provider Engine |
| e4798d5 | T5.1-T6.1 | Subagent | Usage / Worker / Alert |
| aa1ec60 | T7.1 | Subagent | Team Sharing（人工 commit，连接中断） |
| cfd2dd3 | T8.0-T8.5 | Subagent | Frontend 全部页面 |
| 828fcea | T9.1/T9.3 | 人工 | Docker + README + REFLECTION |
| a25ac35 | CI | 人工 | CI fix: aiosqlite |
| 35eade1 | CI | 人工 | CI fix: redis |
| 4705006 | CI | 人工 | CI fix: pytest |
| c73b6c8 | CI | 人工 | CI fix: relax pins |
| 0b8749d | Bugfix | 人工 | INET/JSONB 类型修复 |
| d544453 | Bugfix | 人工 | ProviderRegistry 单例修复 |
| 73a9d76 | Bugfix | 人工 | replace placeholder providers |
| 57f9a18 | Feature | 人工 | Test Connection 触发告警 |
| 其余 25+ | Bugfix/Feature | 人工 | 共享权限、Dashboard、邮件等 |

---

## 2026-06-14 — Brainstorming & 规约阶段

### Brainstorming (Superpowers brainstorming skill)

| 项目 | 详情 |
|------|------|
| **时间** | 2026-06-14 上午 |
| **触发技能** | `superpowers:brainstorming` |
| **投入** | 1 小时，6 轮关键追问 |
| **产出** | SPEC.md v1.0 (10 节完整设计) |

**关键决策节点**：
1. 第三方 AI API 用量管理 → Provider 插件架构
2. 自动拉取 vs 手动录入 → 自动对接官方 API
3. 全功能版（仪表盘+告警+团队）→ 6 模块
4. 安全模型 → AES-256 + 审计日志
5. 前端 → React SPA + Open Design (Linear)
6. 通知渠道 → 缩减为纯邮件

**AI 追问好在哪里**：从"管理 API"模糊需求收敛到 6 模块设计。

**人工推翻 AI**：通知渠道从多渠道 Webhook 缩减为纯邮件；否决微服务架构。

---

### Writing Plans

| 项目 | 详情 |
|------|------|
| **触发技能** | `superpowers:writing-plans` |
| **产出** | PLAN.md (25 tasks, 9 phases) |

---

### 冷启动验证

| 项目 | 详情 |
|------|------|
| **验证 Task** | Task 2.1: Encryption Service |
| **冷启动 Agent** | 与主 Agent 不同类型的 agent（全新 session） |
| **结果** | 代码与 PLAN 几乎完全一致 |

**暴露的 3 个缺陷**：
1. EncryptionService 生命周期未定义 → SPEC v1.1 新增 §5.2
2. KEY_ENCRYPTION_KEY 派生方式缺失 → SHA-256 策略
3. __init__.py 约定缺失 → PLAN 新增约定表

---

## Phase 0: 工程脚手架

| Task | Commit | Agent | 说明 |
|------|--------|-------|------|
| T0.1 Backend | aa01dc1 | 人工 | requirements.txt, config, database, main |
| T0.2 Frontend | bad2c45 | 人工 | Vite + React + TS, JWT client, types |

---

## Phase 1: Backend Core Infrastructure

| Task | Commit | Agent | 测试 |
|------|--------|-------|:--:|
| T1.1 ORM Models | 4008ddd | Implementer (sonnet) | 65 pass |
| T1.2 Alembic | dccad5e | Implementer (sonnet) | 65 pass |

**Branch**: `feature/phase-1-core-infra` | **审查**: Spec ✅, Code ✅

---

## Phase 2: Auth (M1)

| Task | Commit | Agent | 测试 |
|------|--------|-------|:--:|
| T2.1 Encryption | 冷启动 | 冷启动 Agent | 6 pass |
| T2.2 Auth Service | ff41b33 | Implementer (sonnet) | 79 pass |

**Branch**: `feature/phase-2-auth`

---

## Phase 3: Key Vault (M2)

| Task | Commit | Agent | 测试 |
|------|--------|-------|:--:|
| T3.1 Key Service | bbe37db | Implementer (sonnet) | 107 pass |

**Branch**: `feature/phase-3-keyvault`

---

## Phase 4: Provider Engine (M3)

| Task | Commit | Agent | 测试 |
|------|--------|-------|:--:|
| T4.1-T4.6 Providers | 82599ec | Implementer (sonnet) | 149 pass |

**Branch**: `feature/phase-4-providers`

---

## Phase 5+6: Usage Worker & Alert Engine

| Task | Commit | Agent | 测试 |
|------|--------|-------|:--:|
| T5.1-T6.1 | e4798d5 | Implementer (sonnet) | 192 pass |

**Branch**: `feature/phase-5-usage-alerts`

---

## Phase 7: Team Sharing (M6)

| Task | Commit | Agent | 测试 |
|------|--------|-------|:--:|
| T7.1 Team Service | aa1ec60 | Implementer (sonnet) | 219 pass |

**Branch**: `feature/phase-7-team` | **注意**: Subagent 连接断开，代码已写入，人工 commit

---

## Phase 8: Frontend Pages

| Task | Commit | Agent |
|------|--------|-------|
| T8.0-T8.5 Frontend | cfd2dd3 | Implementer (sonnet) |

9 页面 (Landing, Auth×2, Dashboard, Keys×2, Alerts, Team, Providers, Onboarding)，Linear 暗色主题。

---

## Phase 9: Docker, CI, Docs

| Task | Commit | Agent | 说明 |
|------|--------|-------|------|
| Docker + Docs | 828fcea | 人工 | Dockerfile×2, docker-compose, README, REFLECTION |
| CI fix: aiosqlite | a25ac35 | 人工 | CI 缺少 aiosqlite 依赖 |
| CI fix: redis | 35eade1 | 人工 | arq 0.26.0 要求 redis<5 |
| CI fix: pytest | 4705006 | 人工 | pytest-asyncio 1.4.0 要求 pytest≥8.4 |
| CI fix: pins | c73b6c8 | 人工 | 预防性放宽 5+ 依赖版本 |

**CI 教训**: Subagent 独立 pin 版本，无全局 compatibility check。

---

## 生产 Bug 修复 (2026-06-14 下午)

### 模型不一致

| Commit | 问题 | 修复 |
|--------|------|------|
| 0b8749d | ip_address INET vs String、tags JSON vs JSONB | 恢复 PostgreSQL 原生类型 |
| 90817bf | alert_event.threshold_pct NOT NULL | 改为 nullable |

### Provider Registry

| Commit | 问题 | 修复 |
|--------|------|------|
| d544453 | 实例方法 vs 类方法调用 | @classmethod 单例，main.py 启动注册 |

### 占位实现

| Commit | 问题 | 修复 |
|--------|------|------|
| 73a9d76 | Anthropic/DeepSeek 占位 | 真实 test_connection (/v1/models) |

### Key 共享 & 权限

| Commit | 说明 |
|--------|------|
| b7fa362 | ShareResponse 加 key 信息 |
| 4226384 | Team 页同时请求 sent+received |
| bccd2b2 | 共享 Key 回 Keys 列表，permission 控制 |
| 98db89a | test_key → _get_key_or_shared |

### Dashboard & Alerts 重构

| Commit | 说明 |
|--------|------|
| ff02f38 | budget/call_count → key_health |
| 3f2d7f9 | Dashboard 用量图表 → 健康总览 |
| 80cda6e | KeyResponse 加 status 字段 |

### 告警触发

| Commit | 说明 |
|--------|------|
| 57f9a18 | Test Connection 触发告警事件 + 邮件 |
| 1c65c78 | MailHog 开发邮件捕获 |
| 255276a | SMTP 配置支持 .env |
| e21a32e | email_verified=True 修复规则创建 |

---

## 总结

| 指标 | 数值 |
|------|------|
| Subagent 派发 | 9 implementers + 8 reviewers |
| 人工 commits | 30+ |
| 测试 | 219 pass |
| 总 commits | 45+ |
| 代码行数 | ~5000 (backend 3000 + frontend 2000) |
| 冷启动缺陷 | 3 (已修复) |
| 最大教训 | 隐性上下文是 AI 协作最大敌人；subagent 独立 pin 版本导致 CI 冲突 |
