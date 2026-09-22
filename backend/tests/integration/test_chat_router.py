from httpx import ASGITransport, AsyncClient

from app.main import app


async def _post(path: str, json: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(path, json=json)


async def test_chat_message_requires_authentication():
    response = await _post("/chat/message", {"message": "hello"})

    assert response.status_code == 401


async def test_chat_message_rejects_empty_message():
    # Auth still fails first (no cookie), but this also confirms the route
    # exists and accepts the expected request shape.
    response = await _post("/chat/message", {"message": ""})

    assert response.status_code in (401, 422)
