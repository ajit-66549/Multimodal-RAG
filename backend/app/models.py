from uuid import uuid4

from sqlalchemy import String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone

from app.database import Base

class Documents(Base):
    __tablename__="documents"
    
    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )
    filename: Mapped[str] = mapped_column(String)
    file_type: Mapped[str] = mapped_column(String)
    storage_path: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="uploaded")
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
class DocumentChunk(Base):
    __tablename__="document_chunks"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    document_id: Mapped[str] = mapped_column(String, ForeignKey("documents.id"))
    page_number: Mapped[int] = mapped_column(Integer)
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer)
    
    document = relationship("Documents")
    
class DocumentAsset(Base):
    __tablename__ = "document_assets"
        
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    document_id: Mapped[str] = mapped_column(String, ForeignKey("documents.id"), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    asset_type: Mapped[str] = mapped_column(String, nullable=False)
    asset_path: Mapped[str] = mapped_column(String, nullable=False)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
        
    document = relationship("Documents")