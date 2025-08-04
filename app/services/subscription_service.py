import structlog
from typing import Optional, Dict, Any
from app.schemas.subscription import CustomerCreate

logger = structlog.get_logger(__name__)

class SubscriptionService:
    """Basic subscription service for development - mocks subscription operations"""
    
    def __init__(self, db):
        self.db = db
        self.logger = logger
    
    async def get_customer(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get customer by user ID (mocked)"""
        self.logger.info(f"Getting customer for user_id: {user_id}")
        # Mock - return None to simulate customer not found
        return None
    
    async def create_customer(self, customer_data: CustomerCreate) -> Dict[str, Any]:
        """Create a new customer (mocked)"""
        self.logger.info(f"Creating customer: {customer_data}")
        # Mock successful customer creation
        return {
            "success": True,
            "customer_id": f"cust_{customer_data.external_user_id}",
            "external_user_id": customer_data.external_user_id,
            "email": customer_data.email
        } 