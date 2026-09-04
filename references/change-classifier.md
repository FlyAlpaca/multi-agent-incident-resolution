# 变更分类器（Change Classifier）

变更分类器是入口确认后的固定规则求值器，不是 Agent、工作流阶段或诊断角色。它把协调者归一化的变更信封映射为 `TINY`、`NORMAL` 或 `COMPLEX` 路线；规则求值本身不检查仓库、不调用独立模型、不派发 Agent、不授予权限，也不判断根因。

它只用于需要修改源码的 `debug` 和 `repair`。`diagnose`、`review` 以及 **Codex 原生处理** 不进入分类流程。协调者必须在首个 Skill 阶段前把结果写入 `classification.md`；分类不增加用户菜单或阶段门禁。

## 输入与输出

分类器只接受结构化变更信封。协调者无法从用户明确提供的事实中确定字段时使用 `UNKNOWN`，不能把“简单”“小改”“应该没风险”等形容词当作指标。后续调查可由协调者用有来源的事实补全信封，再按同一规则求值。

```yaml
change_scope:
  affected_files: 1 | UNKNOWN       # 预计会写入的文件数，不含只读查看的文件
  affected_paths: [path/to/file]    # TINY 必须给出且数量与 affected_files 一致
  estimated_changes: 8 | UNKNOWN    # 归一化后的增删行数

risk:
  api_change: false | true | UNKNOWN
  database_change: false | true | UNKNOWN
  schema_change: false | true | UNKNOWN
  architecture_change: false | true | UNKNOWN

dependency:
  cross_module: false | true | UNKNOWN
  external_dependency: false | true | UNKNOWN
```

`api_change` 包括公开函数、导出符号、消息或协议签名变化；`database_change` 包括持久化逻辑、数据迁移和数据库内容变化；`schema_change` 包括序列化、配置和数据契约；`architecture_change` 包括模块边界、生命周期、并发、状态机或核心抽象变化。`cross_module` 表示变更行为跨越模块边界，`external_dependency` 表示引入、升级、移除或改变第三方/工具链/运行时依赖。

输出记录 `CHANGE_CLASSIFIER_STATUS: COMPLETE | INCOMPLETE | UPGRADED`、`CHANGE_CLASSIFICATION: TINY | NORMAL | COMPLEX`、决定性指标、数据来源和写入前是否需要重分类。忽略调用方提供的分类标签。输入信封、重分类和升级历史集中保存在当前 `RUN_ARTIFACT_DIR/classification.md`，不另建路由台账。

## 固定决策

按以下顺序求值，先命中复杂条件，再判断 `TINY`：

1. 任一风险或依赖字段为 `true`，或 `affected_files > 5`，或 `estimated_changes > 200`，结果为 `COMPLEX`。
2. 只有同时满足以下条件才是 `TINY`：写入目标明确；`affected_files == 1`；`affected_paths` 恰好一个；`estimated_changes <= 20`；全部风险和依赖字段都明确为 `false`。
3. 其余情况为 `NORMAL`。字段缺失、未知或彼此不一致时同时记录 `INCOMPLETE`：可以先调查和诊断，但写入前必须补齐信封并重新求值；仍无法完成时阻塞，不能借未知值进入 `TINY` 或无证据升级。

这些阈值是唯一的路线判定规则，不随用户措辞变化。

分类器的 `classification` 与诊断阶段的 `REPAIR_TYPE: MINIMAL | STRUCTURAL | MIXED` 互不替代：前者决定需要哪些流程角色，后者描述已确认根因应采用的修复形态。诊断员仍负责后者，不负责前者。

## 路由契约

| 分类 | `debug` / `repair` 路线 | 明确省略 | 写入前硬门槛 |
|---|---|---|---|
| `TINY` | 入口协调者物化单任务契约 → 一个实施 Agent → 协调者快速只读验证 | 调查、诊断、规划、集成 Agent、独立复核 | 只能是单文件、`SINGLE`、`INTEGRATION_REQUIRED: NO`；任务必须有精确 `file_scope` 和可检查的验收条件 |
| `NORMAL` | `debug` 先调查、诊断；`repair` 校验已有诊断；之后 `INLINE` 规划 → 一个实施 Agent → 验证 Agent | 集成 Agent、独立复核 | 写入前所有指标必须确认且无复杂条件；必须仍是一个完整修复闭环，否则先升级 |
| `COMPLEX` | `debug` 先调查、诊断；`repair` 校验已有诊断；之后独立规划 → 实施 → 按需集成 → 验证 → 独立复核 | 无 | 规划使用 `DEDICATED`；只有 `POOLED` 才执行集成。是否拆分仍遵守任务闭环与并行安全条件 |

`TINY` 不经过阶段 3，但协调者仍从已确认的信封生成一个最小 `tasks.yaml`；这是写入边界和验收条件登记，不是规划。`NORMAL` 的 `INLINE` 规划仍受修复选择、任务契约和上下文门禁约束。入口、权限、高影响操作和安全边界不会因分类而消失。

集成由任务拓扑唯一决定：`SINGLE -> INTEGRATION_REQUIRED: NO`，`POOLED -> INTEGRATION_REQUIRED: YES`。`COMPLEX` 要求独立规划和独立复核，但不为单任务额外设置集成写入阶段。

分类不扩展 `RUN_MODE`。`repair` 只有在已有诊断缺失、过期或被新证据推翻时才返回调查/诊断；独立 `diagnose` 和 `review` 始终保持只读范围。

## 单向升级

分类只允许在当前运行中向更重路线升级，不允许根据后续“看起来更简单”降级，以免丢失已建立的质量门禁。升级由协调者依据新获得的结构化事实应用同一规则；Agent 只能报告事实或 `UPGRADE_REQUESTED`，不能自行改路由。

以下新事实必须在下一次写入或阶段切换前重新求值，并在命中更高路线时升级：

- 实际文件数或变更量超过信封；
- 发现跨模块、公开接口、数据库/数据结构、架构、并发、生命周期或外部依赖影响；
- `TINY` 实施 Agent 发现需要重新设计、第二个独立修复闭环或共享接缝；
- `TINY` 快速验证发现界内失败，且不能在原单文件边界内可靠解决；
- `NORMAL` 的诊断/规划无法保持单任务、单模块、无集成的执行形态；
- 验证失败表明问题属于修复方向、任务边界或跨模块装配，而非环境或既有基线。

升级时：

1. 先让当前 Agent 完成终态交接并回收；活动的实施 Agent 不能通过追加指令改造路线。
2. 在 `classification.md` 追加新指标、触发条件、旧/新分类、当前版本标识和影响阶段；不覆盖旧结论。
3. 在下一阶段门禁前由协调者重新校验分类和授权。已完成且仍有效的调查/诊断证据可以复用，但不为改标签而重复阶段。
4. `TINY` 升级到 `NORMAL` 后补充调查、诊断和规划；`NORMAL` 升级到 `COMPLEX` 后使用独立规划 Agent 和独立复核 Agent，若任务拓扑升级为 `POOLED` 再执行集成。
5. `TINY` 快速验证的界内失败按验证失败修复轮次保存不可变证据，再进入 `NORMAL` 的新诊断/规划闭环；环境或既有失败只保留为阻塞，不自动重试或升级。

每次升级都保留累计实施 `attempt`、`REPAIR_ROUND` 和既有任务记录；升级不是重置尝试次数，也不是扩大用户授权。分类状态、路由原因和升级历史由 `classification.md` 单独作为权威来源，其他文档只引用它。
