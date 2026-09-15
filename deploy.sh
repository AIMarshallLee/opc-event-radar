#!/bin/bash
# ============================================================
# 杭州 AI / OPC 活动情报系统 - 生产一键部署脚本
# ============================================================
set -e

echo "============================================================"
echo "🚀 开始部署: 杭州 AI / OPC 活动情报雷达系统"
echo "============================================================"

# 1. 检查 Docker 与 Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: 未检测到 Docker，请先安装 Docker 环境。"
    exit 1
fi

# 2. 检查 .env 文件
if [ ! -f .env ]; then
    echo "ℹ️ 未检测到 .env 文件，自动从 .env.example 创建默认配置..."
    cp .env.example .env
fi

# 3. 确保持久化数据目录
mkdir -p data

# 4. 构建并启动容器
echo "📦 正在构建并拉起 Docker 容器..."
if command -v docker-compose &> /dev/null; then
    docker-compose down 2>/dev/null || true
    docker-compose up -d --build
else
    docker compose down 2>/dev/null || true
    docker compose up -d --build
fi

# 5. 健康检查等待
echo "⏳ 等待服务就绪 (最长 15 秒)..."
SUCCESS=0
for i in {1..15}; do
    if curl -s http://localhost:8765/api/stats > /dev/null; then
        SUCCESS=1
        break
    fi
    sleep 1
done

if [ $SUCCESS -eq 1 ]; then
    echo "============================================================"
    echo "✅ 部署成功！活动雷达已稳定运行。"
    echo "👉 本地访问地址: http://127.0.0.1:8765"
    echo "👉 日历订阅接口: http://127.0.0.1:8765/feed/hangzhou-ai.ics"
    echo "👉 系统监控端点: http://127.0.0.1:8765/api/stats"
    echo "============================================================"
else
    echo "⚠️ 容器已启动，但健康检查响应较慢，请执行 docker logs -f hangzhou-opc-event-radar 查看日志。"
fi
