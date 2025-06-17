import fitz  # PyMuPDF

def extract_data_from_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    # Use regex or patterns here to extract platform, date, amount
    return {"platform": "Zomato", "amount": 420.5, "order_date": "2024-06-01"}
