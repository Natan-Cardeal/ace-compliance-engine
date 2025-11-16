import os
from pathlib import Path
import sqlite3

from ace.extraction.layout import extract_text_from_pdf
from ace.extraction.ocr import extract_text_with_ocr, OcrMode

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "ace.sqlite"
DOCS_DIR = ROOT / "db" / "docs"
DEBUG_DIR = ROOT / "db" / "ocr_debug"


def get_certificate_path(cert_id: int) -> Path:
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(
            "SELECT storage_path FROM certificates WHERE id = ?", (cert_id,)
        )
        row = cur.fetchone()
        if not row or not row[0]:
            raise RuntimeError(f"Nenhum storage_path encontrado para certificate {cert_id}")
        return ROOT / row[0]
    finally:
        conn.close()


def run(cert_id: int):
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = get_certificate_path(cert_id)
    if not pdf_path.exists():
        raise SystemExit(f"Arquivo PDF não encontrado: {pdf_path}")

    print(f"Usando PDF: {pdf_path}")

    # 1) Camada de texto (pdfplumber)
    pages_text = extract_text_from_pdf(str(pdf_path))
    text_debug = []
    for p in pages_text:
        text_debug.append(f"=== PAGE {p.page_number} (TEXT LAYER) ===\n")
        text_debug.append(p.text or "")
        text_debug.append("\n\n")

    # 2) OCR obrigatório (Tesseract)
    ocr_result = extract_text_with_ocr(str(pdf_path), mode=OcrMode.REQUIRED, max_pages=None)
    for p in ocr_result.pages:
        text_debug.append(f"=== PAGE {p.page_number} (OCR TESSERACT) ===\n")
        text_debug.append(p.text or "")
        text_debug.append("\n\n")

    out_path = DEBUG_DIR / f"certificate_{cert_id}_ocr_dump.txt"
    out_path.write_text("".join(text_debug), encoding="utf-8")
    print(f"Dump salvo em: {out_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Uso: py scripts\\dump_ocr_text_for_cert.py <certificate_id>")
        raise SystemExit(1)
    run(int(sys.argv[1]))
