from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EducationAreaOut(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True 