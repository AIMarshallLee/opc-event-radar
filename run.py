import os
import sys
import uvicorn
from src.core.database import init_db, get_all_events
from src.sources.registry import initialize_source_registry
from src.pipeline.engine import run_pipeline
from src.scheduler.runner import manage_event_lifecycles

def main():
    print("=" * 60)
    print("⚡ 杭州 AI / OPC 活动情报系统 (杭州 AI 活动雷达)")
    print("全自动运营流水线与自运转服务")
    print("=" * 60)

    # 1. 初始化数据库与表
    init_db()

    # 2. 初始化数据源注册表
    initialize_source_registry()

    # 3. 命令行参数检查：支持单次流水线巡检
    if "--pipeline-only" in sys.argv or "--pipeline" in sys.argv:
        print("[Pipeline] 收到手动或定时触发指令，开始执行全源采集与研判流水线...")
        res = run_pipeline()
        print(f"[Pipeline] 流水线执行完毕: {res}")
        return

    # 检查数据库，若过少则执行首轮采集
    existing = get_all_events()
    print(f"[Storage] 现有本地活动库总数: {len(existing)} 场")
    if len(existing) < 10:
        print("[Pipeline] 本地活动库不足，触发首轮多源数据采集与研判...")
        run_pipeline()

    # 4. 刷新生命周期
    manage_event_lifecycles()

    # 5. 启动 Web 服务 (支持环境变量配置)
    host = os.environ.get("RADAR_HOST", "0.0.0.0")
    port = int(os.environ.get("RADAR_PORT", "8765"))
    print(f"\n🚀 活动雷达 Web 服务已就绪: http://{host}:{port}")
    print(f"👉 访问地址: http://localhost:{port}")
    print("=" * 60)

    uvicorn.run("src.web.app:app", host=host, port=port, reload=False, access_log=False)

if __name__ == "__main__":
    main()
