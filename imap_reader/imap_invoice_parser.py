import imaplib
import email
from email.header import decode_header
import re
from bs4 import BeautifulSoup

# ===== CONFIG =====
IMAP_HOST = "imap.zoho.com"  # e.g. Zoho IMAP server
EMAIL_USER = "invoices@yourdomain.com"
EMAIL_PASS = "your_app_password"  # Generate app-specific password if needed

# ===== CONNECT =====
mail = imaplib.IMAP4_SSL(IMAP_HOST)
mail.login(EMAIL_USER, EMAIL_PASS)
mail.select("inbox")  # or "INBOX"

# ===== SEARCH NEW INVOICES =====
status, messages = mail.search(None, '(UNSEEN)')
email_ids = messages[0].split()

for eid in email_ids:
    status, msg_data = mail.fetch(eid, '(RFC822)')
    msg = email.message_from_bytes(msg_data[0][1])

    subject, encoding = decode_header(msg["Subject"])[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding or 'utf-8')

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                html = part.get_payload(decode=True).decode()
                soup = BeautifulSoup(html, "html.parser")

                # === EXTRACT PLATFORM & AMOUNT (example logic) ===
                if "Swiggy" in subject:
                    platform = "Swiggy"
                    amount = re.search(r'₹(\d+[\.,]?\d*)', soup.text)
                    print(f"✅ Swiggy: ₹{amount.group(1) if amount else 'N/A'}")

    # Mark email as read
    mail.store(eid, '+FLAGS', '\\Seen')

mail.logout()
