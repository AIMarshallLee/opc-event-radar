<div align="center">

# ⚡ OPC Event Radar
### Fully-automated event intelligence for AI / FDE / OPC offline meetups in China's four tech hubs (Hangzhou · Shanghai · Shenzhen · Xiamen)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)

**We don't dump low-quality event listings — we tell you which ones are actually worth attending.**
An AI-powered radar that automatically monitors, extracts, deduplicates, verifies, and scores offline hacker salons, closed-door meetups, hackathons, and One-Person-Company (OPC) business events on a 100-point scale.

[Quick Start](#-quick-start) • [Calendar & Feeds](#-calendar-and-feeds) • [API](#-api) • [Deploy](#-production-deployment) • [Contribute](#-contributing)

> 🇨🇳 完整中文文档：[README.md](./README.md)

</div>

---

## 🌟 Why This Exists

Event platforms today are flooded with franchise pitches, generic training, and pay-to-learn seminars. The genuinely valuable events — hardcore closed-door meetups from **Forward-Deployed Engineers (FDE)**, **One-Person Companies (OPC)**, LLM/Agent builders, and global founders — are scattered across Luma, WeChat article posts, Xiaohongshu, and niche developer communities.

OPC Event Radar solves this information asymmetry:

1. **≥95% automated**: no daily manual curation; the pipeline senses and ingests new events on its own
2. **No fake data, no junk**: multi-source cross-validation, organizer endorsement checks, and a 100-point scoring engine output blunt "why go / who should skip" guidance
3. **Four core innovation hubs**: Hangzhou (home base), Shanghai (Xuhui West Bund / Zhangjiang), Shenzhen (Nanshan / Yuehai), Xiamen (Software Park / indie-hacker scene)

## 🏙️ City Matrix

| City | Scene | Typical events |
| :--- | :--- | :--- |
| **⚡ Hangzhou** | LLM agents, e-commerce + AI, OPC, Alibaba/Zhejiang-University ecosystem | AI Agent workshops, vibe-coding salons, OPC pitch nights |
| **🗼 Shanghai** | Top-tier hackathons, cross-border developers, ModelSpeed Space (模速空间) ecosystem | Founder meetups, AGI hacker days, going-global seminars |
| **🏙️ Shenzhen** | Hardware + edge AI, FDE, overseas expansion | Edge-LLM workshops, enterprise FDE co-builds |
| **🌊 Xiamen** | Indie hackers, cross-border tooling, small-and-beautiful SaaS | Indie dev meetups, cross-border e-commerce AI sessions |

## ✨ Core Features

- **🌐 Locale-aware front page** with smooth fallback: highlights your city when you're in a supported region, 100% falls back to Hangzhou otherwise — never blank
- **📅 RFC 5545 calendar subscription**: subscribe per city (`/feed/events.ics?city=杭州`) in iPhone/Mac Calendar, Google Calendar, or Outlook; 2-hour event reminders with AI "avoid-the-pit" notes
- **📰 Atom / RSS feed**: `/feed/events.xml` for Feedly, Inoreader, Folo and any RSS reader; same filter semantics as the calendar feed
- **📥 WeChat article & poster OCR intake**: POST an article URL or a photo of an event poster to `/api/intake/*` and get structured events in seconds
- **🤖 GitHub Actions self-running**: built-in workflow scans four times daily (08:00/12:00/18:00/23:00) and auto-commits newly discovered events — zero server cost forever
- **🎨 Modern light/dark themes**: Tailwind CSS responsive dashboard, skeleton loading, mobile-first

## 🚀 Quick Start

### Option 1: Docker (recommended)

```bash
git clone https://github.com/AIMarshallLee/opc-event-radar.git
cd opc-event-radar
cp .env.example .env
./deploy.sh
```

Then open:

* Web dashboard: `http://localhost:8765`
* Calendar feed: `http://localhost:8765/feed/events.ics`
* Health/stats endpoint: `http://localhost:8765/api/stats`

### Option 2: Local Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 run.py   # starts the background inspection daemon
```

## 📡 Calendar and Feeds

| Scope | URL | Notes |
| :--- | :--- | :--- |
| Per-city calendar | `https://ai.2199.chat/feed/events.ics?city=杭州` | Chinese city name as the `city` param |
| All cities calendar | `https://ai.2199.chat/feed/events.ics` | Score ≥ 75 across all four cities |
| Atom feed (RSS readers) | `https://ai.2199.chat/feed/events.xml` | Same filters: `?city=`, `?min_score=`, `?category=` |
| CSV export | `https://ai.2199.chat/api/events.csv` | UTF-8 BOM, Excel-friendly, same filters |

Filters shared by all feeds: `city` (Chinese city name), `min_score` (default 75), `category` (e.g. `AI`, `FDE`, `OPC`, `Agent`).

## 🔌 API

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/events` | GET | Paginated event list with filters |
| `/api/events/{id}` | GET | Event detail with scores and AI commentary |
| `/api/stats` | GET | System health and pipeline stats |
| `/api/observability` | GET | Pipeline run history |
| `/api/intake` | POST | Manual text intake (title/body/url) |
| `/api/intake/wechat` | POST | WeChat article URL → structured event |
| `/api/intake/upload` | POST | Event poster image → multimodal extraction |
| `/feed/events.ics` | GET | iCalendar subscription |
| `/feed/events.xml` | GET | Atom subscription |
| `/api/events.csv` | GET | CSV export |
| `/api/pipeline/trigger` | POST | Manually trigger a scan |

## 🏗️ Architecture

Single port (`8765`), SQLite in WAL mode — no external Redis or heavyweight database.

```text
src/
├── core/          # Pydantic models, SQLite persistence
├── fetchers/      # Luma, WeChat, SegmentFault, Huodongxing probes…
├── pipeline/      # Dedup → location validation → classification → scoring → AI commentary
├── scheduler/     # Lifecycle management (upcoming → today → ended)
├── content/       # iCal / Atom / CSV renderers
└── web/           # FastAPI app + Tailwind dashboard
```

## 🚢 Production Deployment

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for Docker Compose, Aliyun, and reverse-proxy setup. CI runs the full pipeline daily and pushes newly discovered events straight back to the repo.

## 🤝 Contributing

PRs welcome from developers, event organizers, and indie hackers!

1. Fork the repo and create a feature branch
2. **Add a city or data source**: extend `src/fetchers/` and the landmark rules in `src/pipeline/location_validator.py`
3. Follow [Conventional Commits](https://www.conventionalcommits.org/)
4. CI must pass; we review and merge promptly

## 💬 Community & Commercial Inquiries

Join the **Kunlun Growth · AI & OPC offline event intelligence network** — connect with indie developers, AI creators, and event organizers across the four cities. Event organizers can request expedited listing and calendar featuring. Commercial inquiries: see [README.md](./README.md#-开发者与主办方社群-community--commercial-inquiries) (Chinese) or open an issue.

## 📄 License

MIT — see [LICENSE](./LICENSE).
