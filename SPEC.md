# SPEC: API Vault — AI API 用量管理与监控平台

> **Spec-Driven, Subagent-Built, Human-Owned.**  
> 版本: v1.2 | 日期: 2026-06-14 | 状态: 终版（全部实现完成）

---

## 一、问题陈述

### 1.1 要解决什么问题

中国 AI 应用开发者面临碎片化的第三方 API 管理困境：

- **Key 散落各处**：OpenAI 的 Key 在 `.env` 文件，Anthropic 的在 1Password，通义千问的在阿里云控制台，DeepSeek 的在邮箱里——没有统一的地方查看和管理。
- **用量不可见**：每个服务商有独立控制台，需逐一登录查看。无法回答"我这个月所有 AI API 一共花了多少钱"这样最基本的问题。
- **超额没有预警**：深夜调试时不小心跑完额度，第二天生产环境报 HTTP 429——没有统一的预算阈值通知机制。
- **团队共享靠截图**：Key 通过微信/飞书/Slack 明文传递，既不安全也无法追踪使用情况。

### 1.2 目标用户

| 画像 | 描述 |
|------|------|
| **独立开发者** | 同时使用 3-5 个 AI API 服务，关心月度总花费，需要预算预警 |
| **AI 创业小团队** | 5-20 人，多人共享 Key，需要知道"谁用了多少"并安全管控 |
| **国内 AI 应用开发者** | 同时调用国际（OpenAI/Anthropic/Google AI）和国内（通义/文心/DeepSeek/智谱等）多个服务商 |

### 1.3 为什么值得做

AI API 正在成为现代应用的基础设施层，与云服务器同等重要。云服务器有 Terraform + Datadog 管理，但 AI API 的集中管理工具仍是空白。本项目填补这一空缺，且与 AI4SE 课程主题高度契合——它本身就是一个 AI 时代开发者需要的工具。

---

## 二、用户故事

遵循 INVEST 原则（Independent, Negotiable, Valuable, Estimable, Small, Testable）。

| # | 用户故事 | 验收要点 |
|---|----------|----------|
| **US-1** | 作为开发者，我希望能**安全地存储和管理所有 AI API Key**，按服务商和标签分类，不再需要在 `.env` 文件和聊天记录里到处找 Key | 可增删改查 Key；Key 在数据库中 AES-256-GCM 加密存储；支持按 provider 和 tag 分类筛选；列表显示掩码（如 `sk-...****a1b2`）；提供"复制到剪贴板"按钮（不渲染明文到 DOM，30s 后清除提示）并记录审计日志 |
| **US-2** | 作为开发者，我希望能**在一个仪表盘看到所有 AI API 的用量汇总**——各服务商的调用次数、Token 消耗、费用估算，而不必逐一登录各服务商控制台 | 仪表盘展示各 provider 用量卡片；自动定时拉取 + 手动刷新；支持日/周/月粒度切换；空状态有引导文案 |
| **US-3** | 作为团队 Lead，我希望能**把某个 Key 分享给团队成员**，设定只读（看用量）或可使用（调用 API）权限，并能查看每个人的使用记录 | 支持按邮箱/用户名分享 Key；两种权限级别；被分享者可在自己面板查看；撤销分享立即生效；不可链式分享 |
| **US-4** | 作为开发者，我希望**月度费用或调用量接近预算时收到邮件告警**，这样能防止意外超额 | 可设置 provider 级或 Key 级预算阈值；80% 预警 + 100% 严重两级告警；邮件通知；24h 内同规则不重复触发；用户须绑定并验证邮箱才能创建告警规则 |
| **US-5** | 作为开发者，我希望能**查看历史用量趋势和费用报表**——过去 N 个月各服务商的费用变化，找出"哪个 API 最烧钱"，辅助技术选型和成本优化 | 折线图展示趋势；可按 provider 对比；支持导出 CSV |
| **US-6** | 作为新用户，我希望能用 **GitHub 或 Google 账号一键登录**，也可以用邮箱注册，首次登录后有引导流程帮助快速添加第一个 Key | OAuth 登录正常回调；邮箱注册含验证步骤；新用户 Onboarding 引导 |
| **US-7** | 作为开发者，我希望能**添加对新 AI 服务商的适配**（如某国内新出的模型 API），只需配置 URL、认证方式、返回字段映射即可，不需等平台更新 | Provider 配置表单；支持自定义 HTTP REST 适配器；测试连接按钮验证配置正确性 |

