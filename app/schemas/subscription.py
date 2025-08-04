from pydantic import BaseModel
from typing import Optional

class CustomerCreate(BaseModel):
    external_user_id: str
    email: str 