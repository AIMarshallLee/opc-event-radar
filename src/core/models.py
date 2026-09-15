from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

class Source(BaseModel):
    id: str
    name: str
    type: str  # event_platform, government, opc_community, organizer, media, public_page, other
    url: str
    priority: int = 1  # 1 (high), 2 (medium), 3 (low)
    enabled: bool = True
    fetch_method: str = "http_html"  # http_html, http_json, web_search, headless
    last_checked_at: Optional[str] = None
    last_success_at: Optional[str] = None
    failure_count: int = 0
    status: str = "active"  # active, degraded, disabled
    notes: str = ""

class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    normalized_title: str
    description: Optional[str] = ""
    start_time: str
    end_time: Optional[str] = None
    city: str = "杭州"
    district: Optional[str] = "未知"  # 余杭, 滨江, 西湖, 上城, 拱墅, 萧山, 钱塘, 临平, 富阳, 临安, 桐庐, 建德, 淳安, 线上
    venue: Optional[str] = "待定"
    address: Optional[str] = ""
    organizer: Optional[str] = "未知"
    co_organizers: List[str] = Field(default_factory=list)
    price: Optional[float] = 0.0
    price_text: Optional[str] = "免费"
    category: str = "AI"  # AI, OPC, FDE, Agent, 开发者, 创业, 投融资, 出海, 电商, 内容, 企业服务, 政策/园区, 具身智能, 其他
    tags: List[str] = Field(default_factory=list)
    audience: Optional[str] = "AI从业者/创业者"
    source_id: str
    source_name: str
    source_url: str
    signup_url: Optional[str] = ""
    image_url: Optional[str] = ""
    sources: List[Dict[str, Any]] = Field(default_factory=list)  # 多来源聚合记录

    # 质量与推荐体系 (总分 100)
    confidence_score: int = 80  # 0-100 可信度
    overall_score: int = 75     # 0-100 综合推荐总分
    learning_score: int = 70    # 知识含金量
    networking_score: int = 70  # 社交人脉
    business_score: int = 70    # 商务商业价值
    technical_score: int = 70   # 技术深度
    fundraising_score: int = 60 # 融资对接价值

    recommendation_reason: str = "具有较高本土产业对接与学习价值"
    suitable_for: str = "AI从业者、OPC独立开发者、创业团队"
    not_suitable_for: str = "寻求基础科普的非技术人群"

    verification_status: str = "verified"  # verified, partially_verified, unverified
    status: str = "upcoming"  # upcoming, today, ongoing, ended, cancelled, postponed, unknown

    first_seen_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_seen_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_verified_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class BusinessSignal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization: str
    signal_type: str  # high_frequency_park, active_opc_community, top_organizer, enterprise, new_startup
    evidence: str
    frequency: int = 1
    potential_value: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class PipelineRun(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    start_time: str
    end_time: Optional[str] = None
    scanned_sources: int = 0
    success_sources: int = 0
    failed_sources: int = 0
    candidate_events: int = 0
    new_events: int = 0
    updated_events: int = 0
    duplicate_events: int = 0
    rejected_events: int = 0
    ai_calls: int = 0
    estimated_tokens: int = 0
    status: str = "running"  # running, success, partial_failure, failure
    summary: str = ""
