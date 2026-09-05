import pytest
from pathlib import Path
from PIL import Image


def _create_test_image(tmp_path: Path, width=100, height=100, color=(128, 64, 32)) -> Path:
    img = Image.new("RGB", (width, height), color)
    path = tmp_path / "test.jpg"
    img.save(path, "JPEG")
    return path


class TestDetector:
    def test_returns_valid_structure(self, tmp_path):
        from app.services.detector import detect_media
        path = _create_test_image(tmp_path)
        result = detect_media(str(path), "image", None)
        assert "ai_probability" in result
        assert "manipulation_probability" in result
        assert "authentic_probability" in result
        assert "signals" in result
        assert isinstance(result["signals"], list)

    def test_ai_probability_in_range(self, tmp_path):
        from app.services.detector import detect_media
        path = _create_test_image(tmp_path)
        result = detect_media(str(path), "image", None)
        assert 0 <= result["ai_probability"] <= 100
        assert 0 <= result["manipulation_probability"] <= 100
        assert 0 <= result["authentic_probability"] <= 100

    def test_signals_have_required_fields(self, tmp_path):
        from app.services.detector import detect_media
        path = _create_test_image(tmp_path)
        result = detect_media(str(path), "image", None)
        for signal in result["signals"]:
            assert "name" in signal
            assert "description" in signal
            assert "confidence" in signal

    def test_with_camera_metadata(self, tmp_path):
        from app.services.detector import detect_media
        path = _create_test_image(tmp_path)
        metadata = {"exif": {271: "Canon", 272: "EOS R5", 305: "Adobe Photoshop"}}
        result = detect_media(str(path), "image", metadata)
        assert result["ai_probability"] < 70

    def test_with_ai_software_metadata(self, tmp_path):
        from app.services.detector import detect_media
        path = _create_test_image(tmp_path)
        metadata = {"exif": {305: "Stable Diffusion"}}
        result = detect_media(str(path), "image", metadata)
        assert result["ai_probability"] > 40

    def test_with_no_metadata(self, tmp_path):
        from app.services.detector import detect_media
        path = _create_test_image(tmp_path)
        result = detect_media(str(path), "image", None)
        assert isinstance(result["signals"], list)

    def test_non_image_type(self, tmp_path):
        from app.services.detector import detect_media
        result = detect_media(str(tmp_path), "video", None)
        assert "ai_probability" in result
        assert result["signals"]


class TestSourceTrace:
    def test_fallback_returns_list(self):
        from app.services.source_trace import source_trace_fallback
        result = source_trace_fallback()
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_fallback_has_required_fields(self):
        from app.services.source_trace import source_trace_fallback
        result = source_trace_fallback()
        for event in result:
            assert "source" in event
            assert "date" in event
            assert "platform" in event
            assert "caption" in event
            assert "status" in event

    def test_from_metadata_with_exif(self):
        from app.services.source_trace import source_trace_from_metadata
        metadata = {"exif": {36867: "2024:01:15 10:30:00", 305: "Adobe Lightroom"}}
        result = source_trace_from_metadata(metadata)
        assert len(result) >= 2
        sources = [e["source"] for e in result]
        assert "File creation" in sources
        assert "Processing detected" in sources

    def test_from_metadata_without_exif(self):
        from app.services.source_trace import source_trace_from_metadata
        metadata = {"exif": {}}
        result = source_trace_from_metadata(metadata)
        assert len(result) >= 1
        assert result[0]["status"] == "Unverified"

    def test_from_metadata_none(self):
        from app.services.source_trace import source_trace_from_metadata
        result = source_trace_from_metadata(None)
        assert len(result) >= 1

    def test_from_metadata_only_creation_date(self):
        from app.services.source_trace import source_trace_from_metadata
        metadata = {"exif": {36867: "2024:03:20 14:00:00"}}
        result = source_trace_from_metadata(metadata)
        assert len(result) >= 1
        assert result[0]["source"] == "File creation"


class TestMediaAnalysis:
    @pytest.mark.anyio
    async def test_extract_image_metadata(self, tmp_path):
        from app.services.media_analysis import extract_metadata
        path = _create_test_image(tmp_path, width=200, height=150)
        metadata = await extract_metadata(str(path), "image")
        assert "format" in metadata
        assert "size_bytes" in metadata
        assert metadata["width"] == 200
        assert metadata["height"] == 150
        assert "exif" in metadata

    @pytest.mark.anyio
    async def test_extract_non_image_metadata(self, tmp_path):
        from app.services.media_analysis import extract_metadata
        path = tmp_path / "video.mp4"
        path.write_bytes(b"fake-video-data")
        metadata = await extract_metadata(str(path), "video")
        assert "format" in metadata
        assert "size_bytes" in metadata
        assert metadata["note"] is not None

    @pytest.mark.anyio
    async def test_extract_audio_metadata(self, tmp_path):
        from app.services.media_analysis import extract_metadata
        path = tmp_path / "audio.wav"
        path.write_bytes(b"fake-audio-data")
        metadata = await extract_metadata(str(path), "audio")
        assert "format" in metadata
        assert "size_bytes" in metadata


class TestDatabase:
    @pytest.mark.anyio
    async def test_in_memory_create_and_get(self):
        from app.database import InMemoryRepository
        repo = InMemoryRepository()
        record = {"analysis_id": "test-123", "filename": "test.jpg", "data": "value"}
        await repo.create(record)
        result = await repo.get("test-123")
        assert result is not None
        assert result["filename"] == "test.jpg"

    @pytest.mark.anyio
    async def test_in_memory_get_missing(self):
        from app.database import InMemoryRepository
        repo = InMemoryRepository()
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.anyio
    async def test_in_memory_list_recent(self):
        from app.database import InMemoryRepository
        repo = InMemoryRepository()
        for i in range(5):
            await repo.create({"analysis_id": f"id-{i}", "filename": f"file{i}.jpg"})
        recent = await repo.list_recent(limit=3)
        assert len(recent) == 3
        assert recent[0]["analysis_id"] == "id-4"

    @pytest.mark.anyio
    async def test_in_memory_delete(self):
        from app.database import InMemoryRepository
        repo = InMemoryRepository()
        await repo.create({"analysis_id": "to-delete", "filename": "x.jpg"})
        deleted = await repo.delete("to-delete")
        assert deleted is True
        assert await repo.get("to-delete") is None

    @pytest.mark.anyio
    async def test_in_memory_delete_missing(self):
        from app.database import InMemoryRepository
        repo = InMemoryRepository()
        deleted = await repo.delete("nonexistent")
        assert deleted is False
