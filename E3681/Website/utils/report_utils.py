import pdfplumber
from docx import Document
import re

def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text.strip()

def extract_text_from_docx(file_path):
    doc = Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text.strip()

def classify_report_text(text: str) -> dict:
    data = {}

    match = re.search(r"amniotic fluid[^:\d]*[:\-]?\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if match:
        data["amniotic_fluid"] = float(match.group(1))

    match = re.search(r"gestational age[^:\d]*[:\-]?\s*(\d+)", text, re.IGNORECASE)
    if match:
        data["gestational_age"] = int(match.group(1))

    match = re.search(r"placenta[^:\n]*[:\-]?\s*([A-Za-z]+)", text, re.IGNORECASE)
    if match:
        data["placenta_position"] = match.group(1)

    return data
