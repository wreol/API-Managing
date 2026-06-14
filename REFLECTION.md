# REFLECTION.md — 反思报告

## 一、Superpowers 技能的实效评估

### 发挥最大作用的

**Brainstorming** 强制在写代码前回答"你到底想做什么"——从模糊的"管理 API"收敛到 6 模块 + 7 用户故事。智能体追问的 6 个关键问题每一个都改变了最终架构。**Subagent-Driven Development** 的新鲜 subagent 每次只做一件事，产物干净专注，219 测试全通过。**TDD 强制**在 AI 协作下是放大器——subagent 只看测试，精确写最少代码变绿。

### 形式大于实质的

**两阶段评审**的 spec reviewer 和 code reviewer 常发现相同问题。对简单 CRUD task 可合并。**Finishing-a-development-branch** 的 4 选项菜单每 worktree 过一遍，流水线开发中保留 3 次分支最后全并到 main。

## 二、TDD 在 AI 协作下的体感

subagent 不抱怨测试、不偷懒、不走捷径。写好失败测试后精确写最少代码——这恰好是 TDD 精髓。但测试质量取决于 task 描述精确度——必须明确列出边界条件。

## 三、Subagent 颗粒度

最优：一个 task = 一组紧密功能（3-5 文件，30-60 分钟）。太细增加调度开销，太粗遗漏边缘功能。

## 四、SPEC 质量影响

**冷启动验证暴露的 3 缺陷是最有价值教训**：EncryptionService 生命周期未定义、密钥派生方式缺失、`__init__.py` 约定缺失。根因：隐性上下文——主 agent 知道的默契，陌生 agent 不存在。

## 五、最有效 Prompt 策略

1. 粘贴 SPEC 字段表而非解释需求
2. 给 subagent 已有代码接口摘要
3. task 描述含边界条件（409/422/401）

## 六、Open Design

Linear 暗色主题确实摆脱了 AI 千篇一律 Material Design 问题。Open Design skill 以文字描述嵌入 prompt 而非直接调用 CLI。

## 七、重做会改变什么

1. Phase 1 就起 Docker（Phase 9 才加导致中间缺集成测试环境）
2. 提前定义模块边界约定写入 PLAN
3. 始终从项目根创建 worktree（避免嵌套）

## 八、方法论批判

Superpowers 假设项目可从 spec 推演——对 CRUD 应用有效，探索性项目摩擦大。假设 subagent 可独立完成——跨模块重构时缺少全局视角。假设 TDD 适合所有场景——标准算法中只确认不发现。

## 九、AI4SE 整体看法

核心洞察：AI 完成编码时，工程师价值在判断力——"做什么"和"做对了吗"。Superpowers 管住 TDD/评审/分支纪律，但不能替你回答产品问题。这个项目中我真正发挥作用的时刻：追问通知渠道缩减、冷启动后修订密钥派生规则、代码评审指出的审计只追加约束。**判断——不是编码——才是工程师在 AI 时代的不可替代性。**
