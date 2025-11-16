from dataclasses import dataclass
from typing import List


@dataclass
class PageText:
    page_number: int
    text: str
    lines: List[str]


def extract_text_from_pdf(path: str) -> List[PageText]:
    """
    Extrai texto por página de um PDF usando pdfplumber.
    Retorna uma lista de PageText com texto bruto e linhas.
    """
    try:
        import pdfplumber
    except ImportError as e:
        raise RuntimeError(
            "pdfplumber não está instalado. Rode: pip install pdfplumber"
        ) from e

    pages: List[PageText] = []

    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            lines = text.splitlines()
            pages.append(PageText(page_number=i, text=text, lines=lines))

    return pages
