from .minirag_base import SQLAlchemyBase
from sqlalchemy import Column, ForeignKey, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship


class Project(SQLAlchemyBase):
    __tablename__ = "projects"

    project_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'), nullable=False)  # Foreign key to users table
    user = relationship("User", back_populates="projects")  #  Optional: add backref if needed


    chunks = relationship("DataChunk", back_populates="project")
    assets = relationship("Asset", back_populates="project")

