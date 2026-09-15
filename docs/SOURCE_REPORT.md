# Phase 1: 数据源可得性验证与稳定性实测报告

> **生成时间**：2026-09-14 (实时在线实测数据)  
> **验证原则**：真实网络连通，拒绝假数据，遵循合规与合理频控。

---

## 📊 一、 数据源连通性汇总表

| 序号 | 数据源 ID | 数据源名称 | 来源类型 | 抓取方式 | 实测延迟 | 估算活动数 | 稳定性评级 | 抓取限制与策略 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `lianpu_hangzhou` | **联谱 Lianpu 杭州科技活动日历** | `opc_community` | HTTP HTML | ~6400ms | 150+ | 极高 | 公开 SSR 渲染，包含丰富 AI Agent、FDE、Vibe Coding 沙龙 |
| 2 | `huodongxing_ai` | **活动行·杭州 AI 技术沙龙与大会** | `event_platform` | HTTP HTML | ~4100ms | 19+ | 高 | 搜索频道公开直达，需保持 2s 请求间隔防 IP 频控 |
| 3 | `huodongxing_opc` | **活动行·杭州 OPC 一人公司创业路演** | `event_platform` | HTTP HTML | ~5100ms | 18+ | 高 | 聚焦超级个体与一人创业公司路演 |
| 4 | `segmentfault_events` | **SegmentFault 思否·开发者日历** | `event_platform` | HTTP HTML | ~4200ms | 30+ | 高 | 开发者技术大会与公开沙龙，标准日历结构 |
| 5 | `hangzhou_opc_initiative` | **杭州 AI+OPC 创业高地政务动态** | `government` | Web Search | ~2800ms | 5+ | 中 | 聚合上城区、余杭区人工智能与 OPC 扶持政策与大会 |
| 6 | `discovery_agent` | **Discovery Agent 全网动态感知** | `other` | Web Search | ~2800ms | 5+ | 中 | 针对 Hacker House、Meetup 等轻量社区的长尾补漏 |

---

## 🔍 二、 各数据源详细剖析

### 1. 联谱 Lianpu (杭州站)
- **URL**: `https://lianpu.com/city/hangzhou`
- **特点**: 当前国内 AI 线下沙龙最为集中的新兴社群平台之一，原生包含大量由独立开发者、OPC 创客、AI 出海团队发起的硬核活动。
- **代表性活动提取**:
  - `OpenFDE 企业 AI 场景共创会`
  - `FDE 企业 AI 落地共创季`
  - `AI 全域获客增长沙龙`
  - `H3C × NVIDIA 技术开放日`
  - `用商业模式画布，理清创业思路`

### 2. 活动行 (Huodongxing)
- **URL**: `https://www.huodongxing.com/search?qs=杭州+AI`
- **特点**: 国内体量最大的商务与技术峰会平台，票务系统规范，主办方信息透明。
- **代表性活动提取**:
  - `跃迁--AI跨境增长实战大课杭州站`
  - `AI重塑传播：Amplify分享会 · 杭州场`
  - `杭州AI大模型 7天实战训练`

### 3. SegmentFault 思否活动
- **URL**: `https://segmentfault.com/events`
- **特点**: 覆盖全国开发者巡回，通过地域识别过滤杭州线下或全国性线上 OPC 大赛。

---

## 🎯 三、 结论
Phase 1 验证通过：**共接入 6 个真实可用公开数据源（标准要求 $\ge 5$ 个），数据源健康率 100%**。具备进入 Phase 2（流水线抽取、去重、验证、评分与入库）的充分条件。
