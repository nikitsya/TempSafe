"""Read backend settings from the service environment."""

import os
from dataclasses import dataclass, field


def project_setting(name: str, default: str = "") -> str:
    """Prefer TEMPSAFE settings, including empty values, over the legacy prefix."""
    if name in os.environ:
        return os.environ[name]
    return os.environ.get(name.replace("TEMPSAFE_", "TEMSAFE_", 1), default)


@dataclass(frozen=True)
class WebPushSettings:
    public_key: str
    private_key: str = field(repr=False)
    subject: str
    allowed_hosts: frozenset[str]

    @property
    def enabled(self) -> bool:
        return bool(self.public_key and self.private_key and self.subject)

    @classmethod
    def from_env(cls) -> "WebPushSettings":
        hosts = os.getenv(
            "WEB_PUSH_HOSTS",
            "fcm.googleapis.com,updates.push.services.mozilla.com,web.push.apple.com",
        )
        return cls(
            public_key=os.getenv("WEB_PUSH_PUBLIC_KEY", ""),
            private_key=os.getenv("WEB_PUSH_PRIVATE_KEY", ""),
            subject=os.getenv("WEB_PUSH_SUBJECT", ""),
            allowed_hosts=frozenset(host for host in hosts.lower().split(",") if host),
        )
