from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from kreo_control.api.app import app

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "app": "kreo-control"}


def test_device_status():
    res = client.get("/api/device/status")
    assert res.status_code == 200
    data = res.json()
    assert "connected" in data


def test_device_diagnostics():
    res = client.get("/api/device/diagnostics")
    assert res.status_code == 200
    data = res.json()
    assert "connected" in data
    assert data["matrix_slots"] == 126
    assert data["physical_keys"] == 82
    assert data["planar_frame_bytes"] == 378
    assert data["light_table_bytes"] == 490
    assert data["keymap_layer_bytes"] == 504


