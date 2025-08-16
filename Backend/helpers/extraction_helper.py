import mimetypes
import pymupdf as fitz
from docx import Document as Docx
import pandas as pd
from pathlib import Path

ALLOWED_EXTS = {".pdf", ".docx", ".txt", ".csv"}

def detect_mime(path: str) -> str:
    mt, _ = mimetypes.guess_type(path)
    return mt or "application/octet-stream"

def extract_pdf(path: Path) -> str:
    doc = fitz.open(path)
    all_text = []
    for page in doc:
        text = page.get_text("text") or ""
        if text.strip():
            all_text.append(text)
    return "\n".join(all_text)

def extract_docx(path: Path) -> str:
    d = Docx(path)
    paras = [p.text for p in d.paragraphs if p.text.strip()]
    return "\n".join(paras)

def extract_txt(path: Path) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def extract_csv(path: Path) -> str:
    df = pd.read_csv(path)
    lines = ["\t".join(map(str, df.columns.tolist()))]
    for _, row in df.iterrows():
        lines.append("\t".join(map(lambda x: "" if pd.isna(x) else str(x), row.tolist())))
    return "\n".join(lines)

def run_extractor(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return extract_pdf(path)
    elif ext == ".docx":
        return extract_docx(path)
    elif ext == ".txt":
        return extract_txt(path)
    elif ext == ".csv":
        return extract_csv(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