---

## 三、功能规约

### M1: 用户认证与账户 (Auth)

| 维度 | 内容 |
|------|------|
| **输入** | 邮箱 + 密码（注册/登录）；GitHub OAuth Code；Google OAuth Code；Refresh Token |
| **行为** | 注册 → 发送验证邮件 → 激活账户；登录 → 签发 JWT access token (15min) + refresh token (7d)；OAuth → 回调验证 → 创建/绑定账户 |
| **输出** | JWT Token Pair、用户 Profile（id, email, avatar_url, auth_provider） |
| **边界条件** | 密码最短 8 位；Token 过期：access 15min / refresh 7d；重复注册邮箱返回 409；OAuth 邮箱冲突提示账户合并 |
| **错误处理** | 无效凭证 → 401 `{"error": "invalid_credentials"}`；邮箱未验证 → 403 `{"error": "email_not_verified"}`；OAuth 失败 → 302 重定向到登录页带 error 参数 |

### M2: API Key 保险库 (Key Vault)

| 维度 | 内容 |
|------|------|
| **输入** | Provider 类型、Key 明文值、显示名称（label）、标签（tags）、关联项目标识（可选） |
| **行为** | 接收明文 Key → AES-256-GCM 加密（密钥由环境变量 `KEY_ENCRYPTION_KEY` 经 SHA-256 派生为 32 字节，详见 §5.2）→ 提取 key_prefix（如 `sk-`）和 last_4 → 存入数据库；列表查询展示掩码格式 `{prefix}...****{last_4}`；点击复制按钮 → 解密完整 Key → 写入系统剪贴板（不渲染到 DOM）→ 记录审计日志；支持软删除（标记 is_active=False，30 天后清理） |
| **输出** | Key 列表（掩码展示）；Key 详情（完整值需二次验证后通过复制获取）；操作确认 |
| **边界条件** | Key 值不允许为空；同名 + 同 Provider 提示重复但允许添加（不同项目可能用不同 Key）；删除前检查是否有活跃的团队共享引用；key_prefix 和 last_4 为冗余存储，无需解密即可渲染列表 |
| **错误处理** | 加密失败 → 500 记录错误日志，不暴露内部细节；解密失败 → 标记数据损坏并告警管理员；Key 未找到 → 404；重复复制无限制（但每次均审计） |

### M3: Provider 适配器框架 (Provider Engine)

| 维度 | 内容 |
|------|------|
| **输入** | 内置 Provider 配置（base URL、auth header 格式、usage endpoint、响应字段映射路径）；自定义 Provider 由用户通过 UI 配置 |
| **行为** | 定义 `BaseProvider` 抽象类 → 每个服务商继承实现 `auth_headers()` / `fetch_usage()` / `normalize_response()`；Background Worker 定时遍历所有 active Key，调用对应 Provider 拉取用量；结果统一转为 `UsageRecord` 结构存入数据库 |
| **输出** | 标准化 `UsageRecord {provider, key_id, period_start, period_end, calls, tokens_in, tokens_out, cost_estimate, raw_response}` |
| **边界条件** | 拉取频率上限可配置（默认每小时，管理员可在配置中调整）；各 Provider 的 rate limit 差异化处理（如 OpenAI 20 req/min）；部分国内 Provider 不提供费用 API → 支持手动设置 token 单价计算费用；单个 Provider 拉取超时 30s，重试 1 次后跳过 |
| **错误处理** | API 超时 → 重试 1 次 → 标记该 Provider 本轮"部分失败"不影响其他；认证失败（401/403）→ 标记 Key 状态为 `needs_update`，前端展示警告；网络错误 → 记录日志，不污染 usage 数据 |

### M4: 仪表盘与用量可视化 (Dashboard)

