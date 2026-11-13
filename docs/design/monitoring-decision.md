# Why TempSafe retired the device heartbeat

On 13 November 2026 the team chose to monitor the age and quality of temperature observations. A separate heartbeat would add a second message schedule, configuration and timeout to maintain. The paramedic needs to know when the box last measured the temperature and whether that measurement succeeded.

The Pi normally records a sample about every 30 seconds. A sensor read exception produces a timestamped sensor error with an empty temperature. Both kinds of record enter the same SQLite queue for delivery through MQTT. If the sensor keeps reporting that data is not ready, the logger retries and may produce no record.

The dashboard uses the original observation time. A reliable timestamp up to 90 seconds old is fresh. An older timestamp is stale, and an unreliable timestamp gives unknown freshness. A sensor error remains visible. Before any samples arrive, the dashboard shows that there are no readings yet.

When uploads resume, buffered observations fill the history at their original times. Silence alone cannot tell the user whether the Pi lost power, the network failed or sampling stopped.

FR-08 retains the requirement to flag a possible loss of device contact. The design uses the latest server receipt time
(`received_at`) for the box. After the first record, more than 90 seconds without a new record triggers the warning.
Receiving a new record, including a sensor error or a buffered sample, clears it. A buffered sample can therefore
restore contact while the temperature is still stale. The backend exposes both states through the assigned box status
endpoint. The current dashboard already checks observation freshness.
