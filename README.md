# Multi-Agent Incident Resolution

这是一个面向 Codex 的多 Agent 故障闭环 Skill。它把日志调查、根因诊断、批准修复、回归验证和独立复核组织成有证据、有边界、可暂停恢复的工作流。

## 适用范围

- 生产或开发服务日志中的故障调查
- 测试失败、回归和多问题分诊
- 需要根因、最小修复、验证和独立复核的缺陷处理
- 修复完成后的服务恢复或运行态验证

普通功能开发、没有缺陷证据的重构和单纯代码解释不应调用此 Skill。

## Agent 分工

| Agent | 主要职责 | 默认模型/推理强度 | 权限 |
|---|---|---|---|
| 协调者 | 用户确认、范围、工件、问题台账和交付 | 当前 Agent | 负责工作流协调 |
| 调查 Agent | 日志、运行态、复现和代码路径取证 | `gpt-5.6-luna/max` | 只读 |
| 诊断 Agent | 根因、违反的不变量、问题分类和最小修复建议 | `gpt-5.6-sol/medium` | 只读 |
| 实施 Agent | 按批准集合修改源码和测试 | `gpt-5.6-luna/max` | 唯一写入者 |
| 验证 Agent | focused、回归、质量和复发检查 | `gpt-5.6-luna/max` | 只读 |
| 独立复核 Agent | 对最终差异、证据和策略做对抗性复核 | `gpt-5.6-sol/medium` | 只读 |

实施阶段只允许一个写入者。独立复核 Agent 不得修改、提交、暂存或重置工作区。

## 工作流

1. 确认进入方式和 debug/diagnose/repair/review 范围。
2. 调查并建立事实、触发条件、影响面和问题台账。
3. 独立诊断每个候选问题，区分真实缺陷、正常受控状态和环境限制。
4. 由用户确认修复集合，单一写入者实施最小修复并补测试。
5. 分阶段验证原始故障、回归、复发模式、诊断残留和最终差异。
6. 由未参与实施的独立 Agent 复核，之后才执行交付或服务恢复。

所有 Agent 都必须读取相同的事件输入、仓库规则和本次运行工件目录；不得把凭据、令牌或未经脱敏的敏感日志写入工件。

协调者应按任务规模设置等待窗口，通过有界进度信号区分长时间运行与真实停滞；不得仅因安静或超过固定时限就中断 Agent。每个子 Agent 的终态结论（包括失败、阻塞和取消）都必须先由协调者在主界面回显，再进入下一阶段，并在最终 `处理总结` 中综合呈现。完整规则见 [`references/workflow.md`](references/workflow.md#subagent-liveness-and-result-visibility)。

在**自动全流程**模式中，只要面向用户提到某个实际计划、运行中或已结束的子 Agent，就必须同时说明该 Agent 的角色或稳定标识、精确模型和推理强度；派发前还必须说明有界任务。并行批次应逐个披露，模型替换也必须先披露后执行。自动执行只免除常规阶段确认，不免除路由透明度。

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

因此仓库目录中的修改会立即对全局 Skill 生效，不需要复制或轮询同步。运行以下命令可以安全地检查或建立链接；如果目标路径指向其他内容，脚本会拒绝覆盖：

```sh
scripts/sync-global-skill.sh
```

脚本默认使用 `${HOME}/.agents/skills`；需要不同位置时可显式设置 `GLOBAL_SKILLS_ROOT`。本环境的实际全局 Skill 根目录是 `/home/hao/.agents/skills`，不使用 `CODEX_HOME` 下的同名目录。

不要直接维护全局目录中的独立副本，也不要重新创建旧的 `debug-repair` Skill 目录。

## 后续迭代

修改 `SKILL.md`、`agents/openai.yaml` 或 `references/` 后，至少运行：

```sh
python3 /run/host/codex/skills/.system/skill-creator/scripts/quick_validate.py .
git diff --check
scripts/sync-global-skill.sh
```

涉及流程行为、Agent 路由、工件字段或确认语义的变更，应同时更新对应参考文档，并在提交说明中记录影响范围、验证命令和同步状态。
