from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class GenerateRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    tone: str = Field(default="confident", description="formal | confident | casual | enthusiastic")
    job_title: str = Field(default="")
    company: str = Field(default="")


class RegenerateRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    original_letter: str
    feedback: str
    tone: str = "confident"
    role: str = ""
    company: str = ""


class MatchItem(BaseModel):
    resume_chunk: str
    jd_requirement: str
    score: float


class CoverLetterResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    cover_letter: str
    match_score: float
    tone_used: str
    tone_label: str
    tone_emoji: str
    top_matches: List[MatchItem]
    jd_role: str
    jd_company: str
    candidate_name: str
    model_used: str
    latency_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    status: str
    ollama_connected: bool
    model: str
    version: str
