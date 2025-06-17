from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import imaplib
import email
import os
import re
import fitz  # PyMuPDF
from datetime import datetime, timedelta
from email.header import decode_header
from dateutil import parser as date_parser
import requests

# ===== CONFIG =====
FASTAPI_ENDPOINT = "http://127.0.0.1:8005/invoices/"
TMP_DIR = "./tmp/invoice_pdfs"
os.makedirs(TMP_DIR, exist_ok=True)

# ===== IN-MEMORY STORE =====
INVOICES_DB = {}

# ===== LOGGING =====
def log(msg):
    LOG_FILE = f"invoice_log_{datetime.now().date()}.log"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

# ===== EMAIL UTIL =====
def get_email_date(msg):
    try:
        raw_date = msg.get("Date")
        dt = date_parser.parse(raw_date)
        if dt.tzinfo is not None:
            dt = dt.astimezone(tz=None).replace(tzinfo=None)
        return dt
    except Exception as e:
        log(f"⚠️ Date parse issue, skipping email: {e}")
        return None

def extract_text_from_pdf(pdf_bytes):
    try:
        tmp_path = os.path.join(TMP_DIR, f"invoice_{datetime.now().timestamp()}.pdf")
        with open(tmp_path, "wb") as f:
            f.write(pdf_bytes)

        try:
            doc = fitz.open(tmp_path)
        except Exception as e:
            log(f"❌ Failed to open PDF ({os.path.basename(tmp_path)}): {e}")
            return "", None

        if doc.is_encrypted:
            log(f"🔐 Skipped encrypted PDF: {os.path.basename(tmp_path)}")
            return "", None

        text = "".join([page.get_text() for page in doc])
        doc.close()
        os.remove(tmp_path)

        platform = get_platform_from_text(text)
        return text, platform
    except Exception as e:
        log(f"❌ PDF parse error (outer): {e}")
        return "", None

def extract_amount(text):
    patterns = [
        r"₹\s?(\d[\d,]*\.?\d*)",
        r"Rs\.?\s?(\d[\d,]*\.?\d*)",
        r"INR\s?(\d[\d,]*\.?\d*)",
        r"Invoice Total\s+(\d+\.\d{2})",
        r"Total Amount\s+(\d+\.\d{2})"
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for amt in matches:
            try:
                val = float(amt.replace(",", ""))
                if val > 10:
                    return val
            except:
                continue
    return None

def get_platform_from_text(text):
    lowered = text.lower()
    if "swiggy" in lowered:
        return "Swiggy"
    elif "zomato" in lowered:
        return "Zomato"
    elif "zepto" in lowered:
        return "Zepto"
    elif "amazon" in lowered:
        return "Amazon"
    return None

# ===== MAIN FUNCTION =====
def fetch_invoices_from_all_pdfs(email_user, email_pass, user_id):
    log(f"\n[📩] Received fetch request for user_id {user_id}")
    log(f"🔐 Connecting to Gmail for user {email_user}...")
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_user, email_pass)
        log("✅ Login successful.")
    except Exception as e:
        log(f"❌ IMAP login failed: {e}")
        return

    status, _ = mail.select("inbox")
    if status != "OK":
        log("❌ Failed to select inbox.")
        return
    log("📂 Inbox selected successfully.")

    try:
        log(f"🧹 Clearing previous invoices for user {user_id} via DELETE request...")
        res = requests.delete(f"{FASTAPI_ENDPOINT}{user_id}/clear")
        if res.status_code == 200:
            log("🗑️ Cleared old invoices.")
        else:
            log(f"⚠️ Failed to clear invoices. Status code: {res.status_code}")
    except Exception as e:
        log(f"❌ Error clearing old invoices: {e}")

    status, messages = mail.search(None, "ALL")
    email_ids = messages[0].split()[::-1]

    now = datetime.utcnow()
    first_day_this_month = now.replace(day=1)
    first_day_last_month = (first_day_this_month - timedelta(days=1)).replace(day=1)
    cutoff_start = first_day_last_month
    cutoff_end = now

    pushed_count = 0
    MAX_PUSH = 5

    for eid in email_ids:
        if pushed_count >= MAX_PUSH:
            break

        _, msg_data = mail.fetch(eid, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        dt = get_email_date(msg)
        if not dt or not (cutoff_start <= dt <= cutoff_end):
            continue

        for part in msg.walk():
            content_dispo = part.get("Content-Disposition", "")
            if part.get_content_type() == "application/pdf" and "attachment" in content_dispo:
                pdf = part.get_payload(decode=True)
                text, platform = extract_text_from_pdf(pdf)
                if not text.strip() or not platform:
                    log("⚠️ Skipped: Not from known platforms or empty text")
                    continue

                amount = extract_amount(text)
                if amount:
                    payload = {
                        "user_id": user_id,
                        "platform": platform,
                        "amount": amount,
                        "date_fetched": dt.date().isoformat()
                    }
                    log(f"📤 Sending to FastAPI: {payload}")
                    try:
                        store_invoice(Invoice(**payload))
                        pushed_count += 1
                        log(f"✅ Pushed invoice: ₹{amount}")
                    except Exception as e:
                        log(f"❌ API error: {e}")

    mail.logout()
    log(f"✅ Invoice fetching complete. Pushed {pushed_count} invoices to FastAPI.")

# ===== FASTAPI CONFIG =====

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FetchRequest(BaseModel):
    email_user: str
    email_pass: str
    user_id: int

class Invoice(BaseModel):
    user_id: int
    platform: str
    amount: float
    date_fetched: str

@app.post("/fetch_invoices/")
def fetch_invoices(req: FetchRequest):
    try:
        fetch_invoices_from_all_pdfs(req.email_user, req.email_pass, req.user_id)
        return {"status": "success"}
    except Exception as e:
        log(f"❌ Error in fetch endpoint: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/invoices/")
def store_invoice(invoice: Invoice):
    INVOICES_DB.setdefault(invoice.user_id, []).append(invoice.dict())
    return {"message": "Invoice stored"}

@app.get("/invoices/{user_id}")
def get_invoices(user_id: int):
    return INVOICES_DB.get(user_id, [])

@app.delete("/invoices/{user_id}/clear")
def clear_invoices(user_id: int):
    INVOICES_DB[user_id] = []
    return {"message": f"Cleared invoices for user {user_id}"}
