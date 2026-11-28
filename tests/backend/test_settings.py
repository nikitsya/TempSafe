"""Check backend settings, defaults and compatibility with older deployments."""

import pytest

from tempsafe.settings import WebPushSettings, project_setting


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


def test_web_push_hosts_can_be_replaced_or_disabled(monkeypatch):
    monkeypatch.delenv("WEB_PUSH_HOSTS", raising=False)
    assert WebPushSettings.from_env().allowed_hosts == {
        "fcm.googleapis.com", "updates.push.services.mozilla.com", "web.push.apple.com",
    }
    monkeypatch.setenv("WEB_PUSH_HOSTS", "One.Example,two.example")
    assert WebPushSettings.from_env().allowed_hosts == {"one.example", "two.example"}
    monkeypatch.setenv("WEB_PUSH_HOSTS", "")
    assert not WebPushSettings.from_env().allowed_hosts
