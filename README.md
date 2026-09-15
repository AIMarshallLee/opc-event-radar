<div align="center">

# ⚡ OPC 活动情报雷达 (OPC Event Radar)
### 全国四大科技核心城市 (杭州 · 上海 · 深圳 · 厦门) AI / FDE / OPC 线下组局全自动情报系统

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![CI Pipeline](https://img.shields.io/github/actions/workflow/status/AIMarshallLee/opc-event-radar/daily-radar-scan.yml?branch=main&label=Auto%20Scan%20CI&style=flat-square)](https://github.com/AIMarshallLee/opc-event-radar/actions)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)

**不堆砌海量低质活动，只告诉你哪场真正值得去。**  
通过 AI 巡检引擎与多源探针，全自动监控、提取、去重、核验与 100 分制价值评估，一页洞察国内顶尖线下极客沙龙、闭门会、黑客松与一人公司(OPC)商业共创。

[在线体验](#-快速启动) • [日历订阅](#-全平台日历一键订阅) • [数据源矩阵](#-全景数据源矩阵) • [开源部署](#-生产级一键部署) • [贡献指南](#-参与贡献)

</div>

---

## 🌟 为什么要做这个开源项目？

在目前的各大活动平台中，充斥着大量的招商加盟、泛科普培训与割韭菜讲座。真正的 **前置部署工程师 (FDE)**、**一人公司 (OPC)**、**大模型 Agent 开发者** 以及 **出海创始人** 举办的硬核闭门会、Demo Day 与极客沙龙，往往散落在 Luma、微信公众号推文、小红书自发帖和垂直开发者社区中。

**OPC 活动情报雷达** 致力于彻底解决活动信息不对称：
1. **自动化率 ≥95%**：无需人工日常维护，全网自动感知发现；
2. **拒绝假数据与割韭菜**：基于多源交叉验证、主办方背书与 100 分制打分引擎，输出犀利的「AI 推荐理由与避坑指南」；
3. **全国四大创新核心城市**：杭州大本营、上海模速空间/张江、深圳南山科技园/粤海、厦门出海软件园。

---

## 🏙️ 四大核心城市定位矩阵

| 城市 | 极客与产业标签 | 核心地标与线下据点 | 代表活动类型 |
| :--- | :--- | :--- | :--- |
| **⚡ 杭州 (大本营)** | **大模型智能体、电商+AI、一人公司(OPC)、阿里/浙大生态** | 未来科技城、梦想小镇、云栖小镇、滨江物联网小镇 | AI Agent 实战、Vibe Coding 沙龙、OPC 商业路演 |
| **🗼 上海** | **全球顶级黑客松、跨国开发者、产学研高地、模速空间** | 徐汇西岸智塔、模速空间、张江高科、创智天地 | 闭门 Founder Meetup、AGI 极客日、海外出海研讨 |
| **🏙️ 深圳** | **硬件+端侧AI、前置交付工程师(FDE)、出海掘金主阵地** | 南山科技园、粤海街道、大族激光中心、深圳湾生态园 | 端侧大模型实战、企业级 FDE 场景共创、出海沙龙 |
| **🌊 厦门** | **独立开发者(Indie Hacker)、跨境工具出海、小而美独立站** | 软件园二期、软件园三期、观音山商务区、集美创新城 | 出海工具变现、独立开发者面基、跨境电商 AI 研讨 |

---

## 🚀 核心系统特性

* **🌐 首页智能网络定位与平滑回退**：访问首页时自动感知访问者所在省市，命中华东/华南支持城市时自动高亮对应城市活动；若在其他城市或定位受阻，**100% 自动回退默认选中「杭州」**，绝不空白卡死。
* **📅 全平台 RFC 5545 日历实时订阅**：支持按城市单独订阅（如 `/feed/events.ics?city=深圳`），在 iPhone、Mac Calendar、Google 日历中一键订阅，提前 2 小时推送日程提醒并自带 AI 避坑指南。
* **📥 微信文章与海报 OCR 秒级补漏**：内置 `/api/intake/wechat` 公开文章直读与多模态海报图片提取接口，群友发一张海报 3 秒结构化入库。
* **🤖 GitHub Actions 云端永久自运转**：内置 `.github/workflows/daily-radar-scan.yml`，每天在 08:00, 12:00, 18:00, 23:00 四次自动拉起云端虚拟机巡检，发现新活动自动提交推回仓库，**零服务器成本永久运行**。
* **🎨 现代化浅色 / 深色双主题**：自适应 Tailwind CSS 响应式大屏，骨架屏加载，支持手机端与电脑端极速浏览。

---

## 📦 生产级一键部署

系统采用极简架构，单端口 `8765`，内置 SQLite WAL 模式，无任何外部 Redis 或重型数据库负担。

### 方式一：Docker 一键部署 (推荐)

```bash
# 1. 克隆开源仓库
git clone https://github.com/AIMarshallLee/opc-event-radar.git
cd opc-event-radar

# 2. 复制环境配置
cp .env.example .env

# 3. 运行一键部署脚本
./deploy.sh
```

服务就绪后直接访问：
* Web 主站：`http://localhost:8765`
* 日历订阅源：`http://localhost:8765/feed/events.ics`
* 系统健康度端点：`http://localhost:8765/api/stats`

### 方式二：Python 本地直接运行

```bash
# 1. 初始化虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动服务 (自带后台巡检守护线程)
python3 run.py
```

---

## 📡 全平台日历一键订阅

无论你是使用 Apple 还是 Android 设备，均可直接通过系统的 iCalendar 标准订阅源将最新活动流同步到系统日历中：

| 订阅范围 | 订阅 URL | 说明 |
| :--- | :--- | :--- |
| **杭州站专属** | `https://ai.2199.chat/feed/events.ics?city=杭州` | 仅推送杭州本地与线上高分活动 |
| **上海站专属** | `https://ai.2199.chat/feed/events.ics?city=上海` | 仅推送上海本地与线上高分活动 |
| **深圳站专属** | `https://ai.2199.chat/feed/events.ics?city=深圳` | 仅推送深圳本地与线上高分活动 |
| **厦门站专属** | `https://ai.2199.chat/feed/events.ics?city=厦门` | 仅推送厦门本地与线上高分活动 |
| **全国全城订阅** | `https://ai.2199.chat/feed/events.ics` | 推送四大城市全部精选高分活动 |

---

## 🤝 参与贡献

我们极其欢迎广大开发者、活动主办方与独立开发者共同维护这个开源情报网络！

1. **Fork 本仓库** 并创建您的特性分支：`git checkout -b feat/my-new-source`；
2. **新增城市或数据源**：在 `src/sources/registry.py` 和 `src/pipeline/location_validator.py` 中添加地标规则与爬虫；
3. **提交代码**：遵循 Conventional Commits 规范；
4. **提交 Pull Request**：CI 自动化测试跑通后，我们将第一时间 Review 并合并上线！

---

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 协议完全开源自由使用。
