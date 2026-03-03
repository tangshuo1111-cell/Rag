from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db import Base


class Document(Base):
    __tablename__  = "documents"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(255), index=True, nullable=False)
    name = Column(String(512), nullable=False)
    source_type = Column(String(50), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    tenant_id = Column(String(255), index=True, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    document = relationship("Document", back_populates="chunks")


class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(255), index=True, nullable=False)
    tenant_id = Column(String(255), index=True, nullable=False)
    question = Column(Text, nullable=False)
    topk_chunks_json = Column(Text, nullable=False, default="[]")
    citations_json = Column(Text, nullable=False, default="[]")
    answer_json = Column(Text, nullable=False, default="{}")
    refused = Column(Boolean, nullable=False, default=False)
    reason = Column(Text, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


all = ["Document", "Chunk", "QueryLog"]