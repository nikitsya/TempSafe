"""Record UTC observation times only when the Pi reports synchronised time."""

import asyncio
from datetime import datetime, timezone


async def observation_time():
    """Return None if systemd cannot confirm synchronisation within two seconds."""
    process = None
    try:
        process = await asyncio.create_subprocess_exec(
            "timedatectl", "show", "--property=NTPSynchronized", "--value",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await asyncio.wait_for(process.communicate(), timeout=2)
        if process.returncode == 0 and stdout.strip() == b"yes":
            return datetime.now(timezone.utc).isoformat(timespec="seconds")
    except (OSError, asyncio.TimeoutError):
        pass
    finally:
        if process is not None and process.returncode is None:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            await process.wait()
    return None
