from datetime import datetime
from typing import Literal, Any
from pydantic import BaseModel, Field, HttpUrl

MediaKind = Literal["image", "video", "audio", "remote-media"]

class Evidence(BaseModel):
    title: str
    description: str
    severity: Literal["High", "Medium", "Low"] = "Medium"
    confidence: int = Field(ge=0, le=100)
    icon: str = "Search"

class SourceEvent(BaseModel):
    date: str
    source: str
    platform: str
    caption: str
    status: Literal["Unverified", "Review", "Warning"] = "Unverified"

class AnalysisReport(BaseModel):
    verdict: str
    confidence: int = Field(ge=0, le=100)
    metrics: dict[str, int]
    evidence: list[Evidence] = []
    source_events: list[SourceEvent] = []
    disclaimer: str
    ai_explanation: dict[str, Any] = {}

class AnalysisResponse(BaseModel):
    id: str
    analysis_id: str | None = None
    name: str
    filename: str | None = None
    type: str
    media_kind: MediaKind
    media_type: str | None = None
    status: Literal["completed", "failed"]
    created_at: datetime
    report: AnalysisReport
    overall_verdict: str | None = None
    confidence: int | None = None
    ai_probability: int | None = None
    manipulation_probability: int | None = None
    authentic_probability: int | None = None
    evidence_data: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] = {}
    source_trace: list[dict[str, Any]] = []

class UrlAnalysisRequest(BaseModel):
    url: HttpUrl

class ClaimRequest(BaseModel):
    claim: str = Field(min_length=1, max_length=5000)

class CopilotRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    analysis_context: dict[str, Any] = {}
