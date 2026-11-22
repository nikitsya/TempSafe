from sqlalchemy import CheckConstraint, Column, Integer, REAL, Text, text

from database import Base


class Reading(Base):
    __tablename__ = "readings"
    __table_args__ = (
        CheckConstraint("sensor_location IN ('inside', 'outside')"),
        {"sqlite_autoincrement": True},
    )

    sequence_no = Column(Integer, primary_key=True, autoincrement=True)
    sensor_location = Column(Text, nullable=False, default="inside", server_default="inside")
    sample_id = Column(Text, nullable=False, unique=True)
    observed_at = Column(Text)
    temperature_c = Column(REAL)
    quality = Column(Text, nullable=False)
    clock_reliable = Column(Integer, nullable=False)
    box_id = Column(Text, nullable=False)
    profile_id = Column(Text, nullable=False)
    uploaded = Column(Integer, nullable=False, server_default=text("0"))


class DeviceConfiguration(Base):
    """Keep the latest valid threshold profile available to the device."""

    __tablename__ = "device_configuration"

    box_id = Column(Text, primary_key=True)
    profile_id = Column(Text, nullable=False)
    lower_c = Column(REAL, nullable=False)
    warning_c = Column(REAL, nullable=False)
    upper_c = Column(REAL, nullable=False)
