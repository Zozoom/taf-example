from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.db import Base


class TestRun(Base):
    __tablename__ = "test_runs"

    id = Column(Integer, primary_key=True)
    env = Column(String, nullable=False)
    test_type = Column(String, nullable=False)
    status = Column(String, nullable=False)  # scheduled, running, finished, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    scheduled_for = Column(DateTime, nullable=True)
    run_folder = Column(String, nullable=True)
    target_url = Column(String, nullable=True)
    finished_at = Column(DateTime, nullable=True)
