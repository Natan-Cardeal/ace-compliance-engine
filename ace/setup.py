"""
Setup e Validação de Dependências
"""

import os
import sys
from pathlib import Path
import subprocess

# ✅ NOVO: Carregar .env se existir
try:
    from dotenv import load_dotenv
    load_dotenv()  # Carrega variáveis de .env
except ImportError:
    pass  # python-dotenv não instalado, ok

from ace.utils.logger import get_logger
from ace.utils.exceptions import ConfigurationException

logger = get_logger('ace.setup')


def validate_tesseract() -> str:
    """
    Valida que Tesseract está instalado e acessível
    
    Returns:
        Path do Tesseract
        
    Raises:
        ConfigurationException: Se Tesseract não encontrado
    """
    # 1. Verificar variável de ambiente
    tesseract_path = os.getenv('TESSERACT_CMD', r'C:\Program Files\Tesseract-OCR\tesseract.exe')
    
    # 2. Verificar se existe
    if not Path(tesseract_path).exists():
        error_msg = (
            f"❌ TESSERACT NÃO ENCONTRADO: {tesseract_path}\n\n"
            "SOLUÇÃO:\n"
            "1. Baixe: https://github.com/tesseract-ocr/tesseract/releases\n"
            "2. Instale em: C:\\Program Files\\Tesseract-OCR\n"
            "3. OU configure variável: TESSERACT_CMD=<caminho>\n"
        )
        logger.critical(error_msg)
        raise ConfigurationException(error_msg)
    
    # 3. Verificar se funciona
    try:
        result = subprocess.run(
            [tesseract_path, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            raise ConfigurationException(f"Tesseract falhou ao executar: {result.stderr}")
        
        version = result.stdout.split('\n')[0]
        logger.info(f"✅ Tesseract validado: {version}")
        logger.info(f"   Path: {tesseract_path}")
        
        return tesseract_path
        
    except subprocess.TimeoutExpired:
        raise ConfigurationException("Tesseract não respondeu em 5 segundos")
    except Exception as e:
        raise ConfigurationException(f"Erro ao validar Tesseract: {e}")


def validate_pdfplumber():
    """Valida que pdfplumber está instalado"""
    try:
        import pdfplumber
        logger.info(f"✅ pdfplumber instalado: v{pdfplumber.__version__}")
    except ImportError:
        error_msg = (
            "❌ pdfplumber NÃO INSTALADO\n\n"
            "SOLUÇÃO:\n"
            "pip install pdfplumber\n"
        )
        logger.critical(error_msg)
        raise ConfigurationException(error_msg)


def validate_pytesseract():
    """Valida que pytesseract está instalado"""
    try:
        import pytesseract
        logger.info(f"✅ pytesseract instalado")
    except ImportError:
        error_msg = (
            "❌ pytesseract NÃO INSTALADO\n\n"
            "SOLUÇÃO:\n"
            "pip install pytesseract\n"
        )
        logger.critical(error_msg)
        raise ConfigurationException(error_msg)


def validate_all_dependencies():
    """
    Valida TODAS as dependências no startup
    
    Raises:
        ConfigurationException: Se alguma dependência falhar
    """
    logger.info("🔍 Validando dependências do ACE...")
    
    try:
        validate_pytesseract()
        validate_pdfplumber()
        tesseract_path = validate_tesseract()
        
        logger.info("✅ TODAS as dependências validadas com sucesso!")
        return tesseract_path
        
    except ConfigurationException as e:
        logger.critical("❌ VALIDAÇÃO FALHOU!")
        logger.critical(str(e))
        raise


# Validar na importação do módulo
try:
    TESSERACT_PATH = validate_all_dependencies()
except ConfigurationException:
    logger.critical("ACE não pode iniciar sem dependências válidas")
    sys.exit(1)

