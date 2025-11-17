"""
Cache de OCR - Baseado em hash de arquivo
Evita reprocessar PDFs já extraídos
"""

import hashlib
import json
from pathlib import Path
from typing import Optional

from ace.utils.logger import get_logger

logger = get_logger('ace.extraction.cache')

# Diretório de cache
CACHE_DIR = Path('cache/ocr')
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _get_file_hash(pdf_path: str) -> str:
    """Calcula hash SHA256 do arquivo"""
    sha256 = hashlib.sha256()
    
    with open(pdf_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    
    return sha256.hexdigest()


def get_cached_text(pdf_path: str) -> Optional[str]:
    """
    Busca texto em cache
    
    Returns:
        Texto em cache ou None se não existir
    """
    try:
        file_hash = _get_file_hash(pdf_path)
        cache_file = CACHE_DIR / f"{file_hash}.json"
        
        if not cache_file.exists():
            return None
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"✅ Cache HIT: {pdf_path}")
        logger.debug(f"   Hash: {file_hash[:16]}...")
        
        return data['text']
        
    except Exception as e:
        logger.warning(f"Erro ao ler cache: {e}")
        return None


def save_to_cache(pdf_path: str, text: str):
    """Salva texto extraído em cache"""
    try:
        file_hash = _get_file_hash(pdf_path)
        cache_file = CACHE_DIR / f"{file_hash}.json"
        
        data = {
            'file_path': pdf_path,
            'file_hash': file_hash,
            'text_length': len(text),
            'text': text
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        
        logger.debug(f"💾 Texto salvo em cache: {file_hash[:16]}...")
        
    except Exception as e:
        logger.warning(f"Erro ao salvar cache: {e}")


def clear_cache():
    """Limpa todo o cache de OCR"""
    import shutil
    
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("🗑️  Cache de OCR limpo")
