from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from kreo_control.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_keyboard_assets_swarm75(client: TestClient):
    resp = client.get("/api/keyboard-assets/swarm75")
    assert resp.status_code == 200
    data = resp.json()
    assert data["asset_name"] == "swarm75"
    assert data["base_image_url"] == "/keyboard/swarm75/base/default.webp"
    assert data["letters_image_url"] == "/keyboard/swarm75/letters/default.webp"
    assert data["interactive_svg_url"] == "/keyboard/swarm75/overlay/interactive.svg"
    assert data["total_keys"] == 82
    assert len(data["keys"]) == 82
    first_key = data["keys"][0]
    assert first_key["logical_id"] == "ESC"
    assert first_key["svg_id"] == "key_ESC"
    assert first_key["ui_key"] == "esc"


def test_keyboard_assets_not_found(client: TestClient):
    resp = client.get("/api/keyboard-assets/nonexistent")
    assert resp.status_code == 404