| 维度 | 内容 |
|------|------|
| **输入** | 用户选中的 Provider 集合（默认全选）、时间范围（日/周/月/自定义起止日期） |
| **行为** | 查询 `UsageRecord` 表 → 按维度聚合（Provider / Key / 时间） → 计算汇总指标 → 渲染图表组件 |
| **输出** | 总览卡片（总调用次数 / Token 消耗 / 估算费用）；费用趋势折线图；Provider 费用占比饼图/环形图；Top-N Key 用量排行表 |
| **边界条件** | 无数据时展示空状态："还没有用量数据，去添加你的第一个 API Key 吧" → 链接到 Key 管理页；图表数据量 > 365 天自动降采样（取日均值）；仪表盘加载时间目标 < 2s；单个 Provider 数据拉取失败时卡片标注 "数据可能不完整" |
| **错误处理** | 查询超时 → 返回缓存数据（若有）或空状态 + 错误提示；聚合计算异常 → 前端 fallback 展示原始记录列表 |

### M5: 告警引擎 (Alert Engine)

| 维度 | 内容 |
|------|------|
| **输入** | 告警规则（Provider 或 Key 级别、阈值类型：费用金额 / 调用次数、阈值数值、通知邮箱） |
| **行为** | Background Worker 每次成功拉取用量后评估所有活跃规则 → 触发时生成 `alert_event` → 通过 SMTP 发送邮件通知；两级告警：80% 预警（warning）/ 100% 严重（critical）；同一规则 24h 内不重复触发 |
| **输出** | 站内通知（alert_events 列表）；邮件通知（HTML 格式，含用量详情和直达链接） |
| **边界条件** | 用户必须先绑定并验证邮箱才能创建告警规则；最多 5 条规则/Key；通知邮箱默认使用用户注册邮箱，可自定义（需额外验证） |
| **错误处理** | 邮件发送失败 → 重试 2 次（间隔 5min）→ 仍失败则记录日志，告警事件仍生成（站内可见）；SMTP 服务不可用 → 告警事件正常生成，用户下次登录可见 |

### M6: 团队共享 (Team Sharing)

| 维度 | 内容 |
|------|------|
| **输入** | 目标用户标识（邮箱/用户名）、Key ID、权限级别（`read` / `use`） |
| **行为** | 创建 `key_share` 记录 → 通知被分享者（站内 + 邮件）→ 被分享者在自己的面板看到共享 Key。`read` 权限：可查看用量、趋势，但不可复制 Key 明文；`use` 权限：可通过平台代理调用 API（实际请求由平台转发，携带 Key），但不能查看 Key 明文 |
| **输出** | 共享列表视图（"我分享的" / "分享给我的"）；分享详情（权限级别、分享时间）；撤销确认 |
| **边界条件** | 不可链式分享（被分享者不能再分享给第三人）；分享者撤销后立即生效，被分享者面板不再显示；`read` 权限下点击"复制 Key"返回权限不足提示；不可分享已软删除的 Key |
| **错误处理** | 目标用户不存在 → 404 `{"error": "user_not_found"}`；重复分享 → 409 `{"error": "already_shared"}`；尝试分享给已存在分享关系的用户 → 返回现有分享信息并提示可修改权限 |

---

## 四、非功能性需求

| 类别 | 要求 |
|------|------|
| **性能** | API 读操作 P95 < 200ms；写操作 P95 < 1s；仪表盘首屏加载 < 2s；后台 Provider 拉取单次 < 30s |
| **安全** | Key 使用 AES-256-GCM 加密存储，加密密钥由环境变量注入；密码 bcrypt 哈希（cost factor ≥ 12）；JWT access token 15min 过期；所有敏感操作（查看 Key、复制 Key、分享、撤销）写入审计日志；全程 HTTPS |
| **可用性** | 首次登录提供 3 步 Onboarding 引导（添加邮箱 → 添加第一个 Key → 查看仪表盘）；所有空状态页面有引导文案而非空白；错误提示使用中文且可理解（非原始异常堆栈） |
| **可观测性** | 结构化日志（JSON 格式，每行一条）；审计日志只追加不删除；关键操作附带 trace_id 便于追踪 |
| **兼容性** | 前端支持 Chrome/Firefox/Edge 最近 2 个主版本；后端 Python 3.11+ |

---

## 五、系统架构

### 5.1 整体架构风格

**模块化单体 + Provider 插件架构**，前后端分离。

