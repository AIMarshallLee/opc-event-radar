# ============================================================
# 杭州 AI / OPC 活动情报雷达系统 - 生产级 Dockerfile
# ============================================================
FROM python:3.11-slim

# 设置时区为东八区 (Asia/Shanghai)
ENV TZ=Asia/Shanghai
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    curl \
    && ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo ${TZ} > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制工程源码
COPY . .

# 确保持久化数据目录存在
RUN mkdir -p data

# 暴露单端口
EXPOSE 8765

# 容器健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8765/api/stats || exit 1

# 启动服务
CMD ["python3", "run.py"]
