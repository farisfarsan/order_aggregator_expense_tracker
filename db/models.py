# db/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    platform = Column(String)
    amount = Column(Float)
    date_fetched = Column(DateTime, default=datetime.utcnow)
