from sqlalchemy import Column, Integer, String
from app.core.database import Base

class Country(Base):
    __tablename__ = "countries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    code = Column(String(3), nullable=False, unique=True) 