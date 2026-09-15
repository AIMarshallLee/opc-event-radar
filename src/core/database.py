import sqlite3
import json
import os
from typing import List, Optional, Dict, Any
from src.core.models import Event, Source, BusinessSignal, PipelineRun

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "events.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Sources 表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sources (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        url TEXT NOT NULL,
        priority INTEGER DEFAULT 1,
        enabled BOOLEAN DEFAULT 1,
        fetch_method TEXT DEFAULT 'http_html',
        last_checked_at TEXT,
        last_success_at TEXT,
        failure_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        notes TEXT
    );
    """)

    # 2. Events 表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        normalized_title TEXT NOT NULL,
        description TEXT,
        start_time TEXT NOT NULL,
        end_time TEXT,
        city TEXT DEFAULT '杭州',
        district TEXT,
        venue TEXT,
        address TEXT,
        organizer TEXT,
        co_organizers TEXT, -- JSON array
        price REAL DEFAULT 0.0,
        price_text TEXT,
        category TEXT DEFAULT 'AI',
        tags TEXT, -- JSON array
        audience TEXT,
        source_id TEXT NOT NULL,
        source_name TEXT NOT NULL,
        source_url TEXT NOT NULL,
        signup_url TEXT,
        image_url TEXT,
        sources TEXT, -- JSON array of source objects
        confidence_score INTEGER DEFAULT 80,
        overall_score INTEGER DEFAULT 75,
        learning_score INTEGER DEFAULT 70,
        networking_score INTEGER DEFAULT 70,
        business_score INTEGER DEFAULT 70,
        technical_score INTEGER DEFAULT 70,
        fundraising_score INTEGER DEFAULT 60,
        recommendation_reason TEXT,
        suitable_for TEXT,
        not_suitable_for TEXT,
        verification_status TEXT DEFAULT 'verified',
        status TEXT DEFAULT 'upcoming',
        first_seen_at TEXT,
        last_seen_at TEXT,
        last_verified_at TEXT,
        created_at TEXT,
        updated_at TEXT
    );
    """)

    # 3. 商业信号表 (Business Signals)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS business_signals (
        id TEXT PRIMARY KEY,
        organization TEXT NOT NULL,
        signal_type TEXT NOT NULL,
        evidence TEXT,
        frequency INTEGER DEFAULT 1,
        potential_value TEXT,
        created_at TEXT,
        updated_at TEXT
    );
    """)

    # 4. Pipeline Runs 运行记录表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pipeline_runs (
        id TEXT PRIMARY KEY,
        start_time TEXT NOT NULL,
        end_time TEXT,
        scanned_sources INTEGER DEFAULT 0,
        success_sources INTEGER DEFAULT 0,
        failed_sources INTEGER DEFAULT 0,
        candidate_events INTEGER DEFAULT 0,
        new_events INTEGER DEFAULT 0,
        updated_events INTEGER DEFAULT 0,
        duplicate_events INTEGER DEFAULT 0,
        rejected_events INTEGER DEFAULT 0,
        ai_calls INTEGER DEFAULT 0,
        estimated_tokens INTEGER DEFAULT 0,
        status TEXT DEFAULT 'running',
        summary TEXT
    );
    """)

    # 索引优化
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_start_time ON events(start_time);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_normalized_title ON events(normalized_title);")

    conn.commit()
    conn.close()

# Source CRUD
def save_source(source: Source):
    conn = get_connection()
    conn.execute("""
    INSERT INTO sources (id, name, type, url, priority, enabled, fetch_method, last_checked_at, last_success_at, failure_count, status, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        name=excluded.name,
        type=excluded.type,
        url=excluded.url,
        priority=excluded.priority,
        enabled=excluded.enabled,
        fetch_method=excluded.fetch_method,
        last_checked_at=coalesce(excluded.last_checked_at, sources.last_checked_at),
        last_success_at=coalesce(excluded.last_success_at, sources.last_success_at),
        failure_count=excluded.failure_count,
        status=excluded.status,
        notes=excluded.notes;
    """, (
        source.id, source.name, source.type, source.url, source.priority,
        source.enabled, source.fetch_method, source.last_checked_at,
        source.last_success_at, source.failure_count, source.status, source.notes
    ))
    conn.commit()
    conn.close()

def get_all_sources() -> List[Source]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sources ORDER BY priority ASC, id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [Source(**dict(r)) for r in rows]