```
┌─────────────────────────────────────────────────┐
│                   React SPA                       │
│              (Nginx 静态服务)                      │
└───────────────────┬─────────────────────────────┘
                    │ REST API (JSON + JWT Bearer)
┌───────────────────▼─────────────────────────────┐
│              FastAPI 主服务                        │
│  ┌──────┬──────────┬─────────┬───────┬────────┐ │
│  │ Auth │ Key Vault│Dashboard│ Alert │  Team  │ │
│  └──────┴──────────┴─────────┴───────┴────────┘ │
│         │                                     │   │
│  ┌──────▼──────────────────────────┐          │   │
│  │     Provider Registry           │          │   │
│  │  BaseProvider → [OpenAI|Anthropic│          │   │
│  │  |Google|Qwen|Wenxin|DeepSeek   │          │   │
│  │  |Zhipu|Moonshot|Doubao|...]    │          │   │
│  └─────────────────────────────────┘          │   │
└──────┬────────────────────┬────────────────────┘
       │                    │
┌──────▼──────┐    ┌───────▼────────┐
│ PostgreSQL  │    │  Redis          │
│ (主数据存储) │    │ (队列 + 缓存)   │
└─────────────┘    └───────┬────────┘
                           │
                  ┌────────▼────────────┐
                  │ Background Worker    │
                  │ (ARQ)                │
                  │ • Provider Fetcher   │
                  │ • Alert Evaluator    │
                  │ • Email Sender       │
                  └────────┬─────────────┘
                           │ 出站请求
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
    ┌──────────┐   ┌────────────┐   ┌──────────────┐
    │ OpenAI   │   │  Anthropic │   │ 通义/文心/... │
    │ API      │   │  API       │   │ API           │
    └──────────┘   └────────────┘   └──────────────┘
                           │
                    ┌──────▼──────┐
                    │ SMTP Server  │
                    │ (邮件通知)    │
                    └──────────────┘
```

### 5.2 服务生命周期与依赖注入

关键服务采用**模块级单例 + FastAPI Depends 注入**模式：

| 服务 | 生命周期 | 初始化方式 |
|------|----------|------------|
| `EncryptionService` | 应用级单例 | 启动时从 `settings.KEY_ENCRYPTION_KEY` 通过 SHA-256 派生 32 字节密钥，构造单例。所有 service 通过 `Depends(get_encryption_service)` 获取同一实例 |
| `ProviderRegistry` | 应用级单例 | 启动时自动发现 `providers/` 目录下所有 `BaseProvider` 子类并注册 |
| `AuthService` / `KeyService` / etc. | 请求级 | 每个请求通过 `Depends` 新建，注入 `db: AsyncSession` + 所需单例服务 |

**密钥派生规则**：环境变量 `KEY_ENCRYPTION_KEY` 接受任意长度字符串，通过 `hashlib.sha256(env_value.encode()).digest()` 派生为 32 字节 AES-256 密钥。测试环境可直接使用 32 字节裸字符串。

### 5.3 Provider 插件架构（核心设计）

```python
# providers/base.py
class BaseProvider(ABC):
    """每个 AI 服务商的适配器基类"""

    provider_name: str              # "openai" / "anthropic" / "qwen"
    base_url: str                   # API base URL
    usage_endpoint: str             # usage 查询端点
    rate_limit_rps: float = 1.0     # 默认每秒 1 次请求

    @abstractmethod
    def auth_headers(self, api_key: str) -> dict[str, str]: ...

    @abstractmethod
    async def fetch_usage(self, api_key: str) -> UsageRecord: ...

    def normalize_response(self, raw: dict) -> UsageRecord: ...
```

每个 AI 服务商实现独立的 Provider 类，注册到 ProviderRegistry。新增 Provider 无需修改任何核心代码。

### 5.3 外部依赖

| 依赖 | 用途 | 是否必须 |
|------|------|----------|
| PostgreSQL 15 | 主数据存储 | 必须 |
| Redis 7 | ARQ 任务队列 + 用量数据缓存 | 必须 |
| SMTP Server / Resend API | 验证邮件 + 告警通知 | 必须 |
| GitHub OAuth API | 第三方登录 | 可选（可降级为纯邮箱） |
| Google OAuth API | 第三方登录 | 可选 |
| OpenAI / Anthropic / etc. API | 拉取用量数据 | 核心功能依赖 |

---

## 六、数据模型

### 6.1 实体关系总览

共 7 张核心表：

```
users ──1:N──▶ api_keys ──1:N──▶ usage_records
  │              │
  │ 1:N          │ N:M
  │              └──────▶ key_shares
  │                         │
  │ 1:N                     ├── shared_with → users
  ▼                         └── shared_by   → users
alert_rules ──1:N──▶ alert_events

audit_logs (独立，关联 user_id)
```

