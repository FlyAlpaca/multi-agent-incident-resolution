# Multi-Agent Incident Resolution

面向 Codex 的多 Agent 故障闭环 Skill：以证据和权限边界组织调查、根因诊断、批准修复、回归验证与独立复核，并支持暂停和恢复。

## 适用范围

适用于复杂服务故障、回归、多问题分诊，以及明确要求分阶段 diagnose/repair/review 的任务。普通单缺陷修复、无缺陷证据的功能开发、普通重构或单纯代码解释不应自动触发此 Skill。

## 工作流

1. 确认运行方式与 `debug`、`diagnose`、`repair` 或 `review` 范围。
2. 调查事实、触发条件、影响面和候选问题；若没有可信问题，立即结束。
3. 诊断根因、违反的不变量、修复类型和验收标准；若无需或未选择修改，立即结束。
4. 用户选择修复集合后，由唯一写入者实施。
5. 验证原始故障、focused test、相关回归、复发模式和诊断残留。
6. 由未参与实施的只读 Agent 独立复核，再完成交付或经授权的服务恢复。

角色职责、默认路由与交接字段见 [Agent 角色与交接规范](docs/agent-roles.md)。

## 核心约束

- 入口菜单、单步检查点、修复选择和 Agent 升级统一使用 [确认协议](references/confirmation.md)。
- 调查、实施、验证、独立复核、运行健康和终态回显统一使用 [工作流协议](references/workflow.md)。
- 多问题分诊和修复集合选择统一使用 [多问题协议](references/multi-issue.md)。
- 运行元数据、派发台账和终态标记统一使用 [工件协议](references/artifacts.md)。
- 子 Agent 的 Work Step、Checkpoint、生命周期状态、停滞判断和终止后证据保留统一使用 [状态与超时协议](references/subagent-state.md)。

所有 Agent 读取同一事件输入、仓库规则与运行目录。实施阶段只有一个源码写入者；不得把凭据、令牌或未脱敏的敏感输出写入工件。

完整阶段链路是上限而非强制清单。提前结束原因会区分无可信问题、无可执行修复、用户未选择修复、修改已存在和审查范围为空；跳过的阶段不伪造通过标记。

子 Agent 状态与终态交接以 [状态与超时协议](references/subagent-state.md) 为唯一权威来源，路由标签与升级授权以 [确认协议](references/confirmation.md) 为唯一权威来源。完整或提前正常完成时仅清理当前已校验的 `RUN_ARTIFACT_DIR`，其他退出状态保留工件。

## 全局 Skill 同步

仓库目录是唯一维护源：

```text
/workspace/multi-agent-incident-resolution
```

全局 Skill 使用符号链接：

```text
/home/hao/.agents/skills/multi-agent-incident-resolution
  -> /workspace/multi-agent-incident-resolution
```

仓库修改会直接生效。以下脚本用于检查或安全建立链接；若目标已指向其他内容，它会拒绝覆盖：

```sh
scripts/sync-global-skill.sh
```

脚本默认使用 `${HOME}/.agents/skills`，也可显式设置 `GLOBAL_SKILLS_ROOT`。不要维护独立全局副本或恢复旧的 `debug-repair` Skill。

## 修改验证

修改 Skill 或参考文档后至少运行：

```sh
python3 /run/host/codex/skills/.system/skill-creator/scripts/quick_validate.py .
git diff --check
scripts/sync-global-skill.sh
```

涉及流程行为、路由、工件字段或确认语义时，同步更新其权威协议；其他文件只保留必要入口和链接，避免复制规则。