# Event CRUD
def save_event(event: Event):
    conn = get_connection()
    conn.execute("""
    INSERT INTO events (
        id, title, normalized_title, description, start_time, end_time, city, district,
        venue, address, organizer, co_organizers, price, price_text, category, tags, audience,
        source_id, source_name, source_url, signup_url, image_url, sources,
        confidence_score, overall_score, learning_score, networking_score, business_score,
        technical_score, fundraising_score, recommendation_reason, suitable_for,
        not_suitable_for, verification_status, status, first_seen_at, last_seen_at,
        last_verified_at, created_at, updated_at
    ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?, ?
    )
    ON CONFLICT(id) DO UPDATE SET
        title=excluded.title,
        normalized_title=excluded.normalized_title,
        description=excluded.description,
        start_time=excluded.start_time,
        end_time=excluded.end_time,
        city=excluded.city,
        district=excluded.district,
        venue=excluded.venue,
        address=excluded.address,
        organizer=excluded.organizer,
        co_organizers=excluded.co_organizers,
        price=excluded.price,
        price_text=excluded.price_text,
        category=excluded.category,
        tags=excluded.tags,
        audience=excluded.audience,
        signup_url=excluded.signup_url,
        image_url=excluded.image_url,
        sources=excluded.sources,
        confidence_score=excluded.confidence_score,
        overall_score=excluded.overall_score,
        learning_score=excluded.learning_score,
        networking_score=excluded.networking_score,
        business_score=excluded.business_score,
        technical_score=excluded.technical_score,
        fundraising_score=excluded.fundraising_score,
        recommendation_reason=excluded.recommendation_reason,
        suitable_for=excluded.suitable_for,
        not_suitable_for=excluded.not_suitable_for,
        verification_status=excluded.verification_status,
        status=excluded.status,
        last_seen_at=excluded.last_seen_at,
        last_verified_at=excluded.last_verified_at,
        updated_at=excluded.updated_at;
    """, (
        event.id, event.title, event.normalized_title, event.description, event.start_time, event.end_time,
        event.city, event.district, event.venue, event.address, event.organizer, json.dumps(event.co_organizers, ensure_ascii=False),
        event.price, event.price_text, event.category, json.dumps(event.tags, ensure_ascii=False), event.audience,
        event.source_id, event.source_name, event.source_url, event.signup_url, event.image_url, json.dumps(event.sources, ensure_ascii=False),
        event.confidence_score, event.overall_score, event.learning_score, event.networking_score, event.business_score,
        event.technical_score, event.fundraising_score, event.recommendation_reason, event.suitable_for,
        event.not_suitable_for, event.verification_status, event.status, event.first_seen_at, event.last_seen_at,
        event.last_verified_at, event.created_at, event.updated_at
    ))
    conn.commit()
    conn.close()

def get_all_events(status: Optional[str] = None, category: Optional[str] = None) -> List[Event]:
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM events WHERE 1=1"
    params = []
    if status and status != 'all':
        query += " AND status = ?"
        params.append(status)
    if category and category != 'all':
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY start_time ASC, overall_score DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    events = []
    for r in rows:
        d = dict(r)
        d['co_organizers'] = json.loads(d['co_organizers'] or '[]')
        d['tags'] = json.loads(d['tags'] or '[]')
        d['sources'] = json.loads(d['sources'] or '[]')
        events.append(Event(**d))
    return events

# Business Signals CRUD
def record_business_signal(organization: str, signal_type: str, evidence: str, potential_value: str):
    if not organization or organization in ["未知", "官方", "个人", "主办方"]:
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, frequency, evidence FROM business_signals WHERE organization = ? AND signal_type = ?", (organization, signal_type))
    row = cursor.fetchone()
    now_str = os.environ.get("MOCK_NOW", "") or ""
    import datetime
    now_iso = datetime.datetime.now().isoformat()
    if row:
        new_freq = row["frequency"] + 1
        new_evidence = f"{row['evidence']} | {evidence}"[:500]
        cursor.execute("""
            UPDATE business_signals 
            SET frequency = ?, evidence = ?, updated_at = ? 
            WHERE id = ?
        """, (new_freq, new_evidence, now_iso, row["id"]))
    else:
        import uuid
        cursor.execute("""
            INSERT INTO business_signals (id, organization, signal_type, evidence, frequency, potential_value, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, ?, ?, ?)
        """, (str(uuid.uuid4()), organization, signal_type, evidence[:500], potential_value, now_iso, now_iso))
    conn.commit()
    conn.close()

def get_business_signals() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM business_signals ORDER BY frequency DESC, updated_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Pipeline Runs CRUD
def save_pipeline_run(run: PipelineRun):
    conn = get_connection()
    conn.execute("""
    INSERT INTO pipeline_runs (
        id, start_time, end_time, scanned_sources, success_sources, failed_sources,
        candidate_events, new_events, updated_events, duplicate_events, rejected_events,
        ai_calls, estimated_tokens, status, summary
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        end_time=excluded.end_time,
        scanned_sources=excluded.scanned_sources,
        success_sources=excluded.success_sources,
        failed_sources=excluded.failed_sources,
        candidate_events=excluded.candidate_events,
        new_events=excluded.new_events,
        updated_events=excluded.updated_events,
        duplicate_events=excluded.duplicate_events,
        rejected_events=excluded.rejected_events,
        ai_calls=excluded.ai_calls,
        estimated_tokens=excluded.estimated_tokens,
        status=excluded.status,
        summary=excluded.summary;
    """, (
        run.id, run.start_time, run.end_time, run.scanned_sources, run.success_sources, run.failed_sources,
        run.candidate_events, run.new_events, run.updated_events, run.duplicate_events, run.rejected_events,
        run.ai_calls, run.estimated_tokens, run.status, run.summary
    ))
    conn.commit()
    conn.close()

def get_recent_pipeline_runs(limit: int = 10) -> List[PipelineRun]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pipeline_runs ORDER BY start_time DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [PipelineRun(**dict(r)) for r in rows]