### 6.2 表定义

**users** — 用户账户

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK, default gen | |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | 登录邮箱 |
| `password_hash` | VARCHAR(255) | nullable | bcrypt 哈希（OAuth 用户可为空） |
| `oauth_provider` | VARCHAR(20) | nullable | "github" / "google" |
| `oauth_id` | VARCHAR(255) | nullable | OAuth provider 的用户 ID |
| `display_name` | VARCHAR(100) | NOT NULL | 显示名称 |
| `is_active` | BOOLEAN | DEFAULT TRUE | |
| `email_verified` | BOOLEAN | DEFAULT FALSE | 邮箱验证状态 |
| `notification_email` | VARCHAR(255) | nullable | 告警通知邮箱（默认=email） |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | |

**api_keys** — 加密存储的 API Key

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | |
| `user_id` | UUID | FK → users.id, NOT NULL | 所有者 |
| `provider` | VARCHAR(50) | NOT NULL | "openai" / "anthropic" / "qwen" / "custom" |
| `label` | VARCHAR(200) | NOT NULL | 用户命名的显示名 |
| `key_encrypted` | TEXT | NOT NULL | AES-256-GCM 密文（nonce + ciphertext 的 hex 编码）。加密密钥由 `KEY_ENCRYPTION_KEY` 经 SHA-256 派生 |
| `key_prefix` | VARCHAR(20) | NOT NULL | 自动提取的 Key 前缀（如 "sk-"） |
| `last_4` | CHAR(4) | NOT NULL | 末 4 位（用于掩码展示） |
| `tags` | JSONB | DEFAULT '[]' | 标签数组 |
| `is_active` | BOOLEAN | DEFAULT TRUE | 软删除标记 |
| `status` | VARCHAR(20) | DEFAULT 'ok' | ok / needs_update / error |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

**usage_records** — 标准化用量记录

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | |
| `key_id` | UUID | FK → api_keys.id, NOT NULL | |
| `provider` | VARCHAR(50) | NOT NULL | 冗余，加速查询 |
| `fetched_at` | TIMESTAMPTZ | DEFAULT NOW() | 拉取时间 |
| `period_start` | DATE | NOT NULL | 用量周期开始 |
| `period_end` | DATE | NOT NULL | 用量周期结束 |
| `calls` | INTEGER | DEFAULT 0 | 调用次数 |
| `tokens_in` | BIGINT | DEFAULT 0 | 输入 token 数 |
| `tokens_out` | BIGINT | DEFAULT 0 | 输出 token 数 |
| `cost_estimate` | DECIMAL(10,4) | nullable | 估算费用（USD） |
| `raw_response` | JSONB | nullable | Provider 原始返回 |

**key_shares** — Key 共享关系

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | |
| `key_id` | UUID | FK → api_keys.id, NOT NULL | |
| `shared_by` | UUID | FK → users.id, NOT NULL | 分享者 |
| `shared_with` | UUID | FK → users.id, NOT NULL | 被分享者 |
| `permission` | VARCHAR(10) | NOT NULL | "read" / "use" |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

**alert_rules** — 告警规则

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | |
| `user_id` | UUID | FK → users.id, NOT NULL | |
| `key_id` | UUID | FK → api_keys.id, nullable | NULL=Provider 级规则 |
| `provider` | VARCHAR(50) | nullable | key_id 为空时必填 |
| `type` | VARCHAR(20) | NOT NULL | "budget" / "call_count" |
| `threshold` | DECIMAL(12,4) | NOT NULL | 阈值（金额或次数） |
| `notify_email` | VARCHAR(255) | NOT NULL | 通知邮箱（须已验证） |
| `is_active` | BOOLEAN | DEFAULT TRUE | |

**alert_events** — 告警触发历史

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | |
| `rule_id` | UUID | FK → alert_rules.id, NOT NULL | |
| `triggered_at` | TIMESTAMPTZ | DEFAULT NOW() | |
| `threshold_pct` | DECIMAL(5,2) | NOT NULL | 触发时的用量百分比 |
| `message` | TEXT | NOT NULL | 告警内容 |
| `is_read` | BOOLEAN | DEFAULT FALSE | |
| `email_sent` | BOOLEAN | DEFAULT FALSE | 邮件是否发送成功 |

