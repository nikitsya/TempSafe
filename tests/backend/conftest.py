"""Supply explicit box assignments for route tests that exercise other behaviour."""

import pytest

from tempsafe.api.auth import accessible_boxes
from tempsafe.main import app


@pytest.fixture
def grant_boxes(monkeypatch):
    def grant(*box_ids):
        monkeypatch.setitem(app.dependency_overrides, accessible_boxes, lambda: list(box_ids))

    return grant
