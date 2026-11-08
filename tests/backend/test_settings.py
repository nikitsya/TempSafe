"""Check compatibility and precedence for renamed environment settings."""

import pytest

from tempsafe.settings import project_setting


@pytest.mark.parametrize("suffix", ["DEVICE_KEY", "DEVICE_BOX_ID", "CONFIG_ADMIN_TOKEN", "LOCAL_MQTT"])
def test_legacy_settings_remain_available(monkeypatch, suffix):
    monkeypatch.delenv(f"TEMPSAFE_{suffix}", raising=False)
    monkeypatch.setenv(f"TEMSAFE_{suffix}", "legacy")
    assert project_setting(f"TEMPSAFE_{suffix}") == "legacy"


@pytest.mark.parametrize("value", ["replacement", ""])
def test_new_setting_overrides_legacy_even_when_empty(monkeypatch, value):
    monkeypatch.setenv("TEMSAFE_DEVICE_KEY", "legacy")
    monkeypatch.setenv("TEMPSAFE_DEVICE_KEY", value)
    assert project_setting("TEMPSAFE_DEVICE_KEY") == value


def test_missing_setting_uses_default(monkeypatch):
    monkeypatch.delenv("TEMSAFE_LOCAL_MQTT", raising=False)
    monkeypatch.delenv("TEMPSAFE_LOCAL_MQTT", raising=False)
    assert project_setting("TEMPSAFE_LOCAL_MQTT", "0") == "0"
