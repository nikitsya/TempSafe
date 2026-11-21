"""Keep the retained MQTT configuration aligned with the selected MySQL profile."""

import asyncio
import json
import logging
import re

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from tempsafe.db.models import Box, BoxConfiguration, ThresholdProfile

LOGGER = logging.getLogger(__name__)


class ConfigurationPublisher:
    """Reconcile one box's desired limits without claiming device adoption."""

    def __init__(self, mqtt, box_id, session_factory, interval=30):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", box_id):
            raise ValueError("Invalid MQTT box ID")
        self.client = mqtt.client
        self.box_id = box_id
        self.topic = f"tempsafe/boxes/{box_id}/configuration"
        self.session_factory = session_factory
        self.interval = interval
        self._requested = asyncio.Event()

        @mqtt.on_connect()
        def connected(client, flags, reason_code, properties):
            if reason_code == 0:
                self.request_publish(box_id)

    def request_publish(self, box_id):
        """Wake the worker after a commit or connection, coalescing rapid updates."""
        if box_id == self.box_id:
            self._requested.set()

    async def publish_current(self):
        """Read committed limits afresh and serialise publication with API writes."""
        if not self.client.is_connected:
            return
        async with self.session_factory() as db:
            async with db.begin():
                # The API locks this same row before selecting a new profile.
                box = await db.scalar(select(Box).where(Box.box_id == self.box_id).with_for_update())
                if box is None:
                    return
                profile = await db.scalar(
                    select(ThresholdProfile)
                    .join(BoxConfiguration, (
                        (BoxConfiguration.profile_id == ThresholdProfile.profile_id)
                        & (BoxConfiguration.box_id == ThresholdProfile.box_id)
                    ))
                    .where(BoxConfiguration.box_id == self.box_id)
                )
                if profile is None or not self.client.is_connected:
                    return
                payload = json.dumps({
                    "schema_version": 1,
                    "box_id": self.box_id,
                    "profile_id": profile.profile_id,
                    "lower_c": format(profile.lower_c, ".2f"),
                    "warning_c": format(profile.warning_c, ".2f"),
                    "upper_c": format(profile.upper_c, ".2f"),
                })
                # Queue publication before releasing the box lock. No network await
                # may separate this read from publish, or an older profile could win.
                self.client.publish(self.topic, payload, qos=1, retain=True)

    async def run(self):
        """Retry from durable desired state after failures, restarts and reconnects."""
        while True:
            self._requested.clear()
            try:
                async with asyncio.timeout(10):
                    await self.publish_current()
            except (SQLAlchemyError, OSError, TimeoutError):
                # Avoid exposing connection details or credentials in logs.
                LOGGER.warning("Configuration publication failed; the selected profile will be retried")
            # gmqtt.publish queues a message; it does not confirm device adoption.
            # Periodic publication also repairs lost retained state on the broker.
            try:
                await asyncio.wait_for(self._requested.wait(), timeout=self.interval)
            except TimeoutError:
                pass
