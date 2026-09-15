# 真实系统架构设计文档 (System Architecture)

> **系统名称**：OPC 活动情报 · 杭州 AI / OPC 活动雷达 V0.1  
> **设计理念**：单体高内聚、抓取与业务解耦、本地优先、防抖避让、零微服务繁杂开销。

---

## 🏛️ 一、 总体分层架构图

```mermaid
graph TD
    subgraph Layer0[公开外部信息源 (External Sources)]
        S1[联谱 Lianpu 杭州]
        S2[活动行 AI 专区]
        S3[活动行 OPC/创业专区]
        S4[SegmentFault 思否活动]
        S5[AI+OPC 政务与产业园区动态]
        S6[Discovery Agent 动态探测]
    end

    subgraph Layer1[采集适配器层 (Fetchers & Adaptors)]
        F1[LianpuFetcher]
        F2[HuodongxingFetcher]
        F3[SegmentFaultFetcher]
        F4[DiscoveryAgentFetcher]
    end

    subgraph Layer2[智能流水线 (Processing Pipeline)]
        Ext[结构化抽取 Extractor]
        Loc[13区县地域校验 LocationValidator]
        Ded[标题语义与时空去重 Deduplicator]
        Ver[多维置信度评定 Verification]
        Cls[14大行业分类 Classifier]
        Sco[100分制综合打分 Scorer]
        Com[犀利高密度评语 CommentGenerator]
    end

    subgraph Layer3[数据存储层 (Storage Layer)]
        DB[(SQLite WAL: events.db)]
        T1[events 表]
        T2[sources 表]
        T3[business_signals 表]
        T4[pipeline_runs 表]
    end

    subgraph Layer4[服务与交互层 (Delivery & Presentation)]
        Sch[增量定时巡检引擎 Scheduler: 08/12/18/23点]
        API[FastAPI 核心中枢]
        UI[极简响应式活动雷达 Web UI]
        Gen[日/周精选社交简报 ContentGenerator]
    end

    S1 --> F1
    S2 --> F2
    S3 --> F2
    S4 --> F3
    S5 --> F4
    S6 --> F4

    F1 & F2 & F3 & F4 --> Ext
    Ext --> Loc --> Ded --> Ver --> Cls --> Sco --> Com
    Com --> DB
    Sch --> Ext
    DB --> API
    DB --> Gen
    API --> UI
```

---

## 🔒 二、 关键设计决策与防御性策略

### 1. 为什么选择 SQLite (WAL 模式) 而非大型外部数据库？
- **环境特性**：部署在移动硬盘 `/Volumes/MOVESPEED` 上，外部 MySQL/PostgreSQL 进程易因挂载点重置或 I/O 延迟引发连接池崩溃。
- **性能保证**：SQLite WAL 模式支持多线程并发读与单写入事务，单库承载数万场活动查询延迟 $\le 2\text{ms}$，极度稳定可靠，免除日常维护。

### 2. 单源失败隔离机制 (Fault Isolation)
- 任何单一数据源发生网络超时、页面结构改版或 403 频控，Fetch 模块仅针对该数据源记录错误并进行本地自愈降级，连续失败 $\ge 3$ 次标记 `status="degraded"`，**严禁阻断全局流水线其他正常数据源的入库**。

### 3. 多源去重与置信度提升 (Cross-Source Enrichment)
- 同一活动在活动行和 Lianpu 同时发布时，基于清洗后的 `normalized_title`（剥离“【】”、无意义标点、“杭州站”等后缀）计算 Levenshtein 相似度；
- 一旦判定为同一活动，自动合并两者的报名链接与来源元数据，并将该活动的 `confidence_score` 自动提升，在卡片上标明“已核实 · 多源印证”。

### 4. 商业信号挖掘 (Business Signals)
- 每次入库活动时，系统自动提取主办方与承办园区。
- 当某一园区（如未来科技城梦想小镇、白马湖党群服务中心）或组织（如万有引力AI、奇思宇宙）的举办频次递增时，系统将其沉淀为潜在商业线索，为未来商业化与生态合作打好数据基石。
