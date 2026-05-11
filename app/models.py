from sqlalchemy import create_engine, Column, Text, Float, ARRAY, TIMESTAMP
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
Base = declarative_base()

class MonitoredUrl(Base):
    __tablename__ = "monitored_urls"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url         = Column(Text, nullable=False)
    webhook_url = Column(Text, nullable=False)
    zones_filter = Column(ARRAY(Text), nullable=True)
    created_at  = Column(TIMESTAMP(timezone=True), server_default=func.now())

class ZoneSnapshot(Base):
    __tablename__ = "zone_snapshots"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url         = Column(Text, nullable=False)
    zone_name   = Column(Text, nullable=False)
    crawled_at  = Column(TIMESTAMP(timezone=True), server_default=func.now())
    chunk_text  = Column(Text, nullable=True)
    embedding   = Column(Vector(384), nullable=True)
    sim_score   = Column(Float, nullable=True)
    sprt_state  = Column(Text, nullable=True)
    log_sum     = Column(Float, nullable=True)

def init_db():
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    init_db()
    print("Tables created successfully")