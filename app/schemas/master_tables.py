from pydantic import BaseModel
from typing import Optional

class Country(BaseModel):
    id: int
    name: str
    code: str
    
    class Config:
        from_attributes = True 