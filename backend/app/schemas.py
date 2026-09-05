from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

MediaKind = Literal["image", "video", "audio", "remote-media"]
AnalysisStatus = Literal["completed", "failed"]


class Evidence(BaseModel):
    title: str
    description: str
    severity: Literal["High", "Medium", "Low"]
    confidence: int = Field(ge=0, le=100)
    icon: str


class SourceEvent(BaseModel):
    date: str
    source: str
    platform: str
    caption: str
    status: Literal["Unverified", "Review", "Warning"]


class AnalysisReport(BaseModel):
    verdict: str
    confidence: int = Field(ge=0, le=100)
    metrics: dict[str, int]
    evidence: list[Evidence]
    source_events: list[SourceEvent]
    disclaimer: str


class AnalysisResponse(BaseModel):
    id: str
    name: str
    type: str
    media_kind: MediaKind
    status: AnalysisStatus
    created_at: datetime
    report: AnalysisReport


class UrlAnalysisRequest(BaseModel):
    url: HttpUrl

