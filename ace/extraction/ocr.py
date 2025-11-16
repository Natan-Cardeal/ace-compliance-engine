from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List

from .layout import PageText, extract_text_from_pdf


class OcrMode(str, Enum):
    REQUIRED = "REQUIRED"   # sempre roda OCR
    FALLBACK = "FALLBACK"   # só roda OCR se pdfplumber não achar texto suficiente


@dataclass
class OcrExtractionResult:
    pages: List[PageText]
    provider: str            # "TESSERACT" ou "PDFPLUMBER"
    used_ocr: bool
    mode: OcrMode


# 👇 Caminho da pasta onde fica o `pdftoppm.exe` (Poppler).
# Use SEMPRE a pasta que termina em `\bin`, NÃO o executável.
POPPLER_PATH = r"C:\Users\Natan\Downloads\Release-25.11.0-0\poppler-25.11.0\Library\bin"

# 👇 Caminho do `tesseract.exe`. Ajuste se estiver em outro lugar.
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def _run_tesseract_ocr(pdf_path: Path) -> List[PageText]:
    """
    Converte o PDF em imagens (usando Poppler) e roda OCR com Tesseract
    página a página. Retorna uma lista de PageText.
    """
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError as e:
        raise RuntimeError(
            "Dependências de OCR não instaladas. Rode dentro do venv:\n"
            "  pip install pytesseract pdf2image pillow"
        ) from e

    # Configurar caminho do Tesseract explicitamente
    if TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

    if not POPPLER_PATH:
        raise RuntimeError(
            "POPPLER_PATH não configurado em ace.extraction.ocr. "
            "Ajuste a constante POPPLER_PATH para a pasta que contém pdftoppm.exe."
        )

    pages: List[PageText] = []

    # converte cada página do PDF em imagem PIL (usa Poppler via pdf2image)
    images = convert_from_path(
        str(pdf_path),
        poppler_path=POPPLER_PATH,
    )

    for idx, img in enumerate(images, start=1):
        text = pytesseract.image_to_string(img)
        lines = text.splitlines()
        pages.append(PageText(page_number=idx, text=text, lines=lines))

    return pages


def extract_text_with_ocr(
    path: str,
    mode: OcrMode = OcrMode.REQUIRED,
    min_chars_for_text_layer: int = 50,
) -> OcrExtractionResult:
    """
    Extrai texto do PDF garantindo OCR conforme o modo:

      - REQUIRED:
          - ignora o que vier do pdfplumber e sempre usa OCR (Tesseract).
      - FALLBACK:
          - usa pdfplumber se já houver "texto suficiente" (>= min_chars_for_text_layer);
          - se não houver, roda OCR e usa a saída do Tesseract.

    Retorna OcrExtractionResult com:
      - pages    -> lista de PageText
      - provider -> "PDFPLUMBER" ou "TESSERACT"
      - used_ocr -> bool
      - mode     -> modo usado (REQUIRED/FALLBACK)
    """
    pdf_path = Path(path).resolve()

    # 1) baseline: camada de texto normal com pdfplumber
    baseline_pages = extract_text_from_pdf(str(pdf_path))
    total_chars = sum(len(p.text.strip()) for p in baseline_pages)
    has_text_layer = total_chars >= min_chars_for_text_layer

    # Modo FALLBACK: se o PDF já tem texto razoável, usamos pdfplumber
    if mode == OcrMode.FALLBACK and has_text_layer:
        return OcrExtractionResult(
            pages=baseline_pages,
            provider="PDFPLUMBER",
            used_ocr=False,
            mode=mode,
        )

    # 2) REQUIRED ou FALLBACK sem texto -> rodar OCR com Tesseract
    ocr_pages = _run_tesseract_ocr(pdf_path)

    return OcrExtractionResult(
        pages=ocr_pages,
        provider="TESSERACT",
        used_ocr=True,
        mode=mode,
    )
