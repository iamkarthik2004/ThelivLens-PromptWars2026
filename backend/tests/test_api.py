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
async def test_upload_returns_analysis(client: AsyncClient):
    response = await client.post("/api/v1/analyses/upload", files={"file": ("test.jpg", b"test-image", "image/jpeg")})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "test.jpg"
    assert body["media_kind"] == "image"
    assert body["report"]["confidence"] >= 78


@pytest.mark.anyio
async def test_rejects_unsupported_media(client: AsyncClient):
    response = await client.post("/api/v1/analyses/upload", files={"file": ("file.pdf", b"x", "application/pdf")})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_analysis_and_missing_id(client: AsyncClient):
    created = await client.post("/api/v1/analyses/url", json={"url": "https://example.com/media.jpg"})
    analysis_id = created.json()["id"]
    assert (await client.get(f"/api/v1/analyses/{analysis_id}")).status_code == 200
    assert (await client.get("/api/v1/analyses/not-found")).status_code == 404
