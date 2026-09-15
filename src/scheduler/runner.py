import time
import datetime
import threading
import schedule
from typing import Optional
from src.pipeline.engine import run_pipeline
from src.core.database import get_all_events, save_event

def manage_event_lifecycles():
    """
    生命周期自动管理：
    自动流转 upcoming -> today -> ongoing -> ended。
    """
    now = datetime.datetime.now()
    today_str = now.strftime("%m月%d日")
    today_iso = now.strftime("%Y-%m-%d")

    events = get_all_events()
    updated_count = 0

    for ev in events:
        old_status = ev.status
        start_t = ev.start_time

        # 如果活动时间已过 (简单日期比对)
        # 例如 09月10日 在 09月15日 之前
        # 提取月份和日期
        import re
        m = re.search(r'(\d{1,2})月(\d{1,2})日', start_t)
        if m:
            month = int(m.group(1))
            day = int(m.group(2))
            # 假定年份为当前年
            ev_date = datetime.date(now.year, month, day)
            today_date = now.date()

            if ev_date < today_date:
                ev.status = "ended"
            elif ev_date == today_date:
                ev.status = "today"
            else:
                ev.status = "upcoming"
        elif "今天" in start_t:
            ev.status = "today"

        if ev.status != old_status:
            ev.updated_at = now.isoformat()
            save_event(ev)
            updated_count += 1

    if updated_count > 0:
        print(f"[Lifecycle] 自动更新了 {updated_count} 个活动的生命周期状态")

def job_pipeline_tick():
    print(f"\n[Scheduler] 定时启动 Pipeline 任务: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    # 1. 刷新生命周期
    manage_event_lifecycles()
    # 2. 增量拉取与入库
    try:
        r = run_pipeline()
        print(f"[Scheduler] Pipeline 运行成功: {r.summary}")
    except Exception as e:
        print(f"[Scheduler] Pipeline 运行异常: {e}")

class EventScheduler:
    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def setup_schedules(self):
        # 按照任务书第 18 条规范：每天 08:00, 12:00, 18:00, 23:00 增量检查
        schedule.every().day.at("08:00").do(job_pipeline_tick)
        schedule.every().day.at("12:00").do(job_pipeline_tick)
        schedule.every().day.at("18:00").do(job_pipeline_tick)
        schedule.every().day.at("23:00").do(job_pipeline_tick)
        print("[Scheduler] 已配置 08:00, 12:00, 18:00, 23:00 定时增量巡检任务")

    def _loop(self):
        while self._running:
            schedule.run_pending()
            time.sleep(30)

    def start_background(self):
        if self._running:
            return
        self.setup_schedules()
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("[Scheduler] 定时调度器后台守护线程已启动")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        print("[Scheduler] 定时调度器已停止")

if __name__ == "__main__":
    print("=== 运行即时生命周期刷新与调度检测 ===")
    manage_event_lifecycles()
