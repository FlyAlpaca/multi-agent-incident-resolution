# Multi-Agent Incident Resolution Skill 架构图

> 本图描述当前 skill 的运行时架构、阶段流转、角色边界、协议依赖和运行工件关系。

```mermaid
flowchart TB
    U["用户请求 / 事件输入"] --> E{"入口确认\n1 自动全流程\n2 单步确认\n3 Codex 原生处理"}
    E -- "3：停用本 skill 工作流" --> N["Codex 默认工作流"]
    E -- "1 / 2" --> R{"范围路由\ndebug / diagnose / repair / review"}

    subgraph C["协调与控制层"]
        CO["协调者（当前 Agent）\n用户门禁 · 事件范围 · 问题选择\n工件 · 任务拆分 · 冲突处理 · 终态"]
        SAFE["证据与安全边界\n最小影响面 · 权限 · 敏感信息\n不变量 · 工作区快照"]
        CTX["阶段上下文重置\nactive-context.md\n规划→实施 / 验证失败→新轮次"]
        LIMIT["修复边界\nMINIMAL / STRUCTURAL\n每个方向最多两次实施尝试"]
    end

    R --> CO
    CO --> SAFE
    CO --> LIMIT

    subgraph P["七阶段工作流（按范围和早退规则裁剪）"]
        S1["1 调查\n复现、日志、运行态、源码路径\n只读 → evidence.md"]
        S2["2 诊断\n根因、不变量、影响面、分类\n只读 → diagnosis.md"]
        SEL["修复选择门禁\n冻结 SELECTED_ISSUES"]
        S3["3 规划\n修复闭环、依赖、执行模式与波次\n→ plan.md + tasks.yaml"]
        S4["4 实施\nsequential / parallel / mixed\n按 wave 与 file_scope 执行"]
        S5["5 集成（按需）\nPOOLED 后由 Integrator\n在 integration_scope 内整合"]
        S6["6 验证\n聚焦、回归、质量、复发扫描\n只读报告"]
        S7["7 独立复核\n对需求、代码、验证结果\n对抗式只读审查"]
        OUT["完成 / 提前正常结束\n处理总结 + 清理当前 RUN_ARTIFACT_DIR"]

        S1 --> S2 --> SEL --> S3 --> S4 --> S5 --> S6 --> S7 --> OUT
        S4 -. "SINGLE：跳过集成" .-> S6
        S6 -. "修复缺陷：新 REPAIR_ROUND" .-> CTX
        CTX -. "回到新一轮诊断" .-> S2
        S6 -. "发现新候选问题" .-> LEDGER["issue-ledger.md\n回到诊断与修复选择"]
        LEDGER -.-> S2
    end

    CO --> S1
    CO --> CTX
    CO --> OUT

    subgraph A["角色执行层"]
        I["Investigator\n调查 Agent · 只读"]
        D["Diagnostician\n诊断 Agent · 只读\nMINIMAL 时可 INLINE 规划"]
        PL["Planner\n闭环拆分 · 依赖分析 · 执行模式\n并行收益评估 · 执行前自检"]
        IMP["Implementer Pool（按规划有界）\n每个任务独占 file_scope\n规模由闭环与预算门禁决定"]
        INT["Integrator\n实施池全部退出后单独整合\n唯一 integration_scope 写入者"]
        V["Verifier\n验证 Agent · 只读"]
        RV["Independent Reviewer\n独立复核 Agent · 只读"]
    end

    S1 -. "执行者" .-> I
    S2 -. "执行者" .-> D
    S3 -. "INLINE / DEDICATED" .-> D
    S3 -. "STRUCTURAL / MIXED" .-> PL
    S4 -. "执行者" .-> IMP
    S5 -. "条件执行" .-> INT
    S6 -. "执行者" .-> V
    S7 -. "执行者" .-> RV

    subgraph K["协议、状态与运行工件层"]
        CONF["confirmation.md\n入口 / 阶段 / 升级 / 修复选择门禁"]
        WF["workflow.md\n阶段协议 / 早退 / 上下文重置 / 完成总结"]
        MI["multi-issue.md\n问题归一化 / 修复集合选择 / 复发扫描"]
        ART["artifacts.md\nRUN 元数据 / tasks.yaml / 终态标记"]
        STATE["subagent-state.md\nstate.md / result.md / 派发、观察、回收"]
        ROLES["docs/agent-roles.md\n角色职责 / 上下文白名单 / 交接边界"]
        RUN["RUN_ARTIFACT_DIR\n证据、计划、状态、审计工件"]
        EVID["evidence.md → diagnosis.md\n→ plan.md → tasks.yaml"]
        STATEFILES["active-context.md\nstate.md / result.md / dispatch ledger"]
    end

    CONF --> CO
    WF --> CO
    MI --> SEL
    MI --> LEDGER
    ART --> RUN
    ART --> S4
    STATE --> IMP
    STATE --> INT
    ROLES --> D
    ROLES --> PL
    ROLES --> IMP
    RUN --> EVID
    RUN --> STATEFILES
    S1 --> EVID
    S2 --> EVID
    S3 --> EVID
    S4 --> STATEFILES
    S5 --> STATEFILES
    S6 --> STATEFILES

    subgraph X["退出与清理"]
        CTXCLEAN["仅完整或提前正常完成：\n清理上下文\n不再携带阶段推导"]
        CLEAN["仅完整或提前正常完成：\n清理已校验的当前运行目录"]
        KEEP["partial / failed / blocked / stopped /\ncancelled / paused：保留工件，可恢复或审计"]
    end
    OUT --> CTXCLEAN --> CLEAN
    S1 -. "早退" .-> OUT
    S2 -. "无可执行修复 / 不修复" .-> OUT
    S3 -. "无可执行任务" .-> OUT
    S6 -. "已存在变更且验证通过" .-> OUT
    S7 -. "空 review 范围" .-> OUT
    CO -. "停止条件或未获授权" .-> KEEP

    classDef control fill:#e8f1ff,stroke:#3b73b9,color:#12324a;
    classDef stage fill:#eef8ee,stroke:#4b8f5a,color:#173b1d;
    classDef role fill:#fff5df,stroke:#b07a17,color:#4a3100;
    classDef contract fill:#f4edff,stroke:#7956ad,color:#2e1c50;
    classDef exit fill:#ffeaea,stroke:#b84a4a,color:#4a1717;

    class E,CO,SAFE,CTX,LIMIT,R control;
    class S1,S2,SEL,S3,S4,S5,S6,S7,OUT,LEDGER stage;
    class I,D,PL,IMP,INT,V,RV role;
    class CONF,WF,MI,ART,STATE,ROLES,RUN,EVID,STATEFILES contract;
    class N,CTXCLEAN,CLEAN,KEEP exit;
```

## 文件映射

| 架构区域 | 当前目录中的权威文件 |
| --- | --- |
| Skill 入口与全局约束 | `SKILL.md` |
| 运行阶段、早退、规划模式、清理 | `references/workflow.md` |
| 用户确认与 Agent 路由披露 | `references/confirmation.md` |
| 多问题发现与修复集合选择 | `references/multi-issue.md` |
| 运行工件、任务契约与终态标记 | `references/artifacts.md` |
| 子 Agent 状态、观察、终止与回收 | `references/subagent-state.md` |
| 角色职责、上下文边界与交接 | `docs/agent-roles.md` |
| 全局同步与运行目录清理 | `scripts/sync-global-skill.sh`、`scripts/cleanup-run-artifacts.sh` |
