from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from kreo_control.api.app import app
from kreo_control.lighting.matrix import load_swarm75_led_map


@pytest.fixture
def client():
    return TestClient(app)


def test_lighting_modes_endpoint(client: TestClient):
    resp = client.get("/api/lighting/modes")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 20
    names = [d["name"] for d in data]
    assert "Rainbow" in names
    assert "Static" in names
    assert "Breathing" in names

