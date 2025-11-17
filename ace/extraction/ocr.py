"""
OCR Inteligente - Com cache e detecção híbrida
"""

from ace.setup import TESSERACT_PATH
from ace.extraction.cache import get_cached_text, save_to_cache
from ace.utils.logger import get_logger
from ace.utils.exceptions import OCRException

logger = get_logger('ace.extraction.ocr')


def _detect_text_density(pdf_path: str) -> float:
    """
    Detecta densidade de texto nativo no PDF
    
    Returns:
        Razão de texto nativo (0.0 = só imagem, 1.0 = só texto)
    """
    import pdfplumber
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_chars = 0
            total_pages = len(pdf.pages)
            
            for page in pdf.pages[:min(3, total_pages)]:  # Sample 3 páginas
                text = page.extract_text() or ""
                total_chars += len(text.strip())
            
            # Média de caracteres por página
            avg_chars = total_chars / min(3, total_pages)
            
            # Se > 100 chars/página, provavelmente tem texto nativo
            density = min(1.0, avg_chars / 500)  # Normalizar para 0-1
            
            logger.debug(f"Densidade de texto: {density:.2f} ({avg_chars:.0f} chars/página)")
            
            return density
            
    except Exception as e:
        logger.warning(f"Erro ao detectar densidade: {e}")
        return 0.0  # Assumir que é imagem


def extract_text_from_pdf(pdf_path: str, force_ocr: bool = True) -> str:
    """
    Extrai texto de PDF com estratégia inteligente
    
    Args:
        pdf_path: Caminho do PDF
        force_ocr: Se True, sempre usa OCR (garantia de 100%)
                   Se False, usa híbrido inteligente
    
    Returns:
        Texto extraído
    """
    # 1. Verificar cache primeiro
    cached_text = get_cached_text(pdf_path)
    if cached_text:
        return cached_text
    
    # 2. Decidir estratégia
    if force_ocr:
        text = _extract_via_ocr(pdf_path)
    else:
        # Híbrido inteligente
        density = _detect_text_density(pdf_path)
        
        if density > 0.3:  # Tem texto nativo significativo
            logger.info(f"Usando extração híbrida (densidade: {density:.2f})")
            text = _extract_hybrid(pdf_path)
        else:
            logger.info(f"Usando OCR completo (densidade: {density:.2f})")
            text = _extract_via_ocr(pdf_path)
    
    # 3. Salvar em cache
    save_to_cache(pdf_path, text)
    
    return text


def _extract_via_ocr(pdf_path: str) -> str:
    """Extração via OCR completo (100% coverage)"""
    import pytesseract
    import pdfplumber
    
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    
    logger.debug(f"Extraindo via OCR (100% coverage): {pdf_path}")
    
    try:
        all_text = []
        
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            logger.info(f"PDF tem {total_pages} páginas - processando via OCR...")
            
            for i, page in enumerate(pdf.pages, 1):
                try:
                    img = page.to_image(resolution=300)
                    pil_img = img.original
                    text = pytesseract.image_to_string(pil_img, lang='eng')
                    
                    if text.strip():
                        all_text.append(text)
                        logger.debug(f"Página {i}/{total_pages}: {len(text)} caracteres")
                
                except Exception as e:
                    logger.error(f"Erro página {i}: {e}")
                    continue
        
        if not all_text:
            raise OCRException("Nenhum texto extraído")
        
        full_text = "\n\n".join(all_text)
        logger.info(f"OCR concluído: {len(full_text)} caracteres de {total_pages} páginas")
        
        return full_text
        
    except Exception as e:
        logger.error(f"Erro no OCR: {e}", exc_info=True)
        raise OCRException(f"Erro no OCR: {e}") from e


def _extract_hybrid(pdf_path: str) -> str:
    """
    Extração híbrida: texto nativo + OCR para páginas sem texto
    """
    import pytesseract
    import pdfplumber
    
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    
    logger.debug(f"Extraindo via híbrido: {pdf_path}")
    
    try:
        all_text = []
        
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            
            for i, page in enumerate(pdf.pages, 1):
                # Tentar texto nativo primeiro
                native_text = page.extract_text() or ""
                
                if len(native_text.strip()) > 100:  # Tem texto suficiente
                    all_text.append(native_text)
                    logger.debug(f"Página {i}: {len(native_text)} chars (nativo)")
                else:
                    # Fallback para OCR
                    try:
                        img = page.to_image(resolution=300)
                        ocr_text = pytesseract.image_to_string(img.original, lang='eng')
                        all_text.append(ocr_text)
                        logger.debug(f"Página {i}: {len(ocr_text)} chars (OCR)")
                    except Exception as e:
                        logger.warning(f"OCR falhou página {i}: {e}")
                        if native_text:
                            all_text.append(native_text)
        
        full_text = "\n\n".join(all_text)
        logger.info(f"Híbrido concluído: {len(full_text)} caracteres")
        
        return full_text
        
    except Exception as e:
        logger.error(f"Erro híbrido: {e}")
        raise OCRException(f"Erro: {e}") from e
