from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from kreo_control.ambience.controller import AmbienceController
from kreo_control.ambience.models import AmbienceConfig, AmbienceMode
from kreo_control.ambience.sampler import ScreenSampler, boost_saturation_and_brightness
from kreo_control.api.app import create_app


def test_saturation_and_brightness_boost():
    # Test neutral gray
    r, g, b = boost_saturation_and_brightness(128, 128, 128, sat_boost=1.5, bright_mult=1.0)
    assert 0 <= r <= 255
    assert 0 <= g <= 255
    assert 0 <= b <= 255

    # Test pure red
    r, g, b = boost_saturation_and_brightness(255, 0, 0, sat_boost=1.2, bright_mult=0.5)
    assert r == 127
    assert g == 0
    assert b == 0


def test_screen_sampler_modes():
    sampler = ScreenSampler()
    
    # Test SPATIAL
    cfg_spatial = AmbienceConfig(mode=AmbienceMode.SPATIAL)
    colors = sampler.sample_keys(cfg_spatial)
    assert len(colors) == 82
    assert "w" in colors
    assert colors["w"].startswith("#")

    # Test AVERAGE
    cfg_avg = AmbienceConfig(mode=AmbienceMode.AVERAGE)
    colors_avg = sampler.sample_keys(cfg_avg)
    assert len(colors_avg) == 82
    assert "space" in colors_avg

    # Test CENTER
    cfg_center = AmbienceConfig(mode=AmbienceMode.CENTER)
    colors_center = sampler.sample_keys(cfg_center)
    assert len(colors_center) == 82


def test_ambience_controller_config():
    ctrl = AmbienceController()
    cfg = AmbienceConfig(mode=AmbienceMode.CENTER, fps=20, smoothness=0.3)
    updated = ctrl.update_config(cfg)
    assert updated.fps == 20
    assert updated.mode == AmbienceMode.CENTER
    status = ctrl.get_status()
    assert status.config.fps == 20


def test_ambience_api_routes():
    app = create_app()
    client = TestClient(app)

    # Status
    res = client.get("/api/ambience/status")
    assert res.status_code == 200
    data = res.json()
    assert "running" in data
    assert "config" in data

    # Update config
    res_cfg = client.post("/api/ambience/config", json={
        "mode": "spatial",
        "fps": 18,
        "smoothness": 0.5,
        "saturation_boost": 1.4,
        "brightness_multiplier": 0.9,
    })
    assert res_cfg.status_code == 200
    assert res_cfg.json()["fps"] == 18

    # Colors
    res_colors = client.get("/api/ambience/colors")
    assert res_colors.status_code == 200
    assert "colors" in res_colors.json()

