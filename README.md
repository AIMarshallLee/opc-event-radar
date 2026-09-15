# ⚡ OPC 活动情报 (杭州 AI / OPC 活动雷达 V0.1)

> **全自动运营系统 · 杭州本地 AI / OPC / 创业活动情报中枢**  
> **核心使命**：解决“杭州今天有什么值得参加的？哪场真正值得去？”——拒绝无意义活动堆砌，聚焦商业落地、一人公司(OPC)变现与技术干货洞察。  
> **目标自动化率**：$\ge 95\%$（项目所有者无需每日手工维护）。

---

## 📌 一、 系统核心价值与特点

1. **真实数据源驱动**：接入联谱 Lianpu、活动行、SegmentFault 思否、政务与园区公开专区等 **6 个稳定公开源**，当前已实测收录 **70+ 场真实杭州本地未来活动**，拒绝任何虚构 Mock 数据。
2. **严苛 13 区县地域过滤**：严格识别余杭（未来科技城/梦想小镇/人工智能小镇）、滨江（阿里园区/白马湖）、西湖（云栖/紫金港）、上城（丁兰智慧小镇OPC高地/钱江新城）、拱墅、萧山等 13 个区县。自动剔除异地杂音，线上生态活动单独归类。
3. **跨源智能去重与富化**：基于标准化标题语义相似度 + 时间重叠度 + 地点/主办方交叉比对，多平台同名活动自动合并，保留所有来源并提升置信度。
4. **100 分制 AI 价值评估体系**：
   - 主办方/嘉宾质量（20分）
   - 内容含金量（20分）
   - 商务连接价值（20分）
   - 创业实际价值（15分）
   - 稀缺性（10分）
   - 性价比（10分）
   - 信息可信度（5分）
   - **五维雷达细分**：知识含金量、社交人脉、商务变现、技术深度、融资对接。
5. **犀利高密度 AI 推荐评语**：DeepSeek 大模型与本地规则混合驱动，直击“为什么值得去”、“明确适合谁”、“明确劝退谁 (避坑指南)”，杜绝泛泛客套文案。
6. **全生命周期自主流转**：定时调度器自动完成 `upcoming` $\to$ `today` $\to$ `ongoing` $\to$ `ended` 流转，活动过期自动归档。
7. **沉淀商业信号 (Business Signals)**：自动沉淀活跃 OPC 组织、高频承办会展园区与明星主办方名单。

---

## 🚀 二、 快速上手与运行

### 1. 环境准备
系统采用轻量单体架构，基于 Python 3.11+ 标准技术栈：
```bash
# 进入项目目录 (严禁使用 cd，保持在工作区根路径或传入相对路径)
# 确保已安装基础依赖：fastapi, uvicorn, beautifulsoup4, schedule, pydantic
```

### 2. 一键启动 (后台常驻调度 + Web雷达服务)
```bash
PYTHONPATH=. python3 run.py
```
- **Web 雷达访问入口**：`http://127.0.0.1:8765`
- 服务将自动完成：
  1. 数据库结构初始化 (`data/events.db`)
  2. 数据源健康状态校验
  3. 启动后台守护定时任务（每天 08:00, 12:00, 18:00, 23:00 自动巡检）
  4. 启动轻量响应式活动雷达前端。

### 3. 手动单次触发增量流水线
```bash
PYTHONPATH=. python3 src/pipeline/engine.py
```

### 4. 生成今日/本周社交媒体精选简报
```bash
# 生成本周精选 Markdown 简报
PYTHONPATH=. python3 src/content/generator.py
```

---

## 🛠️ 三、 核心架构与目录规划