**audit_logs** — 审计日志

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUID | PK | |
| `user_id` | UUID | FK → users.id, NOT NULL | |
| `action` | VARCHAR(50) | NOT NULL | key_viewed / key_copied / key_shared / share_revoked / alert_rule_created |
| `resource_type` | VARCHAR(50) | NOT NULL | "api_key" / "key_share" / "alert_rule" |
| `resource_id` | UUID | NOT NULL | 关联资源 ID |
| `ip_address` | INET | nullable | 请求 IP |
| `user_agent` | TEXT | nullable | 请求 User-Agent |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | |

---

## 七、API 设计

所有端点前缀 `/api/v1`，JSON 请求/响应，认证通过 `Authorization: Bearer <access_token>`。

### 7.1 认证 (`/api/v1/auth`)

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/auth/register` | 邮箱注册 | `{email, password, display_name}` | `201 {user, access_token, refresh_token}` |
| POST | `/auth/login` | 邮箱登录 | `{email, password}` | `200 {access_token, refresh_token}` |
| GET | `/auth/oauth/{provider}` | OAuth 发起 | — | 302 重定向 |
| GET | `/auth/oauth/callback?code=&state=` | OAuth 回调 | — | `200 {access_token, refresh_token}` |
| POST | `/auth/refresh` | 刷新 Token | `{refresh_token}` | `200 {access_token, refresh_token}` |
| POST | `/auth/verify-email` | 验证邮箱 | `{email, code}` | `200 {message}` |
| POST | `/auth/me` | 当前用户信息 | — | `200 {user}` |

错误码：`401` invalid_credentials / token_expired；`403` email_not_verified；`409` email_exists

### 7.2 Key 管理 (`/api/v1/keys`)

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/keys` | 我的 Key 列表 | — | `200 [{id, provider, label, masked_key, tags, status}]` |
| POST | `/keys` | 添加 Key | `{provider, key_value, label, tags?}` | `201 {id, label, masked_key}` |
| GET | `/keys/{id}` | Key 详情（二次验证） | — | `200 {id, provider, label, masked_key, tags, status, usage_summary}` |
| PATCH | `/keys/{id}` | 更新信息 | `{label?, tags?}` | `200 {updated_key}` |
| DELETE | `/keys/{id}` | 软删除 | — | `204` |
| POST | `/keys/{id}/copy` | 复制明文到剪贴板 | — | `200 {message, expires_in: 30}` + 审计 |
| POST | `/keys/{id}/test` | 测试连接 | — | `200 {ok, message}` |

错误码：`404` key_not_found；`403` access_denied；`409` duplicate_key

### 7.3 用量数据 (`/api/v1/usage`)

| 方法 | 路径 | 查询参数 | 响应 |
|------|------|----------|------|
| GET | `/usage/summary` | `?period=current_month` | `{total_calls, total_tokens, total_cost, by_provider: [...]}` |
| GET | `/usage/trend` | `?from=&to=&granularity=day&provider=` | `[{date, calls, tokens, cost}]` |
| GET | `/usage/by-provider` | `?period=30d` | `[{provider, calls, tokens, cost, percentage}]` |
| GET | `/usage/by-key` | `?period=30d&sort=cost` | `[{key_id, label, provider, calls, cost}]` |

### 7.4 告警 (`/api/v1/alerts`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/alerts/rules` | 我的告警规则列表 |
| POST | `/alerts/rules` | 创建规则 `{key_id?, provider?, type, threshold, notify_email}` |
| PATCH | `/alerts/rules/{id}` | 修改规则 |
| DELETE | `/alerts/rules/{id}` | 删除规则 |
| GET | `/alerts/events` | 告警历史 `?unread_only=true` |
| PATCH | `/alerts/events/{id}/read` | 标记已读 |

创建规则前置条件：`notification_email` 必须是已验证邮箱，否则返回 403 `email_not_verified`。

### 7.5 团队共享 (`/api/v1/team`)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/team/share` | 分享 Key `{key_id, shared_with_email, permission}` |
| GET | `/team/shares` | 分享列表 `?direction=sent|received` |
| PATCH | `/team/share/{id}` | 修改权限 |
| DELETE | `/team/share/{id}` | 撤销分享 |

