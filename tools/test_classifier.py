"""
Testa o classificador com amostra real
"""

import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ace.extraction.ocr import extract_text_from_pdf
from ace.extraction.classifier import classify_document, DocType
from ace.utils.logger import get_logger

logger = get_logger('test.classifier')


def test_classifier_on_sample():
    """Testa classificador nos 100 PDFs"""
    
    sample_dir = Path("test_data/sample_pdfs/diverse_100")
    pdfs = list(sample_dir.glob("*.pdf"))
    
    if not pdfs:
        logger.error("❌ Nenhum PDF encontrado!")
        return
    
    logger.info(f"🔍 Testando classificador em {len(pdfs)} PDFs\n")
    
    # Contadores
    by_type = {}
    confidences = []
    
    # Classificar cada PDF
    for i, pdf_path in enumerate(pdfs[:20], 1):  # Testar nos primeiros 20
        logger.info(f"[{i}/20] {pdf_path.name[:60]}")
        
        try:
            # Extrair texto
            text = extract_text_from_pdf(str(pdf_path))
            
            if not text:
                logger.warning("  ⚠️  Sem texto")
                continue
            
            # Classificar
            result = classify_document(text)
            
            # Contar
            doc_type = result.doc_type.value
            by_type[doc_type] = by_type.get(doc_type, 0) + 1
            confidences.append(result.confidence)
            
            # Mostrar resultado
            logger.info(f"  📋 Tipo: {result.doc_type.value}")
            logger.info(f"  📊 Confiança: {result.confidence:.2f}")
            logger.info(f"  🔍 Indicadores: {', '.join(result.indicators[:3])}")
            logger.info("")
            
        except Exception as e:
            logger.error(f"  ❌ Erro: {e}")
            continue
    
    # Resumo
    logger.info("=" * 70)
    logger.info("📊 RESUMO")
    logger.info("=" * 70)
    
    for doc_type, count in sorted(by_type.items(), key=lambda x: -x[1]):
        pct = count / len(confidences) * 100
        logger.info(f"  {doc_type}: {count} ({pct:.1f}%)")
    
    if confidences:
        avg_conf = sum(confidences) / len(confidences)
        logger.info(f"\n  Confiança média: {avg_conf:.2f}")


if __name__ == "__main__":
    test_classifier_on_sample()
