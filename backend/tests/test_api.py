import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
            yield test_client


@pytest.mark.anyio
async def test_health(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.anyio
async def test_health_v2(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "huggingface_configured" in body
    assert "mongodb_configured" in body


@pytest.mark.anyio
async def test_upload_returns_analysis(client: AsyncClient):
    response = await client.post("/api/v1/analyses/upload", files={"file": ("test.jpg", b"test-image", "image/jpeg")})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "test.jpg"
    assert body["media_kind"] == "image"
    assert body["report"]["confidence"] >= 20


@pytest.mark.anyio
async def test_upload_v2(client: AsyncClient):
    response = await client.post("/api/analyze/upload", files={"file": ("photo.jpg", b"test-image-data", "image/jpeg")})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "photo.jpg"
    assert body["media_kind"] == "image"
    assert "id" in body
    assert "report" in body
    assert body["report"]["confidence"] >= 0


@pytest.mark.anyio
async def test_upload_png(client: AsyncClient):
    response = await client.post("/api/analyze/upload", files={"file": ("image.png", b"png-data", "image/png")})
    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "image/png"
    assert body["media_kind"] == "image"


@pytest.mark.anyio
async def test_upload_webp(client: AsyncClient):
    response = await client.post("/api/analyze/upload", files={"file": ("photo.webp", b"webp-data", "image/webp")})
    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "image/webp"
    assert body["media_kind"] == "image"


@pytest.mark.anyio
async def test_upload_video(client: AsyncClient):
    response = await client.post("/api/analyze/upload", files={"file": ("video.mp4", b"video-data", "video/mp4")})
    assert response.status_code == 201
    body = response.json()
    assert body["media_kind"] == "video"


@pytest.mark.anyio
async def test_upload_audio(client: AsyncClient):
    response = await client.post("/api/analyze/upload", files={"file": ("audio.wav", b"audio-data", "audio/wav")})
    assert response.status_code == 201
    body = response.json()
    assert body["media_kind"] == "audio"


@pytest.mark.anyio
async def test_rejects_unsupported_media(client: AsyncClient):
    response = await client.post("/api/v1/analyses/upload", files={"file": ("file.pdf", b"x", "application/pdf")})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_rejects_unsupported_media_v2(client: AsyncClient):
    response = await client.post("/api/analyze/upload", files={"file": ("file.txt", b"hello", "text/plain")})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_analysis_and_missing_id(client: AsyncClient):
    created = await client.post("/api/v1/analyses/url", json={"url": "https://example.com/media.jpg"})
    analysis_id = created.json()["id"]
    assert (await client.get(f"/api/v1/analyses/{analysis_id}")).status_code == 200
    assert (await client.get("/api/v1/analyses/not-found")).status_code == 404


@pytest.mark.anyio
async def test_get_analysis_v2(client: AsyncClient):
    created = await client.post("/api/analyze/url", json={"url": "https://example.com/photo.jpg"})
    assert created.status_code == 201
    analysis_id = created.json()["id"]
    response = await client.get(f"/api/analyze/{analysis_id}")
    assert response.status_code == 200
    assert response.json()["id"] == analysis_id


@pytest.mark.anyio
async def test_get_analysis_not_found_v2(client: AsyncClient):
    response = await client.get("/api/analyze/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_list_recent_analyses(client: AsyncClient):
    await client.post("/api/analyze/upload", files={"file": ("test1.jpg", b"data1", "image/jpeg")})
    await client.post("/api/analyze/upload", files={"file": ("test2.jpg", b"data2", "image/jpeg")})
    response = await client.get("/api/analyze")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 2


@pytest.mark.anyio
async def test_delete_analysis(client: AsyncClient):
    created = await client.post("/api/analyze/url", json={"url": "https://example.com/delete-me.jpg"})
    analysis_id = created.json()["id"]
    delete_resp = await client.delete(f"/api/analyze/{analysis_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] is True
    get_resp = await client.get(f"/api/analyze/{analysis_id}")
    assert get_resp.status_code == 404


@pytest.mark.anyio
async def test_delete_analysis_not_found(client: AsyncClient):
    response = await client.delete("/api/analyze/nonexistent")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_source_trace(client: AsyncClient):
    created = await client.post("/api/analyze/url", json={"url": "https://example.com/trace.jpg"})
    analysis_id = created.json()["id"]
    response = await client.get(f"/api/analyze/{analysis_id}/source-trace")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert "source" in body[0]
    assert "date" in body[0]


@pytest.mark.anyio
async def test_source_trace_not_found(client: AsyncClient):
    response = await client.get("/api/analyze/fake-id/source-trace")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_copilot_endpoint(client: AsyncClient):
    response = await client.post("/api/analyze/copilot", json={"question": "Can I trust this media?", "analysis_context": {}})
    assert response.status_code == 200
    body = response.json()
    assert "answer" in body
    assert "question" in body
    assert len(body["answer"]) > 0


@pytest.mark.anyio
async def test_copilot_with_context(client: AsyncClient):
    context = {
        "overall_verdict": "likely_ai_generated",
        "confidence": 85,
        "report": {
            "metrics": {"ai_generated": 85, "manipulated": 50, "authentic": 15},
            "evidence": [{"title": "Noise pattern", "description": "test", "severity": "High", "confidence": 80}]
        }
    }
    response = await client.post("/api/analyze/copilot", json={"question": "Why was this flagged?", "analysis_context": context})
    assert response.status_code == 200
    body = response.json()
    assert len(body["answer"]) > 0


@pytest.mark.anyio
async def test_copilot_verify_question(client: AsyncClient):
    response = await client.post("/api/analyze/copilot", json={"question": "What should I verify next?", "analysis_context": {}})
    assert response.status_code == 200
    body = response.json()
    assert len(body["answer"]) > 0


@pytest.mark.anyio
async def test_claim_endpoint(client: AsyncClient):
    response = await client.post("/api/analyze/claim", json={"claim": "This photo is from 2024"})
    assert response.status_code == 200
    body = response.json()
    assert "claim" in body
    assert "assessment" in body
    assert body["claim"] == "This photo is from 2024"


@pytest.mark.anyio
async def test_claim_empty_rejected(client: AsyncClient):
    response = await client.post("/api/analyze/claim", json={"claim": ""})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_url_analysis(client: AsyncClient):
    response = await client.post("/api/analyze/url", json={"url": "https://example.com/image.jpg"})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "example.com"
    assert body["media_kind"] == "image"
    assert "id" in body


@pytest.mark.anyio
async def test_url_analysis_invalid(client: AsyncClient):
    response = await client.post("/api/analyze/url", json={"url": "not-a-url"})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_analysis_response_fields(client: AsyncClient):
    response = await client.post("/api/analyze/upload", files={"file": ("test.jpg", b"test", "image/jpeg")})
    body = response.json()
    required_fields = ["id", "name", "type", "media_kind", "status", "created_at", "report", "overall_verdict", "confidence"]
    for field in required_fields:
        assert field in body, f"Missing field: {field}"
    assert body["status"] == "completed"
    assert "verdict" in body["report"]
    assert "metrics" in body["report"]
    assert "evidence" in body["report"]
    assert "disclaimer" in body["report"]


@pytest.mark.anyio
async def test_report_metrics(client: AsyncClient):
    response = await client.post("/api/analyze/upload", files={"file": ("test.jpg", b"test", "image/jpeg")})
    metrics = response.json()["report"]["metrics"]
    assert "ai_generated" in metrics
    assert "manipulated" in metrics
    assert "authentic" in metrics
    assert 0 <= metrics["ai_generated"] <= 100
    assert 0 <= metrics["manipulated"] <= 100
    assert 0 <= metrics["authentic"] <= 100


@pytest.mark.anyio
async def test_cors_headers(client: AsyncClient):
    response = await client.options("/api/health", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET"
    })
    assert response.status_code == 200


@pytest.mark.anyio
async def test_upload_multiple_files_sequential(client: AsyncClient):
    ids = []
    for i in range(3):
        resp = await client.post("/api/analyze/upload", files={"file": (f"file{i}.jpg", b"data", "image/jpeg")})
        assert resp.status_code == 201
        ids.append(resp.json()["id"])
    assert len(set(ids)) == 3, "Each upload should produce a unique ID"


@pytest.mark.anyio
async def test_analysis_has_evidence(client: AsyncClient):
    response = await client.post("/api/analyze/upload", files={"file": ("test.jpg", b"test", "image/jpeg")})
    evidence = response.json()["report"]["evidence"]
    assert isinstance(evidence, list)
    assert len(evidence) >= 1
    for item in evidence:
        assert "title" in item
        assert "description" in item
        assert "confidence" in item
        assert "severity" in item
