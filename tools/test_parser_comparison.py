"""
Comparação de Parsers - ANTES vs DEPOIS
Testa extração de dados de PDFs reais
"""

import sys
from pathlib import Path

# CORREÇÃO: Adicionar path do ACE ao sys.path
ace_root = Path(__file__).parent.parent
sys.path.insert(0, str(ace_root))

import json
from typing import Dict, List, Any
from datetime import datetime

from ace.extraction.layout import PageText
from ace.extraction.ocr import extract_text_from_pdf
from ace.extraction.parser_acord25 import parse_acord25_gl_limits
from ace.utils.logger import get_logger

logger = get_logger('test.parser_comparison')


class ParserComparator:
    """Compara parser antigo vs novo"""
    
    def __init__(self, backup_parser_path: str):
        self.backup_parser_path = backup_parser_path
        self.old_parser_func = None  # Cache do parser antigo
        self.results = {
            'test_date': datetime.now().isoformat(),
            'files_tested': 0,
            'comparisons': []
        }
    
    def load_old_parser(self):
        """Carrega parser antigo do backup via exec()"""
        if self.old_parser_func:
            return self.old_parser_func
        
        backup_path = Path(self.backup_parser_path)
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup não encontrado: {self.backup_parser_path}")
        
        logger.info(f"Carregando parser antigo de: {backup_path}")
        
        # Ler conteúdo do backup
        with open(backup_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Criar namespace para execução
        namespace = {}
        
        # Executar código no namespace
        exec(code, namespace)
        
        # Pegar função parse_acord25_gl_limits
        if 'parse_acord25_gl_limits' not in namespace:
            raise ImportError("Função parse_acord25_gl_limits não encontrada no backup")
        
        self.old_parser_func = namespace['parse_acord25_gl_limits']
        logger.info("Parser antigo carregado com sucesso")
        
        return self.old_parser_func
    
    def extract_text(self, pdf_path: str) -> str:
        """Extrai texto do PDF"""
        logger.info(f"Extraindo texto de: {pdf_path}")
        try:
            result = extract_text_from_pdf(pdf_path)
            
            # CORREÇÃO: OCR pode retornar lista ou string
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
    
    def process_with_parser(self, parser_func, certificate_id: int, text: str) -> Dict:
        """Processa com um parser específico"""
        if not text or not text.strip():
            return {'error': 'Texto vazio'}
        
        try:
            pages = [PageText(page_number=1, text=text, lines=text.splitlines())]
            result = parser_func(certificate_id, pages)
            
            if result is None:
                return {'error': 'Parser retornou None'}
            
            # Serializa resultado
            return {
                'quality_score': result.quality_score,
                'policies_count': len(result.policies),
                'coverages_count': len(result.coverages),
                'policy_data': {
                    'policy_number': result.policies[0].policy_number if result.policies else None,
                    'effective_date': result.policies[0].effective_date if result.policies else None,
                    'expiration_date': result.policies[0].expiration_date if result.policies else None,
                } if result.policies else {},
                'coverages': [
                    {
                        'code': cov.coverage_code,
                        'amount': cov.limit_amount,
                        'confidence': cov.confidence_score
                    }
                    for cov in result.coverages
                ]
            }
        except Exception as e:
            logger.error(f"Erro no parsing: {e}", exc_info=True)
            return {'error': str(e)}
    
    def compare_results(self, old_result: Dict, new_result: Dict) -> Dict:
        """Compara dois resultados"""
        comparison = {
            'status': 'unknown',
            'improvements': [],
            'regressions': [],
            'changes': {}
        }
        
        # Se ambos falharam
        if 'error' in old_result and 'error' in new_result:
            comparison['status'] = 'both_failed'
            return comparison
        
        # Se só o antigo falhou
        if 'error' in old_result and 'error' not in new_result:
            comparison['status'] = 'improvement_major'
            comparison['improvements'].append('Novo parser conseguiu extrair dados (antigo falhou)')
            return comparison
        
        # Se só o novo falhou
        if 'error' not in old_result and 'error' in new_result:
            comparison['status'] = 'regression_major'
            comparison['regressions'].append('Novo parser falhou (antigo funcionou)')
            return comparison
        
        # Ambos funcionaram - comparar qualidade
        old_quality = old_result.get('quality_score', 0)
        new_quality = new_result.get('quality_score', 0)
        
        comparison['changes']['quality_score'] = {
            'old': old_quality,
            'new': new_quality,
            'delta': new_quality - old_quality
        }
        
        if new_quality > old_quality:
            comparison['improvements'].append(f'Quality score aumentou: {old_quality:.2f} → {new_quality:.2f}')
        elif new_quality < old_quality:
            comparison['regressions'].append(f'Quality score diminuiu: {old_quality:.2f} → {new_quality:.2f}')
        
        # Comparar número de coverages
        old_cov = old_result.get('coverages_count', 0)
        new_cov = new_result.get('coverages_count', 0)
        
        comparison['changes']['coverages_count'] = {
            'old': old_cov,
            'new': new_cov,
            'delta': new_cov - old_cov
        }
        
        if new_cov > old_cov:
            comparison['improvements'].append(f'Mais coverages extraídos: {old_cov} → {new_cov}')
        elif new_cov < old_cov:
            comparison['regressions'].append(f'Menos coverages extraídos: {old_cov} → {new_cov}')
        
        # Determinar status geral
        if comparison['regressions']:
            comparison['status'] = 'regression'
        elif comparison['improvements']:
            comparison['status'] = 'improvement'
        else:
            comparison['status'] = 'no_change'
        
        return comparison
    
    def test_file(self, pdf_path: str, certificate_id: int = 1) -> Dict:
        """Testa um arquivo PDF"""
        logger.info(f"\n{'='*70}")
        logger.info(f"Testando: {pdf_path}")
        logger.info(f"{'='*70}")
        
        result = {
            'file': pdf_path,
            'certificate_id': certificate_id,
            'timestamp': datetime.now().isoformat()
        }
        
        # Verificar se arquivo existe e não está vazio
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            result['status'] = 'file_not_found'
            logger.error(f"Arquivo não encontrado: {pdf_path}")
            return result
        
        if pdf_file.stat().st_size == 0:
            result['status'] = 'empty_file'
            logger.warning(f"Arquivo vazio (0 bytes): {pdf_path}")
            return result
        
        # 1. Extrair texto (OCR)
        text = self.extract_text(pdf_path)
        if not text or not text.strip():
            result['status'] = 'ocr_failed'
            logger.error("OCR falhou ou retornou texto vazio")
            return result
        
        result['text_length'] = len(text)
        logger.info(f"Texto extraído: {len(text)} caracteres")
        
        # 2. Processar com parser ANTIGO
        logger.info("Processando com parser ANTIGO...")
        try:
            old_parser = self.load_old_parser()
            old_result = self.process_with_parser(old_parser, certificate_id, text)
        except Exception as e:
            logger.error(f"Erro ao carregar/executar parser antigo: {e}")
            old_result = {'error': f'Falha ao carregar parser antigo: {e}'}
        
        result['old_parser'] = old_result
        
        # 3. Processar com parser NOVO
        logger.info("Processando com parser NOVO...")
        new_result = self.process_with_parser(parse_acord25_gl_limits, certificate_id, text)
        result['new_parser'] = new_result
        
        # 4. Comparar
        logger.info("Comparando resultados...")
        comparison = self.compare_results(old_result, new_result)
        result['comparison'] = comparison
        
        # Log resultado
        logger.info(f"\nStatus: {comparison['status']}")
        if comparison['improvements']:
            logger.info("Melhorias:")
            for imp in comparison['improvements']:
                logger.info(f"  ✅ {imp}")
        if comparison['regressions']:
            logger.warning("Regressões:")
            for reg in comparison['regressions']:
                logger.warning(f"  ❌ {reg}")
        
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
        
        logger.info(f"Encontrados {len(pdf_files)} PDFs, testando {min(len(pdf_files), max_files)}...")
        
        # Carregar parser antigo uma vez
        try:
            self.load_old_parser()
        except Exception as e:
            logger.error(f"ERRO CRÍTICO: Não foi possível carregar parser antigo: {e}")
            logger.error("Verifique se o backup existe e está acessível")
            return
        
        for i, pdf_file in enumerate(pdf_files, 1):
            result = self.test_file(str(pdf_file), certificate_id=i)
            self.results['comparisons'].append(result)
            self.results['files_tested'] = i
        
        # Gerar relatório final
        self.generate_report()
    
    def generate_report(self):
        """Gera relatório consolidado"""
        logger.info(f"\n{'='*70}")
        logger.info("RELATÓRIO FINAL DE COMPARAÇÃO")
        logger.info(f"{'='*70}\n")
        
        total = self.results['files_tested']
        
        if total == 0:
            logger.warning("Nenhum arquivo testado")
            return
        
        # Estatísticas
        stats = {
            'improvements': 0,
            'regressions': 0,
            'no_change': 0,
            'both_failed': 0,
            'ocr_failed': 0,
            'empty_file': 0
        }
        
        for comp in self.results['comparisons']:
            status = comp.get('comparison', {}).get('status', comp.get('status'))
            if 'improvement' in status:
                stats['improvements'] += 1
            elif 'regression' in status:
                stats['regressions'] += 1
            elif status == 'no_change':
                stats['no_change'] += 1
            elif status == 'both_failed':
                stats['both_failed'] += 1
            elif status == 'ocr_failed':
                stats['ocr_failed'] += 1
            elif status == 'empty_file':
                stats['empty_file'] += 1
        
        logger.info(f"Arquivos testados: {total}")
        logger.info(f"\n📊 Estatísticas:")
        logger.info(f"  ✅ Melhorias: {stats['improvements']} ({stats['improvements']/total*100:.1f}%)")
        logger.info(f"  ❌ Regressões: {stats['regressions']} ({stats['regressions']/total*100:.1f}%)")
        logger.info(f"  ⚪ Sem mudança: {stats['no_change']} ({stats['no_change']/total*100:.1f}%)")
        logger.info(f"  🔴 Ambos falharam: {stats['both_failed']}")
        logger.info(f"  ⚠️  OCR falhou: {stats['ocr_failed']}")
        logger.info(f"  📄 Arquivo vazio: {stats['empty_file']}")
        
        # Salvar JSON
        report_file = Path('reports') / f"parser_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n💾 Relatório salvo: {report_file}")
        
        # Conclusão
        if stats['regressions'] > 0:
            logger.warning(f"\n⚠️  ATENÇÃO: {stats['regressions']} regressões detectadas!")
        elif stats['improvements'] > 0:
            logger.info(f"\n🎉 SUCESSO: {stats['improvements']} melhorias!")
        else:
            logger.info("\n✅ Parser manteve qualidade")


def main():
    """Main"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Compara parser antigo vs novo')
    parser.add_argument('--pdf-dir', required=True, help='Diretório com PDFs de teste')
    parser.add_argument('--backup', required=True, help='Caminho do parser backup')
    parser.add_argument('--max-files', type=int, default=10, help='Máximo de arquivos')
    
    args = parser.parse_args()
    
    comparator = ParserComparator(args.backup)
    comparator.test_directory(args.pdf_dir, args.max_files)


if __name__ == "__main__":
    main()
