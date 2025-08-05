from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class UserType(str, enum.Enum):
    ADMIN = "ADMIN"
    TEACHER = "TEACHER"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    user_type = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    is_oauth_user = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=True)
    country = relationship("Country", backref="users")

    classes = relationship("Class", back_populates="author") 