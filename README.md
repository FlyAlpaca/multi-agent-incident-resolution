# Multi-Agent Incident Resolution

面向 Codex 的多 Agent 事件处理 Skill：显式调用直接进入自动全流程，隐式触发先完成入口确认，再按固定规则选择最小安全路线。`NORMAL` 合并调查与诊断，`COMPLEX` 保留完整多 Agent 闭环。

## 适用范围

适用于源码故障与回归修复、多问题分诊、大型重构或多模块修复，以及明确要求分阶段 `diagnose`、`repair`、`review` 或多 Agent 协作的任务。普通功能开发、代码解释和不需要分阶段协调的常规修改不应自动触发。

## 工作流

需要修改源码的请求先进入[变更分类器](references/change-classifier.md)：`TINY` 采用有界单任务路线；`NORMAL` 采用“只读 Diagnoser（合并调查、诊断和简单修复契约）→ 独立 Implementer → 协调者基础验证”；`COMPLEX` 保留独立调查、诊断、规划、实施、按需集成、验证和独立复核。分类只决定路线，不扩大权限；指标未知时不得进入 `TINY`，运行中只允许向更重的路线升级。

`NORMAL` 不派发独立调查 Agent、规划 Agent 或默认验证 Agent；只有修改或回归范围扩大、协调者验证失败或归因不清、残余风险升高时才升级独立验证 Agent。结构性、多问题、多模块、多任务、迁移、集成或并行需求先升级为 `COMPLEX`，不能在 `NORMAL` 内静默扩张。Diagnoser 始终只读，源码修改只交给 Implementer，从而保留“先分析后实现”的隔离边界。

`COMPLEX` 规划先按完整修复闭环形成任务，再决定依赖、执行波次和执行模式。`SINGLE` 由一个实施 Agent 完成并跳过集成；`POOLED` 仅在任务可独立闭环且写入范围互斥时使用，并在所有实施 Agent 停止后，由一个集成 Agent 在明确的 `integration_scope` 内完成整合。`NORMAL` 固定为一个完整闭环、一个任务、一个 Implementer。

`NORMAL` 内联修复契约或 `COMPLEX` 规划进入实施前，以及修复验证失败进入新轮次前，协调者会重建 `active-context.md` 白名单。旧探索保留为审计记录，不继续占用下一阶段上下文；升级和新轮次都不重置累计尝试次数。

## 权威协议

- Skill 入口、适用范围和核心安全边界：[SKILL.md](SKILL.md)
- 分类输入、阈值、路线与升级：[变更分类器](references/change-classifier.md)
- 阶段、早退、规划、实施、集成、验证与退出：[工作流协议](references/workflow.md)
- 用户菜单与 Agent 路由披露：[确认协议](references/confirmation.md)
- 多问题分诊与修复集：[多问题协议](references/multi-issue.md)
- 运行工件、`tasks.yaml` 与终态字段：[工件协议](references/artifacts.md)
- 子 Agent 状态、观察、终止与回收：[状态协议](references/subagent-state.md)
- 角色职责与上下文边界：[Agent 角色规范](docs/agent-roles.md)

完整关系图见 [skill-architecture.md](skill-architecture.md)。各项规则只在对应权威文件维护，其他文档仅提供入口和引用。

## 全局 Skill 同步

仓库目录是唯一维护源：

```text
<repository-root>/multi-agent-incident-resolution
```

全局 Skill 使用符号链接：

```text
${HOME}/.codex/skills/multi-agent-incident-resolution
  -> <repository-root>/multi-agent-incident-resolution
```

仓库修改会直接生效。以下脚本用于检查或安全建立链接；若目标已指向其他内容，它会拒绝覆盖：

```sh
sh scripts/sync-global-skill.sh
```

脚本默认使用 `${HOME}/.codex/skills`，也可显式设置 `GLOBAL_SKILLS_ROOT`。不要维护独立全局副本或恢复旧的 `debug-repair` Skill。

## 修改验证

修改 Skill 或参考文档后至少运行：

```sh
python3 "${HOME}/.codex/skills/.system/skill-creator/scripts/quick_validate.py" .
python3 scripts/validate-test-prompts.py test-prompts.json
python3 scripts/test-subagent-stop-eligibility.py
sh -n scripts/*.sh
git diff --check
sh scripts/sync-global-skill.sh
```

涉及流程行为、路由、工件字段或确认语义时，同步更新其权威协议；其他文件只保留必要入口和链接，避免复制规则。

测试提示采用独立输入：菜单选择、`RUN_CONTROL` 和其他阶段状态直接写在同一条 `prompt` 中，不依赖上一轮对话。`scripts/validate-test-prompts.py` 只使用 Python 标准库检查提示集结构和唯一编号。

## 许可证

本项目采用 [Apache License 2.0](LICENSE) 开源协议。
