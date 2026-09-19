from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_me_requires_authentication():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/auth/me")
    assert response.status_code == 401


async def test_admins_list_requires_authentication():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/admins")
    assert response.status_code == 401


async def test_refresh_requires_refresh_cookie():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/auth/refresh")
    assert response.status_code == 401


async def test_google_login_rejects_invalid_credential():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/auth/google", json={"id_token": "not-a-real-token"})
    assert response.status_code == 401