### 7.6 Provider (`/api/v1/providers`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/providers` | 可用 Provider 列表（内置 + 自定义） |
| POST | `/providers/custom` | 添加自定义 Provider `{name, base_url, auth_type, usage_endpoint, field_mapping}` |
| DELETE | `/providers/custom/{id}` | 删除自定义 Provider |

### 7.7 审计 (`/api/v1/audit-logs`)

| 方法 | 路径 | 查询参数 | 说明 |
|------|------|----------|------|
| GET | `/audit-logs` | `?action=&from=&to=&page=&limit=` | 我的审计日志（分页） |

---

## 八、技术选型与理由

| 层 | 选型 | 版本 | 理由 |
|----|------|------|------|
| **后端框架** | FastAPI | 0.115+ | 异步原生支持、自动 OpenAPI 文档生成、Pydantic 类型校验、Python 生态丰富——你的主力语言 |
| **前端框架** | React + TypeScript | 18+ | 交互式仪表盘组件生态最成熟（Recharts / shadcn/ui）；TypeScript 减少运行时错误 |
| **Open Design 设计系统** | **Linear** + `dashboard` / `saas-landing` / `web-prototype` / `critique` / `tweaks` skill | — | 详见下方「Open Design 使用说明」 |
| **数据库** | PostgreSQL | 15 | JSONB 支持存 raw_response；成熟稳定；行级安全可扩展 |
| **缓存 / 队列** | Redis + ARQ | 7 / 0.25+ | Redis 做用量数据缓存；ARQ 比 Celery 更轻、async 原生、够用 |
| **加密** | cryptography (Fernet / AES-256-GCM) | 44+ | Python 标准加密库；审计友好；Fernet 简化密钥管理 |
| **邮件** | AIOSMTP / Resend API | — | 异步发送；Resend 提供优雅的 Python SDK |
| **OAuth** | httpx + 标准 OAuth2 流程 | — | GitHub / Google OAuth 直接对接 |
| **容器化** | Docker + docker-compose | — | 课程强制要求；三服务编排（app / postgres / redis） |
| **CI/CD** | GitHub Actions | — | 自动测试 + Docker 镜像构建 + 推送到 GHCR |

### Open Design 使用说明

本项目为 Web 全栈应用，须使用 Open Design。选定 **Linear 设计系统**（暗色主题、简洁线条、最小化装饰，精准匹配开发者工具定位），按以下页面→skill 映射执行前端开发：

| 前端页面 | Open Design Skill | 说明 |
|----------|-------------------|------|
| 首页 / Landing | `saas-landing` | 产品介绍、功能展示、CTA 按钮，引导用户注册或登录 |
| 仪表盘（Dashboard） | `dashboard` | 用量总览卡片 + 趋势图 + Provider 占比，**整个项目的视觉核心** |
| 登录 / 注册页 | `web-prototype` | 邮箱登录 + OAuth 按钮 + 注册表单。Open Design 无独立 auth skill，用 `web-prototype` 生成 |
| 新用户引导（Onboarding） | `web-prototype` | 3 步引导：验证邮箱 → 添加第一个 Key → 查看仪表盘 |
| Key 管理 / 详情页 | `web-prototype` | Key 列表 + 添加表单 + 详情面板 |
| 告警规则 / 团队 / Provider 配置页 | `web-prototype` | 表单密集型页面，统一用 `web-prototype` |
| 设计审查 | `critique` | 每完成 2-3 个页面后触发，检查设计与 Linear 系统的一致性 |
| 细节修复 | `tweaks` | 根据 `critique` 的反馈进行针对性修复 |

**工作流**：每开发一个前端页面 → 先调用对应 Open Design skill 生成设计稿 → 确认后写代码 → 每 2-3 页调用 `critique` → `tweaks` 修复。这确保了 AI 不产出千篇一律的 Material Design 风格，而是有 Linear 品牌个性的界面。

---

## 九、验收标准

