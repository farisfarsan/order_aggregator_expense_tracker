from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from db.database import get_db, engine
from db.models import Invoice, Base
from pydantic import BaseModel
from datetime import datetime

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "FastAPI is running"}

# ✅ Pydantic model updated with user_id
class InvoiceCreate(BaseModel):
    user_id: int
    platform: str
    amount: float
    date_fetched: datetime  # Ensure frontend sends ISO 8601 datetime string

# ✅ Get invoices for a specific user
@app.get("/invoices/{user_id}")
def get_invoices(user_id: int, db: Session = Depends(get_db)):
    return db.query(Invoice).filter(Invoice.user_id == user_id).all()

# ✅ Create a new invoice
@app.post("/invoices/")
def create_invoice(invoice: InvoiceCreate, db: Session = Depends(get_db)):
    db_invoice = Invoice(**invoice.dict())
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    return db_invoice
