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

