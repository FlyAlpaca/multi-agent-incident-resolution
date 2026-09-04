# Agent 角色与交接规范

## 角色边界

- **入口 Agent（协调者）**：接收用户原始事件请求，维护入口确认、分类与升级、事件范围、工件、问题台账、任务契约、阶段状态和最终交付；在规划完成与验证失败两个节点重建 `active-context.md`；不以协调判断替代独立证据。分类规则以[变更分类器](../references/change-classifier.md)为准，它不是可派发角色。
- **调查 Agent**：只读收集日志、运行态、配置、复现、源码路径和测试入口；可提出候选问题，不把可疑日志直接视为根因。
- **诊断 Agent**：只读建立症状、触发、根因、违反的不变量、待恢复的不变量、影响范围（模块、文件、符号、契约、数据、调用方、测试）与爆炸半径、修复类型和置信度，提出最小修复方向与验收测试；不判断变更分类器的流程路线，也不决定是否启动后续阶段。最小改动模式下它同时是规划者：修复集合冻结且门禁允许后写出 `plan.md` 与单任务 `tasks.yaml`；门禁要求暂停时先交接诊断，再由协调者复用同一 Agent 及其上下文做规划。重构模式下它只停在“哪里错、为什么、影响多大”，**不**负责任务拆分、方案设计和执行顺序。
- **规划 Agent**（`COMPLEX` 或其他 `DEDICATED` 模式派发）：只读、独立上下文（`gpt-5.6-luna/max`）；基于冻结的诊断结果与已选问题集制定修复/重构方案，按独立修复闭环产出 `plan.md` 与 `tasks.yaml`，分析依赖并规划 `sequential`、`parallel` 或 `mixed` 执行模式、顺序和波次，评估并行收益，并在完成前自检可合并项、任务粒度和实施 Agent 数量；不继承诊断 Agent 的工作记忆，不重新判定根因、不改 `REPAIR_TYPE`、不扩大已选问题集，诊断无法支撑安全拆分或调度时回退诊断。
- **实施 Agent（有界池）**：每个 Agent 只负责 `tasks.yaml` 中的一个完整修复闭环任务，是该任务文件范围内的唯一写入者；`TINY` 也使用一个由协调者物化的单任务契约。实施池规模和执行顺序由规划 Agent 按工作流契约确定。只实施已批准、已选择的问题，保留无关改动并记录尝试次数；越界需求、跨任务接缝、分类升级和新增问题一律记录回协调者，不自行扩大范围。
- **集成 Agent**：`POOLED` 实施的所有 Agent 退出后，唯一负责系统整合的写入者：按规划 Agent 已定策略在 `tasks.yaml` 的 `integration_scope` 内解决跨任务不一致、补齐预先规划的连接，并证明整体可装配；即使某个任务最终 `NO_CHANGE` 也不跳过已要求的集成。不修改执行模式、重排任务、重建设计、验收标准或问题范围；契约不足时回退规划，方向问题回退诊断。
- **验证 Agent**：只读判断结果是否符合需求与验收条件：测试执行、功能验证、回归检查、复发扫描、诊断残留检查；不合并、不修复，只报告单任务、跨任务装配、规划契约或修复方向中的责任归属。`TINY` 不派发此角色，由协调者执行限定的快速只读验证；`NORMAL` 和 `COMPLEX` 才派发验证 Agent。确认属于修复缺陷时，由协调者开启新轮次并重新经过诊断、规划，不直接回写入者。
- **独立复核 Agent**：不参与实施与集成且只读；只看需求、最终代码与验证结果，检查是否真正解决问题、是否过度修改、是否引入风险、架构是否合理，返回 `PASS`、`FAIL` 或 `BLOCKED`。

模型路由以 [SKILL.md](../SKILL.md#coordinate-agents) 为准；变更路线以[变更分类器](../references/change-classifier.md)为准；规划、任务池和集成条件以 [workflow.md](../references/workflow.md) 为准。本文只定义角色边界。

Agent 类型、阶段角色与模型路由是三个正交维度；除入口 Agent 外，被派发角色均按 [运行控制交接协议](../references/subagent-state.md#run-control-handoff) 执行有界任务。

角色中的“只读”专指不得修改项目源码；各角色可写入分配给自己的运行工件，验证阶段也可产生仓库规则允许的测试或构建输出。可修改项目源码的只有实施 Agent（限自身任务文件范围）与集成 Agent（限集成阶段内明确的 `integration_scope`）；同一文件在同一时刻不得有两个写入者。

## 上下文边界

拆分的价值来自小上下文与职责隔离：

- 主 Agent 在“规划 → 实施”和“验证失败 → 新修复轮次”执行上下文重置；只把 `active-context.md` 的白名单及其精确引用带入下一阶段，旧聊天、探索过程、完整日志和上一轮实施推导只保留审计用途。`TINY` 没有规划重置，实施上下文仅来自 `classification.md` 与其单任务 `tasks.yaml`；
- 重构模式下的规划 Agent 不继承诊断 Agent 的工作记忆，只读 `evidence.md`、`diagnosis.md`、`issue-ledger.md`、已选问题集与当前差异；最小改动模式下不重新派发规划 Agent，由诊断 Agent 顺带产出单任务拆分；
- 集成 Agent 不继承各实施 Agent 的推导过程，只读 `plan.md`、`tasks.yaml` 与各任务结果；
- `NORMAL`/`COMPLEX` 实施 Agent 只接收已校验的 `active-context.md`、自己的 `tasks.yaml` 条目、相关 `plan.md` 片段、仓库规则、工作区快照、修复轮次与状态路径；`TINY` 实施 Agent 则接收 `classification.md`、单任务契约及同样的仓库和状态边界；
- 不要把整个事件历史、无关任务或无关工件一并塞入；不要让一个 Agent 承担“诊断 + 规划 + 实施”的全部记忆。

## 交接字段

交接只携带该角色完成有界任务所需的事件输入、仓库规则、权限、相关证据、产物与停止条件，并引用持久化的运行控制元数据。实施派发只使用已批准的 `tasks.yaml` 条目；完整派发台账字段见 [artifacts.md](../references/artifacts.md)，运行控制、状态与观察字段见 [subagent-state.md](../references/subagent-state.md)。不得夹带凭据或未脱敏的敏感输出。

## 运行与回显

派发后的状态、观察、干预、终态交接、子 Agent 回收和用户回显均以 [subagent-state.md](../references/subagent-state.md) 为唯一权威来源。

## 路由与升级

每个实际子 Agent 在派发前获得唯一、稳定的披露标签和有界任务；标签格式、复用规则与升级确认以 [confirmation.md](../references/confirmation.md#subagent-routing-disclosure) 为唯一权威来源。

## 运行工件

Skill 创建的证据、草稿、缓存和进度状态均放入当前 `RUN_ARTIFACT_DIR`。完整或提前正常完成后只清理这个经过校验的运行目录；其他退出状态保留工件。边界和脚本调用见 [references/workflow.md](../references/workflow.md#run-artifact-cleanup)。
