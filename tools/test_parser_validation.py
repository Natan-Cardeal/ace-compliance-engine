"""
Teste do Parser Novo - SEM comparação
Valida que o parser melhorado funciona
"""

import sys
from pathlib import Path

# Adicionar ACE ao path
ace_root = Path(__file__).parent.parent
sys.path.insert(0, str(ace_root))

import json
from typing import Dict, List
from datetime import datetime

from ace.extraction.layout import PageText
from ace.extraction.ocr import extract_text_from_pdf
from ace.extraction.parser_acord25 import parse_acord25_gl_limits
from ace.utils.logger import get_logger

logger = get_logger('test.parser_validation')


class ParserValidator:
    """Valida parser novo sem comparação"""
    
    def __init__(self):
        self.results = {
            'test_date': datetime.now().isoformat(),
            'parser_version': 'NEW_IMPROVED',
            'files_tested': 0,
            'extractions': []
        }
    
    def extract_text(self, pdf_path: str) -> str:
        """Extrai texto do PDF"""
        logger.info(f"Extraindo texto de: {pdf_path}")
        try:
            result = extract_text_from_pdf(pdf_path)
            
            # OCR pode retornar lista ou string
            if isinstance(result, list):
                text = "\n".join(str(item) for item in result if item)
            elif isinstance(result, str):
                text = result
            else:
                text = str(result) if result else ""
            
            return text
            
        except Exception as e:
            logger.error(f"Erro no OCR: {e}")
            return ""
    
    def test_file(self, pdf_path: str, certificate_id: int = 1) -> Dict:
        """Testa um arquivo PDF"""
        logger.info(f"\n{'='*70}")
        logger.info(f"Testando: {pdf_path}")
        logger.info(f"{'='*70}")
        
        result = {
            'file': pdf_path,
            'file_name': Path(pdf_path).name,
            'certificate_id': certificate_id,
            'timestamp': datetime.now().isoformat(),
            'status': 'unknown'
        }
        
        # Verificar arquivo
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            result['status'] = 'file_not_found'
            logger.error(f"Arquivo não encontrado")
            return result
        
        file_size = pdf_file.stat().st_size
        result['file_size_bytes'] = file_size
        
        if file_size == 0:
            result['status'] = 'empty_file'
            logger.warning(f"Arquivo vazio (0 bytes)")
            return result
        
        logger.info(f"Tamanho: {file_size:,} bytes")
        
        # 1. Extrair texto (OCR)
        text = self.extract_text(pdf_path)
        if not text or not text.strip():
            result['status'] = 'ocr_failed'
            logger.error("OCR falhou ou retornou texto vazio")
            return result
        
        result['text_length'] = len(text)
        logger.info(f"Texto extraído: {len(text)} caracteres")
        
        # 2. Processar com parser
        logger.info("Processando com parser...")
        try:
            pages = [PageText(page_number=1, text=text, lines=text.splitlines())]
            # ✅ NOVO: Adicionar referência ao PDF para fallback
            pages[0]._source_pdf = str(pdf_file)
            parsed = parse_acord25_gl_limits(certificate_id, pages)
            
            if parsed is None:
                result['status'] = 'parsing_failed'
                result['error'] = 'Parser retornou None'
                logger.error("Parser retornou None")
                return result
            
            # Extrair dados
            result['status'] = 'success'
            result['quality_score'] = parsed.quality_score
            result['policies_count'] = len(parsed.policies)
            result['coverages_count'] = len(parsed.coverages)
            
            # Policy data
            if parsed.policies:
                policy = parsed.policies[0]
                result['policy_number'] = policy.policy_number
                result['effective_date'] = policy.effective_date
                result['expiration_date'] = policy.expiration_date
            
            # Coverages
            result['coverages'] = [
                {
                    'code': cov.coverage_code,
                    'amount': cov.limit_amount,
                    'currency': cov.limit_currency,
                    'confidence': cov.confidence_score
                }
                for cov in parsed.coverages
            ]
            
            # Log sucesso
            logger.info(f"✅ SUCESSO!")
            logger.info(f"  Quality Score: {parsed.quality_score:.2f}")
            logger.info(f"  Coverages: {len(parsed.coverages)}")
            logger.info(f"  Policy: {policy.policy_number if parsed.policies else 'N/A'}")
            
            if parsed.coverages:
                logger.info(f"  Limites extraídos:")
                for cov in parsed.coverages:
                    logger.info(f"    {cov.coverage_code}: USD {cov.limit_amount:,.2f}")
            
        except Exception as e:
            result['status'] = 'parsing_error'
            result['error'] = str(e)
            logger.error(f"Erro no parsing: {e}", exc_info=True)
        
        return result
    
    def test_directory(self, pdf_dir: str, max_files: int = 10):
        """Testa todos PDFs em um diretório"""
        pdf_path = Path(pdf_dir)
        
        if not pdf_path.exists():
            logger.error(f"Diretório não encontrado: {pdf_dir}")
            return
        
        pdf_files = list(pdf_path.glob("*.pdf"))[:max_files]
        
        if not pdf_files:
            logger.error(f"Nenhum PDF encontrado em: {pdf_dir}")
            return
        
        logger.info(f"\n{'='*70}")
        logger.info(f"INICIANDO VALIDAÇÃO DO PARSER")
        logger.info(f"{'='*70}")
        logger.info(f"PDFs encontrados: {len(pdf_files)}")
        logger.info(f"PDFs a testar: {min(len(pdf_files), max_files)}")
        logger.info(f"{'='*70}\n")
        
        for i, pdf_file in enumerate(pdf_files, 1):
            result = self.test_file(str(pdf_file), certificate_id=i)
            self.results['extractions'].append(result)
            self.results['files_tested'] = i
        
        # Gerar relatório
        self.generate_report()
    
    def generate_report(self):
        """Gera relatório consolidado"""
        logger.info(f"\n{'='*70}")
        logger.info("RELATÓRIO FINAL DE VALIDAÇÃO")
        logger.info(f"{'='*70}\n")
        
        total = self.results['files_tested']
        
        if total == 0:
            logger.warning("Nenhum arquivo testado")
            return
        
        # Estatísticas
        stats = {
            'success': 0,
            'ocr_failed': 0,
            'parsing_failed': 0,
            'parsing_error': 0,
            'empty_file': 0,
            'file_not_found': 0
        }
        
        total_quality = 0
        total_coverages = 0
        
        for extraction in self.results['extractions']:
            status = extraction.get('status')
            stats[status] = stats.get(status, 0) + 1
            
            if status == 'success':
                total_quality += extraction.get('quality_score', 0)
                total_coverages += extraction.get('coverages_count', 0)
        
        success_count = stats['success']
        
        logger.info(f"Arquivos testados: {total}")
        logger.info(f"\n📊 Estatísticas:")
        logger.info(f"  ✅ Sucesso: {success_count} ({success_count/total*100:.1f}%)")
        logger.info(f"  ❌ OCR falhou: {stats['ocr_failed']}")
        logger.info(f"  ❌ Parsing falhou: {stats['parsing_failed']}")
        logger.info(f"  ❌ Erro no parsing: {stats['parsing_error']}")
        logger.info(f"  ⚠️  Arquivo vazio: {stats['empty_file']}")
        
        if success_count > 0:
            avg_quality = total_quality / success_count
            avg_coverages = total_coverages / success_count
            
            logger.info(f"\n📈 Métricas de Qualidade:")
            logger.info(f"  Qualidade média: {avg_quality:.2f}")
            logger.info(f"  Coverages por doc: {avg_coverages:.1f}")
        
        # Salvar JSON
        report_file = Path('reports') / f"parser_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n💾 Relatório salvo: {report_file}")
        
        # Conclusão
        if success_count == total:
            logger.info(f"\n🎉 100% DE SUCESSO! Parser funcionou em todos os {total} PDFs!")
        elif success_count > 0:
            logger.info(f"\n✅ Parser funcionou em {success_count}/{total} PDFs ({success_count/total*100:.1f}%)")
        else:
            logger.error(f"\n❌ FALHA TOTAL: Parser não funcionou em nenhum PDF")


def main():
    """Main"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Valida parser novo')
    parser.add_argument('--pdf-dir', default='test_data/sample_pdfs/originals', 
                       help='Diretório com PDFs de teste')
    parser.add_argument('--max-files', type=int, default=10, 
                       help='Máximo de arquivos')
    
    args = parser.parse_args()
    
    validator = ParserValidator()
    validator.test_directory(args.pdf_dir, args.max_files)


if __name__ == "__main__":
    main()

