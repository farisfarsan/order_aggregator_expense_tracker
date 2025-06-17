from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from datetime import datetime

app = FastAPI()

# In-memory storage
invoices_db = []

# Schema definition
class Invoice(BaseModel):
    user_id: int
    platform: str
    amount: float
    date_fetched: str  # Expected in ISO format (yyyy-mm-dd)

# POST: Add a new invoice
@app.post("/invoices/")
async def receive_invoice(invoice: Invoice):
    try:
        # Validate date
        datetime.fromisoformat(invoice.date_fetched)
    except ValueError:
        return {"status": "failed", "reason": "Invalid date format"}

    invoices_db.append(invoice)
    print(f"✅ Received invoice: {invoice.platform} | ₹{invoice.amount} | {invoice.date_fetched}")
    return {"status": "success"}

# GET: Fetch all invoices for a given user_id, sorted by date
@app.get("/invoices/{user_id}", response_model=List[Invoice])
async def get_invoices(user_id: int):
    user_invoices = [inv for inv in invoices_db if inv.user_id == user_id]
    user_invoices.sort(key=lambda x: x.date_fetched)  # sort by date
    return user_invoices

# DELETE: Remove all invoices for a given user_id
@app.delete("/invoices/{user_id}/clear")
async def clear_user_invoices(user_id: int):
    global invoices_db
    before = len(invoices_db)
    invoices_db = [inv for inv in invoices_db if inv.user_id != user_id]
    removed = before - len(invoices_db)
    print(f"🧹 Cleared {removed} invoice(s) for user_id {user_id}")
    return {"status": "cleared", "removed": removed}
