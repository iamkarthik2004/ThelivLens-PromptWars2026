import hashlib
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import Settings
from app.schemas import AnalysisReport, Evidence, SourceEvent

ALLOWED_MEDIA_TYPES = {
    "image/jpeg": "image", "image/png": "image", "image/webp": "image",
    "video/mp4": "video", "video/quicktime": "video",
    "audio/mpeg": "audio", "audio/wav": "audio", "audio/x-wav": "audio",
}


def media_kind(content_type: str) -> str:
    return ALLOWED_MEDIA_TYPES.get(content_type, "")


async def read_validated_upload(upload: UploadFile, max_bytes: int) -> tuple[bytes, str]:
    content_type = upload.content_type or ""
    if content_type not in ALLOWED_MEDIA_TYPES:
        raise ValueError("Unsupported media type. Use JPG, PNG, WEBP, MP4, MOV, MP3, or WAV.")
    data = await upload.read(max_bytes + 1)
    if not data:
        raise ValueError("The uploaded file is empty.")
    if len(data) > max_bytes:
        raise ValueError("Files must be 500 MB or smaller.")
    return data, content_type


def mock_report(seed: str) -> AnalysisReport:
    value = int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16)
    confidence = 78 + value % 15
    return AnalysisReport(
        verdict="Likely AI-Generated",
        confidence=confidence,
        metrics={"ai_generated": confidence, "manipulated": 48 + value % 18, "authentic": 11 + value % 12},
        evidence=[
            Evidence(title="Face & Skin Analysis", description="Unusual texture consistency and facial-region artifacts detected.", severity="High", confidence=min(96, confidence + 2), icon="ScanFace"),
            Evidence(title="Lighting Analysis", description="Light direction differs slightly between the subject and background.", severity="Medium", confidence=72 + value % 10, icon="SunMedium"),
            Evidence(title="Pixel Analysis", description="High-frequency patterns differ from typical camera-generated imagery.", severity="High", confidence=min(97, confidence + 4), icon="ScanSearch"),
            Evidence(title="Metadata", description="Original EXIF metadata is missing from the submitted file.", severity="Medium", confidence=84, icon="FileSearch"),
            Evidence(title="Model Consensus", description="Multiple independent signals point to synthetic-generation traits.", severity="High", confidence=confidence, icon="BrainCircuit"),
        ],
        source_events=[
            SourceEvent(date="Unknown", source="Original upload", platform="Unverified", caption="Earliest available instance could not be independently confirmed.", status="Unverified"),
            SourceEvent(date="Aug 28, 2026", source="Social repost", platform="Social network", caption="Caption changed to imply a recent event.", status="Review"),
            SourceEvent(date="Sep 02, 2026", source="Viral post", platform="Social network", caption="Shared widely with materially different context.", status="Warning"),
        ],
        disclaimer="This assessment is probabilistic and should be corroborated with independent evidence before drawing conclusions.",
    )


class LocalObjectStorage:
    """Development storage adapter; production uses S3ObjectStorage."""
    def __init__(self) -> None:
        self.directory = Path("uploads")
        self.directory.mkdir(parents=True, exist_ok=True)

    async def put(self, filename: str, data: bytes, content_type: str) -> str:
        key = f"uploads/{uuid4()}-{filename}"
        destination = Path(key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        return key


class S3ObjectStorage:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def put(self, filename: str, data: bytes, content_type: str) -> str:
        import aioboto3
        key = f"uploads/{uuid4()}-{filename}"
        session = aioboto3.Session()
        async with session.client(
            "s3", endpoint_url=self.settings.s3_endpoint_url, region_name=self.settings.s3_region,
            aws_access_key_id=self.settings.s3_access_key_id, aws_secret_access_key=self.settings.s3_secret_access_key,
        ) as client:
            await client.put_object(Bucket=self.settings.s3_bucket, Key=key, Body=data, ContentType=content_type)
        return key


class InMemoryRepository:
    """Development and test repository; matches the Mongo repository interface."""
    def __init__(self) -> None:
        self.records: dict[str, dict] = {}

    async def create(self, record: dict) -> dict:
        self.records[record["id"]] = record
        return record

    async def get(self, analysis_id: str) -> dict | None:
        return self.records.get(analysis_id)


class MongoRepository:
    def __init__(self, uri: str, database: str) -> None:
        from motor.motor_asyncio import AsyncIOMotorClient
        self.client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=8_000)
        self.collection = self.client[database]["analyses"]

    async def connect(self) -> None:
        await self.client.admin.command("ping")
        await self.collection.create_index("id", unique=True)
        await self.collection.create_index("created_at")

    async def create(self, record: dict) -> dict:
        await self.collection.insert_one(record)
        return record

    async def get(self, analysis_id: str) -> dict | None:
        return await self.collection.find_one({"id": analysis_id}, {"_id": 0})

    def close(self) -> None:
        self.client.close()


def create_record(name: str, content_type: str, kind: str, object_key: str | None, seed: str) -> dict:
    return {
        "id": str(uuid4()), "name": name, "type": content_type, "media_kind": kind,
        "status": "completed", "created_at": datetime.now(timezone.utc), "object_key": object_key,
        "report": mock_report(seed).model_dump(),
    }
