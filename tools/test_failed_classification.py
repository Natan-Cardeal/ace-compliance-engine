"""
Testa classificador nos PDFs que falharam
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ace.extraction.ocr import extract_text_from_pdf
from ace.extraction.classifier import classify_document
from ace.utils.logger import get_logger

logger = get_logger('test.failed_docs')


def test_failed_docs():
    """Testa classificador nos documentos que falharam"""
    
    # Os 4 que falharam no parsing
    failed_files = [
        "sample_053_17036 Granges Viking_KenIsaacsInteriors_Auto_19_1002.pdf",
        "sample_096_17036 Granges Viking_CoopersSteelFabricatorsWC_23_1023.pdf",
        "sample_097_Where I'm From... DR.pdf",
        "sample_099_17002 MGC O Plant_ThermalEquipmentSales_24_0116.pdf"
    ]
    
    sample_dir = Path("test_data/sample_pdfs/diverse_100")
    
    logger.info("=" * 70)
    logger.info("🔍 TESTANDO CLASSIFICADOR NOS DOCUMENTOS QUE FALHARAM")
    logger.info("=" * 70)
    logger.info("")
    
    for filename in failed_files:
        pdf_path = sample_dir / filename
        
        if not pdf_path.exists():
            logger.warning(f"❌ Arquivo não encontrado: {filename}")
            continue
        
        logger.info(f"📄 {filename}")
        
        try:
            # Extrair texto
            text = extract_text_from_pdf(str(pdf_path))
            
            if not text:
                logger.warning("  ⚠️  Sem texto extraído")
                continue
            
            logger.info(f"  📝 Texto extraído: {len(text)} caracteres")
            
            # Classificar
            result = classify_document(text)
            
            # Mostrar resultado
            logger.info(f"  📋 Tipo identificado: {result.doc_type.value}")
            logger.info(f"  📊 Confiança: {result.confidence:.2f}")
            logger.info(f"  🔍 Indicadores encontrados:")
            for indicator in result.indicators[:5]:
                logger.info(f"     - {indicator}")
            
            # Mostrar trecho do texto (primeiras 500 chars)
            logger.info(f"  📖 Trecho do texto:")
            preview = text[:500].replace('\n', ' ')
            logger.info(f"     {preview}...")
            
            logger.info("")
            
        except Exception as e:
            logger.error(f"  ❌ Erro: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    logger.info("=" * 70)


if __name__ == "__main__":
    test_failed_docs()
