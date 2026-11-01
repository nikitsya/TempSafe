from sqlalchemy import Column, Integer, REAL, Text, text

from database import Base


class Reading(Base):
    __tablename__ = "readings"
    __table_args__ = {"sqlite_autoincrement": True}

    sequence_no = Column(Integer, primary_key=True, autoincrement=True)
    sample_id = Column(Text, nullable=False, unique=True)
    observed_at = Column(Text)
    temperature_c = Column(REAL)
    quality = Column(Text, nullable=False)
    clock_reliable = Column(Integer, nullable=False)
    box_id = Column(Text, nullable=False)
    profile_id = Column(Text, nullable=False)
    uploaded = Column(Integer, nullable=False, server_default=text("0"))
