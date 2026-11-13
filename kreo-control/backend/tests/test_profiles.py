from __future__ import annotations

import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from kreo_control.api.app import app
from kreo_control.profiles.models import ProfileCreateRequest, ProfileLightingData, ProfileUpdateRequest
from kreo_control.profiles.store import ProfilesStore


@pytest.fixture
def temp_store(tmp_path: Path):
    store_file = tmp_path / "profiles.json"
    return ProfilesStore(path=store_file)


def test_default_profiles_initialization(temp_store: ProfilesStore):
    profiles = temp_store.list_all()
    assert len(profiles) >= 3
    active = temp_store.get_active()
    assert active is not None
    assert active.is_active is True


def test_create_and_update_profile(temp_store: ProfilesStore):
    created = temp_store.create(
        ProfileCreateRequest(
            name="Testing Profile",
            description="Unit test profile",
            lighting=ProfileLightingData(mode_id=1, color="#00FF00"),
        )
    )
    assert created.name == "Testing Profile"
    assert created.lighting.color == "#00FF00"

    updated = temp_store.update(
        created.id,
        ProfileUpdateRequest(name="Updated Name", description="New description"),
    )
    assert updated is not None
    assert updated.name == "Updated Name"
    assert updated.description == "New description"


def test_duplicate_and_delete_profile(temp_store: ProfilesStore):
    initial_count = len(temp_store.list_all())
    active = temp_store.get_active()
    assert active is not None

    cloned = temp_store.duplicate(active.id)
    assert cloned is not None
    assert cloned.name.endswith("(Copy)")
    assert len(temp_store.list_all()) == initial_count + 1

    # Delete cloned profile
    deleted = temp_store.delete(cloned.id)
    assert deleted is True
    assert len(temp_store.list_all()) == initial_count


def test_export_and_import_profile(temp_store: ProfilesStore):
    active = temp_store.get_active()
    assert active is not None
    exported = temp_store.export_profile(active.id)
    assert exported is not None
    assert "lighting" in exported

    imported = temp_store.import_profile(exported)
    assert imported.id != active.id
    assert imported.lighting.mode_id == active.lighting.mode_id


def test_api_profiles_endpoints():
    client = TestClient(app)
    resp = client.get("/api/profiles")
    assert resp.status_code == 200
    data = resp.json()
    assert "profiles" in data
    assert len(data["profiles"]) >= 1
    assert data["active_profile_id"] is not None

