# 杭州 AI / OPC 活动情报雷达系统 - 生产部署与运维手册

本文档专为运维工程师与技术部署人员编写，指导如何将 **杭州 AI / OPC 活动情报系统** 部署上线并绑定域名（例如 `ai.2199.chat`）。

---

## 一、 架构与部署概览

* **运行环境**: Python 3.11+ / Docker
* **暴露端口**: `8765`（支持环境变量 `RADAR_PORT` 自定义）
* **存储引擎**: SQLite (WAL 预写日志模式，单文件高并发无锁，存储于 `./data/events.db`)
* **架构特点**: 单一可执行服务，自带后台巡检调度器（每天 08:00, 12:00, 18:00, 23:00 自动发现新活动），无外部 Redis/PostgreSQL 重型依赖，极低资源占用（内存 < 80MB）。

---

## 二、 部署方案

### 方案 A：Docker Compose 一键部署（推荐）

#### 1. 准备代码包与环境变量
进入项目根目录：
```bash
cp .env.example .env
# 可根据需要编辑 .env，默认配置即可直接运行
```

#### 2. 一键执行部署脚本
```bash
./deploy.sh
```
或者手动运行：
```bash
docker compose up -d --build
```

#### 3. 验证运行状态
```bash
curl http://localhost:8765/api/stats
# 返回 JSON 统计信息即代表部署成功
```

---

### 方案 B：Linux 裸机 / VPS 常驻部署 (Systemd)

如果目标服务器不使用 Docker，可直接使用 Python 虚拟环境与 Systemd 守护进程：

#### 1. 初始化 Python 环境
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 2. 配置 Systemd 服务
创建 `/etc/systemd/system/opc-event-radar.service`：
```ini
[Unit]
Description=Hangzhou AI/OPC Event Radar Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/opc-event-radar
Environment="PYTHONPATH=/opt/opc-event-radar"
Environment="RADAR_HOST=0.0.0.0"
Environment="RADAR_PORT=8765"
ExecStart=/opt/opc-event-radar/.venv/bin/python run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### 3. 启动并启用开机自启
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now opc-event-radar
sudo systemctl status opc-event-radar
```

---

## 三、 域名解析与反向代理 (以 `ai.2199.chat` 为例)

### 1. Nginx 反向代理配置
在 `/etc/nginx/conf.d/ai.2199.chat.conf` 中添加：

```nginx
server {
    listen 80;
    server_name ai.2199.chat;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ai.2199.chat;

    # SSL 证书配置 (Certbot 或 Cloudflare Origin CA)
    ssl_certificate /etc/letsencrypt/live/ai.2199.chat/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ai.2199.chat/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8765;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_read_timeout 60s;
    }
}
```

### 2. Caddy 反向代理配置（自动配置 SSL）
如果使用 Caddy，仅需在 `Caddyfile` 加入两行：
```caddy
ai.2199.chat {
    reverse_proxy 127.0.0.1:8765
}
```

### 3. Cloudflare Tunnel 穿透配置（若服务器在内网）
如果服务器位于本地机房或内网，可直接通过 Cloudflare Tunnel 映射：
```yaml
tunnel: <TUNNEL_UUID>
credentials-file: /root/.cloudflared/<TUNNEL_UUID>.json

ingress:
  - hostname: ai.2199.chat
    service: http://localhost:8765
  - service: http_status:404
```

---

## 四、 核心接口与外部订阅

部署上线后，以下对外地址即可直接提供给用户或三方系统：

| 功能模块 | 访问路径 | 说明 |
| :--- | :--- | :--- |
| **Web 交互主站** | `https://ai.2199.chat/` | 浅色/深色自适应现代化活动雷达大屏 |
| **日历订阅源** | `https://ai.2199.chat/feed/hangzhou-ai.ics` | 支持 Apple 日历、Google Calendar、Outlook 实时订阅 |
| **JSON API 列表** | `https://ai.2199.chat/api/events?limit=50` | 结构化活动数据（含置信度、打分、毒舌评语） |
| **公众号直读入库** | `POST https://ai.2199.chat/api/intake/wechat` | 传入 `{"url": "https://mp.weixin.qq.com/s/..."}` 秒级直读 |
| **海报 OCR 入库** | `POST https://ai.2199.chat/api/intake/upload` | 上传多模态海报图片提取活动 |
| **系统健康度统计** | `https://ai.2199.chat/api/stats` | 监控活动总数、更新时间与来源分布 |

---

## 五、 数据持久化与备份

* 数据库文件位置：`./data/events.db`
* 备份建议：每天定时执行 `cp ./data/events.db ./data/backup_$(date +%Y%m%d).db`。由于启用了 SQLite WAL 模式，热备份完全不会阻塞任何读写操作。
