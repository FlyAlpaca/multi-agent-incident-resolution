# Multi-Agent Incident Resolution 架构图

> 本图描述当前 Skill 的运行时架构、路线边界、角色隔离、协议依赖和运行工件关系。

```mermaid
flowchart TB
    U["用户请求 / 事件输入"] --> E{"入口确认\n1 自动全流程\n2 单步确认\n3 Codex 原生处理"}
    E -- "3：停用本 Skill 工作流" --> N["Codex 默认工作流"]
    E -- "1 / 2" --> R{"范围路由\ndebug / diagnose / repair / review"}
    R --> CO

    subgraph C["协调与控制层"]
        CO["协调者（当前 Agent）\n用户门禁 · 分类升级 · 范围\n任务契约 · NORMAL 验证 · 终态"]
        SAFE["证据与安全边界\n最小影响面 · 权限 · 敏感信息\n不变量 · 工作区快照"]
        CTX["阶段上下文重置\nNORMAL 内联契约 / COMPLEX 规划 → 实施\n验证失败 → 新轮次"]
        LIMIT["修复边界\nMINIMAL / STRUCTURAL\n每个方向最多两次实施尝试"]
    end

    CO --> SAFE
    CO --> LIMIT
    CO -- "需修改源码的 debug / repair" --> CL{"变更分类器\n固定规则求值"}
    CL --> ROUTE{"TINY / NORMAL / COMPLEX\n单向升级"}
    CO -- "diagnose" --> ND
    CO -- "review" --> SR["Independent Reviewer（独立复核 Agent，只读）"]

    subgraph T["TINY 快速路径"]
        TI["协调者物化单任务 tasks.yaml"] --> TIMP["一个 Implementer（实施 Agent）"] --> TV["协调者快速验证"]
    end
    ROUTE -- "TINY" --> TI

    subgraph NM["NORMAL：合并诊断的安全短链"]
        ND["Diagnoser（诊断 Agent，只读）\n基础调查 + 日志/代码路径分析\n根因 + 修复方向\n统一 diagnosis.md"]
        NC["同一诊断 Agent（仍只读）\n修复选择后内联简单修复契约\n→ 单任务 tasks.yaml"]
        NIMP["一个 Implementer（实施 Agent）\n唯一源码写入者"]
        NV["协调者基础验证"]
        VE{"需要独立 Verifier？\n范围扩大 / 检查失败或归因不清 / 风险升高"}
        NIV["Verifier（独立验证 Agent，只读）"]
        NS{"只读 diagnose 范围？"}
        ND --> NS
        NS -- "否 / NORMAL debug 或 repair" --> NC --> NIMP --> NV --> VE
        NS -- "是" --> NOUT
        VE -- "否" --> NOUT["NORMAL 完成"]
        VE -- "是" --> NIV --> NOUT
    end
    ROUTE -- "NORMAL" --> ND

    subgraph CP["COMPLEX：完整多 Agent 路径"]
        CI["1 Investigator（调查 Agent，只读）\n→ evidence.md"]
        CD["2 Diagnoser（诊断 Agent，只读）\n→ diagnosis.md"]
        SEL["修复选择门禁\n冻结 SELECTED_ISSUES"]
        CPL["3 Planner（规划 Agent，只读）\n独立上下文 → plan.md + tasks.yaml"]
        CIMP["4 Implementer（实施 Agent）池\nsequential / parallel / mixed"]
        IG{"POOLED?"}
        CINT["5 Integrator（集成 Agent）\nintegration_scope 唯一写入者"]
        CV["6 Verifier（验证 Agent，只读）"]
        CR["7 Independent Reviewer（独立复核 Agent，只读）"]
        CI --> CD --> SEL --> CPL --> CIMP --> IG
        IG -- "是" --> CINT --> CV
        IG -- "否 / SINGLE" --> CV
        CV --> CR --> COUT["COMPLEX 完成"]
    end
    ROUTE -- "COMPLEX" --> CI

    ND -. "结构性 / 多问题 / 多模块 / 多任务\n迁移 / 集成 / 并行 / COMPLEX 风险" .-> CUP["协调者重分类并升级 COMPLEX"] --> CPL
    TV -. "界内失败：重分类" .-> TUP["升级 NORMAL"] --> ND
    NV -. "修复失败：新 REPAIR_ROUND" .-> CTX
    NIV -. "确认修复失败" .-> CTX
    CV -. "修复失败：新 REPAIR_ROUND" .-> CTX
    CTX -. "重新诊断" .-> ND
    CTX -. "COMPLEX 重新诊断" .-> CD

    subgraph K["协议、状态与运行工件层"]
        CONF["confirmation.md\n入口 / 阶段 / 升级 / 修复选择门禁"]
        CLASSIFIER["change-classifier.md\n结构化指标 / 阈值 / 单向升级"]
        WF["workflow.md\n路线协议 / 早退 / 上下文重置 / 总结"]
        MI["multi-issue.md\n问题归一化 / 修复集合选择 / 复发扫描"]
        ART["artifacts.md\nRUN 元数据 / tasks.yaml / 终态标记"]
        STATE["subagent-state.md\nstate.md / result.md / 派发、观察、回收"]
        ROLES["docs/agent-roles.md\n角色职责 / 上下文白名单 / 交接边界"]
        RUN["RUN_ARTIFACT_DIR\n分类、诊断、计划、任务与状态工件"]
    end

    CONF --> CO
    CLASSIFIER --> CL
    WF --> CO
    MI --> SEL
    ART --> RUN
    STATE --> RUN
    ROLES --> ND
    ROLES --> CPL
    ROLES --> NIMP
    RUN --> CTX

    OUT["完成 / 提前正常结束\n处理总结"]
    TV --> OUT
    NOUT --> OUT
    COUT --> OUT
    ND -. "无问题 / 无可执行修复 / diagnose 完成" .-> OUT
    CI -. "无问题" .-> OUT
    CR -. "复核范围为空" .-> OUT
    SR --> OUT
    SR -. "复核范围为空" .-> OUT

    subgraph X["退出与清理"]
        CTXCLEAN["仅完整或提前正常完成：\n清理上下文\n不再携带阶段推导"]
        CLEAN["仅完整或提前正常完成：\n清理已校验的当前运行目录"]
        KEEP["部分完成 / 失败 / 阻塞 / 停止 /\n取消 / 暂停：保留工件，可恢复或审计"]
    end
    OUT --> CTXCLEAN --> CLEAN
    CO -. "停止条件或未获授权" .-> KEEP

    classDef control fill:#e8f1ff,stroke:#3b73b9,color:#12324a;
    classDef tiny fill:#f2f7ff,stroke:#5578a8,color:#17324d;
    classDef normal fill:#eef8ee,stroke:#4b8f5a,color:#173b1d;
    classDef complex fill:#fff5df,stroke:#b07a17,color:#4a3100;
    classDef contract fill:#f4edff,stroke:#7956ad,color:#2e1c50;
    classDef exit fill:#ffeaea,stroke:#b84a4a,color:#4a1717;

    class E,CO,SAFE,CTX,LIMIT,R,CL,ROUTE,NS,VE,IG,CUP,TUP control;
    class TI,TIMP,TV tiny;
    class ND,NC,NIMP,NV,NIV,NOUT normal;
    class CI,CD,SEL,CPL,CIMP,CINT,CV,CR,COUT complex;
    class CONF,CLASSIFIER,WF,MI,ART,STATE,ROLES,RUN contract;
    class N,SR,OUT,CTXCLEAN,CLEAN,KEEP exit;
```

## 文件映射

| 架构区域 | 当前目录中的权威文件 |
| --- | --- |
| Skill 入口与全局约束 | `SKILL.md` |
| 变更分流与升级 | `references/change-classifier.md`、运行工件 `classification.md` |
| 运行路线、早退、规划模式、验证升级与清理 | `references/workflow.md` |
| 用户确认与 Agent 路由披露 | `references/confirmation.md` |
| 多问题分诊与修复集合选择 | `references/multi-issue.md` |
| 运行工件、`tasks.yaml` 与终态标记 | `references/artifacts.md` |
| 子 Agent 状态、观察、终止与回收 | `references/subagent-state.md` |
| 角色职责、上下文边界与交接 | `docs/agent-roles.md` |
| 全局同步与运行目录清理 | `scripts/sync-global-skill.sh`、`scripts/cleanup-run-artifacts.sh` |