| 模块 | 验收标准 | 验证方式 |
|------|----------|----------|
| **Auth** | 邮箱注册 + 验证邮件 + 登录完整通过；GitHub OAuth 登录成功；Google OAuth 登录成功；refresh token 有效；过期 token 被拒绝 | E2E 测试 |
| **Key Vault** | 添加 Key → 列表显示掩码 `sk-...****a1b2`；点击复制 → 剪贴板获得完整 Key；审计日志有 `key_copied` 记录；删除 Key 后列表不再显示；恢复后可重新出现 | E2E + 单元测试 |
| **Provider Engine** | OpenAI Provider 拉取返回有效数据；Anthropic Provider 拉取成功；DeepSeek Provider 拉取成功；自定义 Provider 配置 + 测试连接通过；一个 Provider 失败不影响其他 | 集成测试 |
| **Dashboard** | 有数据时总览卡片数字正确；趋势折线图渲染正常；切换日/周/月粒度正常；无数据时展示空状态引导 | E2E 测试 |
| **Alert Engine** | 创建预算规则 → 用量超阈值 → 收到邮件；24h 内不重复触发同一规则；未验证邮箱用户创建规则被拒绝 | 集成测试 |
| **Team Sharing** | 分享给另一用户 → 对方面板可见；read 权限不可复制 Key；use 权限可通过代理调用；撤销分享后对方面板不再显示 | E2E 测试 |
| **容器化** | `docker compose up` 一键启动；三服务（app / postgres / redis）正常通信；健康检查通过 | 手动验证 |
| **CI** | push 触发自动测试 + Docker 镜像构建；PR 触发相同流程 | GitHub Actions |

---

## 十、风险与未决问题

| # | 风险 | 概率 | 影响 | 缓解策略 |
|---|------|------|------|----------|
| R1 | **Provider API 不稳定/变更**：服务商修改 API 格式或限频策略 | 高 | 拉取失败、数据显示不全 | 每个 Provider 独立隔离，一个挂不影响其他；异常标记 `status=error` 而非崩溃；`raw_response` 保留原始数据便于回溯 |
| R2 | **国内部分 Provider 无官方 Usage API**：如某些国产模型不提供用量查询接口 | 中 | 用户无法自动追踪这些 Provider | 支持手动录入用量 + CSV 文件导入作为 fallback；自定义 Provider 允许用户配置任何 REST API |
| R3 | **Key 加密密钥泄露**：`KEY_ENCRYPTION_KEY` 环境变量泄露 | 低 | 所有存储的 Key 可被解密 | 环境变量通过 Docker secrets 注入；文档记录密钥轮换预案（MVP 不实现自动轮换） |
| R4 | **Agent 对异步代码产出质量差**：subagent 产出的 Provider 适配器有并发 bug | 中 | Provider 功能异常 | 每个 Provider 必须通过集成测试（含 mock API server）才能合并；代码评审重点检查 async/await 正确性 |
| R5 | **时间紧张**：1-2 周完成 3000-8000 行代码 | 中 | 部分功能未完成 | Provider 优先实现 3 个（OpenAI + Anthropic + DeepSeek），其余用通用适配器；团队功能 MVP 先做基础分享，复杂权限后续迭代 |
| R6 | **前后端分离增加 subagent 协调成本**：React + FastAPI 两边需对齐接口 | 中 | 接口不一致导致集成失败 | API 设计先在 SPEC 中确定；生成 OpenAPI schema 自动给前端生成类型；先做 API 契约测试 |

### 未决问题

1. **费用计算的精度**：各 Provider 的 token 单价和计费粒度不同（有的按 1K tokens，有的按 1M），统一用 USD 计价还是保留原币种？
   - **暂定**：统一换算为 USD（使用固定汇率，MVP 不实时更新），raw_response 保留原始币种数据。
2. **通用 Provider 适配器的认证方式覆盖**：除 API Key Header 外，是否需支持 OAuth Client Credentials / mTLS？
   - **暂定**：MVP 只支持 Bearer Token 和自定义 Header 两种，其余后续扩展。
3. **自部署 vs SaaS**：项目作为课程交付物是自部署容器，但设计上预留多租户能力？
   - **暂定**：按单实例多用户设计，不预留多租户（YAGNI）。

---

## 附录 A：项目命名

正式名称待 brainstorming 后确定，当前代号 **API Vault**。备选：`APIGuard` / `KeyNest` / `AIMeter`。

## 附录 B：术语表

| 术语 | 说明 |
|------|------|
| Provider | AI API 服务商（OpenAI / Anthropic / 通义千问 等） |
| Key | 用户的 API 密钥（如 `sk-...`） |
| Usage Record | 一次用量拉取产生的标准化数据记录 |
| Key Vault | 加密存储和管理 Key 的功能模块 |
| Background Worker | 独立进程，负责定时拉取用量和发送告警 |
