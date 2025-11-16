"""
Módulo de OCR do ACE.

Responsável por combinar:
- texto da camada de texto do PDF (pdfplumber, via layout.extract_text_from_pdf)
- OCR com Tesseract (via pdf2image + pytesseract)

Externa:
- extract_text_with_ocr(path, mode, min_chars_for_text_layer, max_pages)

Configuração:
- ACE_TESSERACT_CMD: caminho do executável do Tesseract
- ACE_POPPLER_PATH: pasta "bin" do Poppler (Windows)
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional

import pdf2image
import pytesseract

from .layout import PageText, extract_text_from_pdf


class OcrMode(Enum):
    """Modo de uso do OCR."""

    REQUIRED = "REQUIRED"  # sempre usa OCR
    FALLBACK = "FALLBACK"  # tenta texto do PDF, cai pro OCR se precisar


@dataclass
class OcrExtractionResult:
    """Resultado da extração com ou sem OCR."""

    pages: List[PageText]
    provider: str          # "PDFPLUMBER" ou "TESSERACT"
    used_ocr: bool
    mode: OcrMode


# ========= Configuração (sem hardcoded de usuário) =========

# Caminho padrão do executável do Tesseract (Windows). Pode ser sobrescrito.
DEFAULT_TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Poppler não tem um path padrão confiável; forçamos configuração via env.
DEFAULT_POPPLER_PATH: Optional[str] = None

# Variáveis de ambiente
TESSERACT_CMD = os.getenv("ACE_TESSERACT_CMD", DEFAULT_TESSERACT_CMD)
POPPLER_PATH = os.getenv("ACE_POPPLER_PATH", DEFAULT_POPPLER_PATH)

# Configura pytesseract se tivermos um comando definido
if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def ensure_ocr_dependencies() -> None:
    """
    Verifica se Tesseract e Poppler estão configurados corretamente.

    Levanta RuntimeError com mensagem amigável se algo estiver faltando.
    """
    # --- Tesseract ---
    if not TESSERACT_CMD:
        raise RuntimeError(
            "Tesseract não configurado. Defina ACE_TESSERACT_CMD com o caminho do "
            "executável do Tesseract (ex: C:\\Program Files\\Tesseract-OCR\\tesseract.exe)."
        )

    exe_path = Path(TESSERACT_CMD)
    found = False
    if exe_path.is_file():
        found = True
    elif shutil.which(TESSERACT_CMD) is not None:
        found = True

    if not found:
        raise RuntimeError(
            f"Tesseract não encontrado em '{TESSERACT_CMD}'. "
            "Ajuste ACE_TESSERACT_CMD ou instale corretamente o Tesseract."
        )

    # --- Poppler ---
    if POPPLER_PATH is None:
        raise RuntimeError(
            "Poppler não configurado. Defina ACE_POPPLER_PATH com a pasta 'bin' do Poppler "
            "(ex: C:\\tools\\poppler\\Library\\bin)."
        )

    poppler_dir = Path(POPPLER_PATH)
    if not poppler_dir.exists():
        raise RuntimeError(
            f"Pasta do Poppler não encontrada em '{POPPLER_PATH}'. "
            "Verifique ACE_POPPLER_PATH."
        )


def _run_ocr(path: str, max_pages: Optional[int] = None) -> List[PageText]:
    """
    Roda OCR com Tesseract para até max_pages do PDF.

    Retorna lista de PageText.
    """
    ensure_ocr_dependencies()

    images = pdf2image.convert_from_path(
        path,
        poppler_path=POPPLER_PATH,
        first_page=1,
        last_page=max_pages if max_pages is not None else None,
    )

    pages: List[PageText] = []
    for idx, img in enumerate(images):
        text = pytesseract.image_to_string(img)
        lines = text.splitlines()
        pages.append(
            PageText(
                page_number=idx + 1,
                text=text,
                lines=lines,
            )
        )
    return pages


def extract_text_with_ocr(
    path: str,
    mode: OcrMode = OcrMode.REQUIRED,
    min_chars_for_text_layer: int = 50,
    max_pages: Optional[int] = None,
) -> OcrExtractionResult:
    """
    Extrai texto de um PDF combinando camada de texto e OCR.

    - mode=REQUIRED: sempre roda OCR e usa o resultado do Tesseract.
    - mode=FALLBACK: tenta usar apenas pdfplumber; se pouco texto, cai para OCR.

    max_pages limita o número de páginas processadas por OCR (útil para PDFs
    grandes onde o ACORD 25 está no começo).
    """
    # 1) Tenta camada de texto (pdfplumber) primeiro
    baseline_pages = extract_text_from_pdf(path)
    baseline_chars = sum(len(p.text or "") for p in baseline_pages)

    # Se o modo for FALLBACK e a camada de texto já for suficiente, usamos ela.
    if mode == OcrMode.FALLBACK and baseline_chars >= min_chars_for_text_layer:
        return OcrExtractionResult(
            pages=baseline_pages,
            provider="PDFPLUMBER",
            used_ocr=False,
            mode=mode,
        )

    # 2) Caso contrário, rodamos OCR obrigatório
    ocr_pages = _run_ocr(path, max_pages=max_pages)

    return OcrExtractionResult(
        pages=ocr_pages,
        provider="TESSERACT",
        used_ocr=True,
        mode=mode,
    )
