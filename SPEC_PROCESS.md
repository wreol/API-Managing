# SPEC_PROCESS.md — 规约与计划生成过程

> 记录与 Superpowers 协作生成 SPEC + PLAN 的过程，以及冷启动验证结果。

---

## 一、Brainstorming 关键节点

### 1.1 选题收敛

**初始想法**："做一个查看并管理我的各个 API 以及用量的应用"

**智能体追问的关键问题及影响**：

| # | 追问 | 我的修正 |
|---|------|----------|
| 1 | "管理的 API 是调用的第三方还是自己部署的？" | 明确为**第三方 AI API**，这决定了 Provider 插件架构的核心设计 |
| 2 | "用量数据是自己录入还是自动拉取？" | 选择**对接官方 API 自动拉取**，这引入了 Provider Engine 模块 |
| 3 | "要做多全？" | 选择**全功能版**（仪表盘 + 告警 + 团队共享），而非轻量版 |
| 4 | "安全模型？" | 选择**中等加密 + 审计日志**，而非极端安全的端到端加密 |
| 5 | "前端技术路线？" | 选择**前后端分离 React + FastAPI**，而非 SSR |
| 6 | "通知渠道？" | 最初选了多渠道 Webhook，讨论后**缩减为纯邮件通知**，大幅降低实现复杂度 |

### 1.2 AI 提出我采纳的建议

- **Provider 插件架构**：AI 建议用 `BaseProvider` 抽象类 + 注册表模式，我最初想的是硬编码 switch-case。采纳原因是可扩展性好，且与产品核心价值（支持多服务商）直接对齐
- **key_prefix + last_4 冗余存储**：AI 建议在数据库中冗余存储 Key 前缀和末 4 位，避免渲染列表时解密所有 Key。采纳原因是实际的性能考量
- **Open Design Linear 设计系统**：AI 在评估 71 个设计系统后推荐 Linear（开发者工具审美），我接受

### 1.3 AI 提出我推翻/修正的

- **通知渠道**：AI 最初建议 Webhook + 邮件 + 站内多渠道，我缩减为**纯邮件通知**。理由：1-2 周时间不够，Webhook 格式适配（飞书/钉钉/企业微信各不同）增加不必要的复杂度
- **微服务架构**：AI 提供了微服务选项，我否决。单人项目 3000-8000 行用微服务是过度设计

### 1.4 反思：Superpowers Brainstorming 的优劣

**做得好的地方**：
- 逐步追问机制确实能逼我把模糊想法说清楚
- 多方案对比（A/B/C）让决策有依据
- 设计呈现按节推进，每节签字确认，避免到最后才发现理解偏差

**不满意的地方**：
- 转向 Open Design 选型时，AI 对 Open Design 具体 skill 的了解不够深入（"onboarding" skill 实际不存在，应为 `web-prototype`），需要我自己去 GitHub 翻阅
- 冷启动验证机制是课程要求，不是 brainstorming 自动触发的——这是课程设计的亮点，但 Superpowers 框架本身缺少这一步

---

## 二、冷启动验证

### 2.1 验证设置

| 项目 | 详情 |
|------|------|
| 验证 Task | PLAN Task 2.1: Encryption Service |
| 使用的 Agent | 不同于主开发 agent（另开全新 session） |
| 提供材料 | 仅 `SPEC.md` + `PLAN.md`，无任何口头解释 |
| 产出文件 | `encryption_service.py` (44 行) + `test_encryption.py` (50 行) |

### 2.2 冷启动 agent 产出 vs 预期对比

**结论：代码几乎完全一致。** 加密服务的 AES-256-GCM 实现、测试用例、掩码逻辑均与 PLAN 预期匹配。

唯一差异：agent 的 `decrypt()` 将异常捕获范围扩展到整个方法体（包括 `bytes.fromhex`），比 PLAN 中仅捕获解密部分的 try 块更健壮。

### 2.3 暴露的 SPEC/PLAN 缺陷（3 个）

**缺陷 1：`EncryptionService` 生命周期未定义**
- agent 在测试中手动 `EncryptionService(key_bytes=...)` 构造实例
- 但 SPEC 未说明生产环境中该服务是单例、请求级还是每次 new
- **修订**：SPEC §5.2 新增「服务生命周期与依赖注入」节，明确模块级单例 + Depends 注入

**缺陷 2：`KEY_ENCRYPTION_KEY` → 32 bytes 转换方式缺失**
- SPEC 只说"密钥由环境变量提供"，PLAN 测试直接用裸 32 字节
- 用户设置任意长度字符串时会直接报错
- **修订**：统一为 `hashlib.sha256(env_value.encode()).digest()` 派生

**缺陷 3：`__init__.py` 内容约定缺失**
- PLAN 在 File Structure Map 中列出了 8 个 `__init__.py` 但未指定内容
- agent 创建了空文件——对 Task 2.1 无影响，但后续 subagent 可能往里面放不兼容的逻辑
- **修订**：PLAN 新增 `__init__.py` Conventions 表（8 个包各自职责）

### 2.4 由此对 SPEC/PLAN 的修订

| 文档 | 修订内容 | 版本 |
|------|----------|------|
| SPEC §5.2 | 新增服务生命周期表 | v1.0 → v1.1 |
| SPEC §5.2 + §6 + M2 | 密钥派生规则（SHA-256） | v1.0 → v1.1 |
| SPEC §8 | Open Design 页面→skill 映射表（8 个页面） | v1.0 → v1.1 |
| PLAN File Structure Map | `__init__.py` 约定表 | 新增 |
| PLAN Phase 8 | 前端 task 全部标注对口 Open Design skill + 新增 critique/tweaks task | 重写 |

### 2.5 冷启动验证的启示

**Task 2.1 通过不是因为 SPEC 写得好——是因为 PLAN 对这个 task 给了完整代码。** 真正的考验在于 PLAN 只有目标描述的后半段 task（T5.1 用量服务 / T8.2 仪表盘），那些 task 的 subagent 能否仅凭 SPEC 推导出正确实现，才是 SPEC 质量的真正度量。

冷启动验证暴露的 3 个缺陷本质上都是**隐性上下文**：我和主 agent 在 brainstorming 中共章的对"单例"、"密钥派生"的默契，对陌生 agent 是不存在的。这验证了课程设计的核心论点——"你会严重高估 spec 的清晰度"。

---

## 三、设计迭代记录

### 3.1 关键修订节点

| 轮次 | 触发 | 变更 | 影响 |
|------|------|------|------|
| 1 | 初始 brainstorming | 确定 6 模块 + 7 用户故事 | 架构基线 |
| 2 | 讨论通知渠道 | Webhook 缩减为纯邮件 | 减少 ~500 行代码 |
| 3 | Key 复制机制 | 新增"复制按钮不渲染到 DOM + 审计日志" | M2 功能细化 |
| 4 | 冷启动验证 | 3 个缺陷修复 + Open Design 具体化 | SPEC v1.1 |
| 5 | Open Design 集成 | 下载 Open Design，8 页面→skill 映射 | 前端工作流确定 |

---

## 四、SPEC v1.1 未解决的问题

以下是我有意识搁置到实现阶段再决定的事项：

1. **费用计算精度**：各 Provider token 单价不同，暂定统一换算 USD
2. **泛 Provider 认证方式**：MVP 只支持 Bearer Token 和自定义 Header
3. **多租户**：按单实例多用户设计，不做租户隔离（YAGNI）
