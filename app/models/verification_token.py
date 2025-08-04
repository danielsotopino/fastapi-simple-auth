from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
import uuid # For default token generation if needed, or use another strategy
from sqlalchemy.dialects.postgresql import UUID # If using UUID for token

class VerificationToken(Base):
    __tablename__ = "verification_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True) # Or UUID(as_uuid=True), default=uuid.uuid4
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    purpose = Column(String(50), nullable=False, index=True, default="account_activation")  # Ej: 'account_activation', 'password_reset'
    # updated_at is not strictly necessary for a token that is used once
