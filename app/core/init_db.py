from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal
from app.core.security import get_password_hash
import structlog
import os

logger = structlog.get_logger(__name__)

def init_db():
    """Initialize the database with tables and sample data"""
    # Import all models to ensure they are registered
    from app.models.user import User, UserType
    from app.models.country import Country
    from app.models.verification_token import VerificationToken
    from app.models.class_model import Class
    
    # Create all tables
    from app.core.database import Base
    Base.metadata.create_all(bind=engine)
    
    # Create sample data
    db = SessionLocal()
    try:
        # Check if we already have data
        if db.query(User).first():
            logger.info("Database already has data, skipping initialization")
            return
        
        # Create sample countries
        countries = [
            Country(name="United States", code="USA"),
            Country(name="Mexico", code="MEX"),
            Country(name="Spain", code="ESP"),
            Country(name="Argentina", code="ARG"),
        ]
        
        for country in countries:
            db.add(country)
        db.commit()
        
        # Create sample admin user
        admin_password = os.getenv("ADMIN_PASSWORD", "ChangeMe123!")
        admin_user = User(
            email="admin@example.com",
            password_hash=get_password_hash(admin_password),
            first_name="Admin",
            last_name="User",
            user_type=UserType.ADMIN,
            is_active=True,
            is_oauth_user=False
        )
        db.add(admin_user)
        db.commit()
        
        logger.info("Database initialized with sample data")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_db() 