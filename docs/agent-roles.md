# Agent 角色与交接规范

## 角色边界

- **入口 Agent（协调者）**：接收用户原始事件请求，维护入口确认、分类与升级、事件范围、工件、问题台账、任务契约、阶段状态和最终交付；在 `NORMAL` 内联契约或 `COMPLEX` 规划完成后、以及验证失败后重建 `active-context.md`；默认负责 `NORMAL` 基础验证，不以协调判断替代应升级的独立验证。分类规则以[变更分类器](../references/change-classifier.md)为准，它不是可派发角色。
- **调查 Agent**：仅在 `COMPLEX` 独立派发，只读收集日志、运行态、配置、复现、源码路径和测试入口；可提出候选问题，不把可疑日志直接视为根因。`NORMAL` 和独立 `diagnose` 由 Diagnoser 合并完成这些工作。
- **Diagnoser（诊断 Agent）**：始终只读。`NORMAL` 和独立 `diagnose` 中，它一次完成基础调查、日志与代码路径分析、根因和不变量判断、影响范围、修复类型、最小修复方向及验收测试，统一写入 `diagnosis.md`；`NORMAL` 的修复集按[多问题协议](../references/multi-issue.md#freeze-the-repair-set-by-run-control)冻结后，还在同一工件内写简单修复契约并生成单任务 `tasks.yaml`，记录 `TASK_CONTRACT_MODE: DIAGNOSER_INLINE`，规划阶段保持跳过。`COMPLEX` 中，它基于独立 `evidence.md` 只回答“哪里错、为什么、影响多大”，不负责任务拆分、结构设计和执行顺序。它发现结构性、多问题、多模块、多任务、集成或并行需求时请求升级，不在 `NORMAL` 内展开。
- **规划 Agent**（仅 `COMPLEX`/`DEDICATED` 派发）：只读、独立上下文（`gpt-5.6-luna/max`）；基于冻结的诊断结果与修复集制定修复/重构方案，按独立修复闭环产出 `plan.md` 与 `tasks.yaml`，分析依赖并规划 `sequential`、`parallel` 或 `mixed` 执行模式、顺序和波次，评估并行收益，并在完成前自检可合并项、任务粒度和实施 Agent 数量；不继承 Diagnoser 的工作记忆，不重新判定根因、不改 `REPAIR_TYPE`、不扩大冻结修复集，诊断无法支撑安全拆分或调度时回退诊断。
- **实施 Agent（有界池）**：每个 Agent 只负责 `tasks.yaml` 中的一个完整修复闭环任务，是该任务文件范围内的唯一写入者；`TINY` 使用协调者物化的单任务契约，`NORMAL` 使用 Diagnoser 的单任务契约，`COMPLEX` 使用 Planner 的任务契约。只实施已批准的冻结修复集，保留无关改动并记录尝试次数；越界需求、跨任务接缝、分类升级和新增问题一律记录回协调者，不自行扩大范围。
- **集成 Agent**：`POOLED` 实施的所有 Agent 退出后，唯一负责系统整合的写入者：按规划 Agent 已定策略在 `tasks.yaml` 的 `integration_scope` 内解决跨任务不一致、补齐预先规划的连接，并证明整体可装配；即使某个任务最终 `NO_CHANGE` 也不跳过已要求的集成。不修改执行模式、重排任务、重建设计、验收标准或问题范围；契约不足时回退规划，方向问题回退诊断。
- **验证 Agent**：只读判断结果是否符合需求与验收条件：测试执行、功能验证、回归检查、复发扫描、诊断残留检查；不合并、不修复，只报告单任务、跨任务装配、规划契约或修复方向中的责任归属。`COMPLEX` 默认派发；`NORMAL` 默认由协调者验证，仅在修改/回归范围扩大、协调者检查失败或归因不清、残余风险升高时派发；`TINY` 始终由协调者快速验证。确认属于修复缺陷时，由协调者开启新轮次并重新经过诊断，`COMPLEX` 再规划，不能直接回写入者。
- **独立复核 Agent**：不参与实施与集成且只读；只看需求、最终代码与验证结果，检查是否真正解决问题、是否过度修改、是否引入风险、架构是否合理，返回 `PASS`、`FAIL` 或 `BLOCKED`。

模型路由以 [SKILL.md](../SKILL.md#coordinate-agents) 为准；变更路线以[变更分类器](../references/change-classifier.md)为准；规划、任务池和集成条件以 [workflow.md](../references/workflow.md) 为准。本文只定义角色边界。

Agent 类型、阶段角色与模型路由是三个正交维度；除入口 Agent 外，被派发角色均按 [运行控制交接协议](../references/subagent-state.md#run-control-handoff) 执行有界任务。

角色中的“只读”专指不得修改项目源码；各角色可写入分配给自己的运行工件，验证阶段也可产生仓库规则允许的测试或构建输出。可修改项目源码的只有实施 Agent（限自身任务文件范围）与集成 Agent（限集成阶段内明确的 `integration_scope`）；同一文件在同一时刻不得有两个写入者。

## 上下文边界

拆分的价值来自小上下文与职责隔离：

- 主 Agent 在“`NORMAL` 内联契约或 `COMPLEX` 规划 → 实施”和“验证失败 → 新修复轮次”执行上下文重置；只把 `active-context.md` 的白名单及其精确引用带入下一阶段，旧聊天、探索过程、完整日志和上一轮实施推导只保留审计用途。`TINY` 没有规划重置，实施上下文仅来自 `classification.md` 与其单任务 `tasks.yaml`；
- `COMPLEX` 的规划 Agent 不继承 Diagnoser 的工作记忆，只读 `evidence.md`、`diagnosis.md`、`issue-ledger.md`、冻结修复集与当前差异；`NORMAL` 不派发规划 Agent，Diagnoser 在 `diagnosis.md` 内联简单修复契约并产出单任务 `tasks.yaml`；
- 集成 Agent 不继承各实施 Agent 的推导过程，只读 `plan.md`、`tasks.yaml` 与各任务结果；
- `NORMAL` 实施 Agent 只接收已校验的 `active-context.md`、自己的 `tasks.yaml` 条目、`diagnosis.md` 的相关内联契约、仓库规则、工作区快照、修复轮次与状态路径；`COMPLEX` 额外接收相关 `plan.md` 片段；`TINY` 实施 Agent 则接收 `classification.md`、单任务契约及同样的仓库和状态边界；
- 不要把整个事件历史、无关任务或无关工件一并塞入；不要让一个 Agent 承担“诊断 + 规划 + 实施”的全部记忆。

## 交接字段

交接只携带该角色完成有界任务所需的事件输入、仓库规则、权限、相关证据、产物与停止条件，并引用持久化的运行控制元数据。实施派发只使用已批准的 `tasks.yaml` 条目；完整派发台账字段见 [artifacts.md](../references/artifacts.md)，运行控制、状态与观察字段见 [subagent-state.md](../references/subagent-state.md)。不得夹带凭据或未脱敏的敏感输出。

## 运行与回显

派发后的状态、观察、干预、终态交接、子 Agent 回收和用户回显均以 [subagent-state.md](../references/subagent-state.md) 为唯一权威来源。

## 路由与升级

每个实际子 Agent 在派发前获得唯一、稳定的披露标签和有界任务；标签格式、复用规则与升级确认以 [confirmation.md](../references/confirmation.md#subagent-routing-disclosure) 为唯一权威来源。

## 运行工件

Skill 创建的证据、草稿、缓存和进度状态均放入当前 `RUN_ARTIFACT_DIR`。完整或提前正常完成后只清理这个经过校验的运行目录；其他退出状态保留工件。边界和脚本调用见 [references/workflow.md](../references/workflow.md#run-artifact-cleanup)。
