<<<<<<< HEAD
# 💰 Smart Finance Manager

A full-stack Python solution that fetches, parses, and visualizes invoice data from your Gmail inbox to help you manage and monitor your daily spending. Built with Django + FastAPI, this project combines automation, analytics, and clean UI to deliver a smart financial dashboard.

---

## ✨ Features

- 🔐 **User Authentication** with Django login system
- 📊 **Dashboard View** with:
  - Budget limit display and spend alerts
  - Daily and platform-wise spend charts
  - Smart insights and summaries
- 📥 **Gmail Invoice Parsing** using IMAP:
  - Detects PDF invoices from platforms like Swiggy, Zomato, Amazon, Flipkart
  - Extracts platform name and amount from attachment content
- ⚙️ **FastAPI Microservice**:
  - Parses PDFs and handles invoice data endpoints
  - In-memory storage (PostgreSQL planned)
- 🧾 **Downloadable Reports**:
  - Generate monthly PDF reports using WeasyPrint
- 📈 **Smart Spend Charts**:
  - Auto-filled 7-day trend graphs via Chart.js
- 📬 **Budget Alerts**:
  - UI warnings when spending crosses thresholds
- 🎨 **Clean UI** with Bootstrap 5 and form feedback

---

## 🔧 Tech Stack

| Layer        | Technology                                |
|--------------|--------------------------------------------|
| Backend      | Django, FastAPI                            |
| Frontend     | Django Templates, Bootstrap 5, Chart.js    |
| Email Parser | IMAP, PDFMiner, Regex                      |
| Reporting    | WeasyPrint (PDF generation)                |
| Storage      | In-memory (PostgreSQL planned)             |
| Auth         | Django Auth (OAuth 2.0 planned)            |
| Testing      | PyTest, Selenium                           |

---

## 📂 Project Structure

smart_finance_manager/
├── django_app/ # Dashboard + auth + insights
├── fastapi_parser/ # Invoice parsing engine
├── gmail_invoice_django/ # Email handler (IMAP)
├── imap_reader/ # Helper for raw inbox reads
├── scripts/ # Data and test utilities
├── db/, logs/, tmp/ # Runtime and cache folders
├── README.md, .gitignore, requirements.txt, etc.





=======
>>>>>>> 22f88b9 (WIP: Save local changes before pull --rebase)