```
opc-event-radar/
├── run.py                       # 一键启动中枢 (Web + 调度守护)
├── docs/                        # 交付报告与架构文档
│   ├── SOURCE_REPORT.md         # Phase 1 数据源可得性实测报告
│   ├── ARCHITECTURE.md          # 真实系统架构设计
│   └── DELIVERY_REPORT.md       # V0.1 最终验收与指标交付报告
├── src/
│   ├── core/
│   │   ├── models.py            # Event/Source/PipelineRun/Signal 数据模型
│   │   └── database.py          # SQLite WAL 高性能存储底座
│   ├── sources/
│   │   ├── registry.py          # Source Registry 数据源注册中枢
│   │   └── verifier.py          # 数据源健康探针与连通性验证
│   ├── fetchers/
│   │   ├── base.py              # 抽象采集基类
│   │   ├── lianpu.py            # 联谱 Lianpu 杭州站采集器
│   │   ├── huodongxing.py       # 活动行杭州 AI/OPC 采集器
│   │   ├── segmentfault.py      # 思否全球开发者日历采集器
│   │   └── discovery.py         # 动态感知雷达采集器
│   ├── pipeline/
│   │   ├── location_validator.py# 杭州 13 区县及园区强校验
│   │   ├── deduplicator.py      # 跨源标题与时空去重合并
│   │   ├── classifier.py        # 14 大行业分类与标签提取
│   │   ├── verification.py      # 置信度评估 (0-100分)
│   │   ├── scorer.py            # 100 分制价值雷达评估
│   │   ├── comment_generator.py # 犀利中肯 AI 评语引擎
│   │   └── engine.py            # 多线程并发流水线编排器
│   ├── scheduler/
│   │   └── runner.py            # APScheduler/Schedule 增量定时引擎与生命周期管理
│   ├── content/
│   │   └── generator.py         # 日/周/周末精选简报自动生成器
│   └── web/
│       ├── app.py               # FastAPI 后端路由与可观测性 API
│       └── static/
│           └── index.html       # 极简高质感现代响应式前端
└── tests/
    └── test_radar_pipeline.py   # 覆盖 14 项异常与边界场景的测试套件
```

---

## ⚙️ 四、 运营与扩展指南

### 1. 如何扩展新的数据源？
1. 在 `src/sources/registry.py` 中添加数据源配置字典（定义 `id`, `name`, `type`, `url`, `fetch_method`）；
2. 在 `src/fetchers/` 目录下继承 `BaseFetcher` 实现对应站点的 `fetch_raw_candidates()` 方法；
3. 在 `src/pipeline/engine.py` 的 `FETCHER_MAP` 中注册该数据源映射即可。
*注：系统内置单源隔离熔断机制，若新源连续失败 $\ge 3$ 次将自动标记为 `degraded`，绝不影响现有源的正常抓取。*

### 2. 如何调整评分权重与 AI 评语提示词？
- **评分规则修改**：编辑 `src/pipeline/scorer.py` 中的 `evaluate_event_scores` 函数，可自定义 7 个维度的权重分配与得分上下限。
- **AI 评语风格调整**：编辑 `src/pipeline/comment_generator.py` 中的提示词模板（System Prompt），可调整毒舌程度、重点侧重赛道（如增加对出海/智能体的偏好）。

### 3. 手动补漏投递 (Manual Intake)
除了全网自动监测，系统在 Web 界面与 API 均提供手工补漏通道：
- **Web 端**：点击右上角「+ 补漏投递」粘贴活动通知或海报文本；
- **API 端**：`POST /api/intake` 携带 `{"raw_text": "...", "url": "..."}`。系统将即时自动调用流水线解析入库。

---

## 📈 五、 成本核算与可观测性

- **规则先行**：90% 的地域判断、噪音过滤、标题去重均走本地正则与轻量算法，零外部调用开销；
- **增量 AI 研判**：仅对初次入库或重大更新的有效活动调用 DeepSeek 模型生成评语，平均每场活动消耗 $\approx 300$ Tokens（折合成本约 0.0004 元/场）；
- **月度成本预估**：按每日增量发现 10 场活动计算，单月大模型成本不足 **0.2 元人民币**，实现极致的低成本、高可靠自运营。
