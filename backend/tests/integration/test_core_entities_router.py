from httpx import ASGITransport, AsyncClient

from app.main import app


async def _get(path: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path)


async def test_labourers_list_requires_authentication():
    response = await _get("/labourers")
    assert response.status_code == 401


async def test_sites_list_requires_authentication():
    response = await _get("/sites")
    assert response.status_code == 401


async def test_work_record_board_requires_authentication():
    response = await _get("/work-records/board?site_id=x&work_date=2026-01-01")
    assert response.status_code == 401


async def test_wage_history_requires_authentication():
    response = await _get("/labourers/x/wages")
    assert response.status_code == 401
