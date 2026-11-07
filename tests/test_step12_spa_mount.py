"""Test serving built frontend React single page application."""

import pytest
from httpx import ASGITransport, AsyncClient
from api.app import app


@pytest.mark.asyncio
async def test_frontend_spa_served():
    """Verify that root / serves index.html."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        assert "<div id=\"root\"></div>" in resp.text
        assert "VentureTwin" in resp.text
