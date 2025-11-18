"""
Test Data Manager - Gestor de Massa de Testes
Controla quais PDFs do datadump são usados nos testes
"""

import sys
from pathlib import Path

# CORREÇÃO: Adicionar path do ACE ao sys.path
ace_root = Path(__file__).parent.parent
sys.path.insert(0, str(ace_root))

import json
import shutil
from datetime import datetime
from typing import List, Dict
import hashlib

from ace.utils.logger import get_logger

logger = get_logger('test.data_manager')


class TestDataManager:
    """Gerencia massa de testes e rastreabilidade"""
    
    def __init__(self, 
                 datadump_path: str,
                 test_data_path: str = 'test_data'):
        self.datadump_path = Path(datadump_path)
        self.test_data_path = Path(test_data_path)
        
        # Pastas
        self.samples_dir = self.test_data_path / 'sample_pdfs' / 'originals'
        self.metadata_dir = self.test_data_path / 'metadata'
        
        # Criar estrutura
        self.samples_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # Arquivo de registro
        self.registry_file = self.metadata_dir / 'test_samples_registry.json'
        self.registry = self._load_registry()
    
    def _load_registry(self) -> Dict:
        """Carrega registro de amostras"""
        if self.registry_file.exists():
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'created_at': datetime.now().isoformat(),
            'datadump_source': str(self.datadump_path),
            'samples': [],
            'total_samples': 0
        }
    
    def _save_registry(self):
        """Salva registro"""
        self.registry['last_updated'] = datetime.now().isoformat()
        self.registry['total_samples'] = len(self.registry['samples'])
        
        with open(self.registry_file, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Registry salvo: {self.registry['total_samples']} amostras")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calcula hash SHA256 do arquivo"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _get_sample_id(self) -> str:
        """Gera ID único para amostra"""
        return f"COI_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.registry['samples']) + 1:04d}"
    
    def copy_samples(self, 
                     num_samples: int = 10,
                     criteria: str = 'random',
                     overwrite: bool = False) -> List[Dict]:
        """
        Copia amostras do datadump para pasta de testes
        
        Args:
            num_samples: Número de amostras a copiar
            criteria: Critério de seleção ('random', 'first', 'size')
            overwrite: Se True, permite recopiar amostras existentes
        
        Returns:
            Lista de amostras copiadas
        """
        logger.info(f"Copiando {num_samples} amostras do datadump...")
        logger.info(f"Datadump: {self.datadump_path}")
        
        # Verificar se datadump existe
        if not self.datadump_path.exists():
            raise FileNotFoundError(f"Datadump não encontrado: {self.datadump_path}")
        
        # Listar PDFs disponíveis
        all_pdfs = list(self.datadump_path.glob("**/*.pdf"))
        
        if not all_pdfs:
            raise FileNotFoundError(f"Nenhum PDF encontrado em: {self.datadump_path}")
        
        logger.info(f"PDFs disponíveis no datadump: {len(all_pdfs)}")
        
        # Selecionar amostras
        if criteria == 'random':
            import random
            selected_pdfs = random.sample(all_pdfs, min(num_samples, len(all_pdfs)))
        elif criteria == 'first':
            selected_pdfs = all_pdfs[:num_samples]
        elif criteria == 'size':
            # Ordenar por tamanho (pegar variedade)
            sorted_pdfs = sorted(all_pdfs, key=lambda p: p.stat().st_size)
            # Pegar distribuição: pequenos, médios, grandes
            step = max(1, len(sorted_pdfs) // num_samples)
            selected_pdfs = [sorted_pdfs[min(i * step, len(sorted_pdfs) - 1)] for i in range(num_samples)]
        else:
            selected_pdfs = all_pdfs[:num_samples]
        
        copied_samples = []
        
        for pdf_file in selected_pdfs:
            # Calcular hash
            file_hash = self._calculate_file_hash(pdf_file)
            
            # Verificar se já existe
            existing = next(
                (s for s in self.registry['samples'] if s['hash'] == file_hash),
                None
            )
            
            if existing and not overwrite:
                logger.info(f"Amostra já existe: {existing['sample_id']}")
                copied_samples.append(existing)
                continue
            
            # Gerar ID
            sample_id = self._get_sample_id()
            
            # Nome do arquivo de destino
            dest_filename = f"{sample_id}.pdf"
            dest_path = self.samples_dir / dest_filename
            
            # Copiar arquivo
            logger.info(f"Copiando: {pdf_file.name} → {dest_filename}")
            shutil.copy2(pdf_file, dest_path)
            
            # Metadados
            sample_info = {
                'sample_id': sample_id,
                'original_filename': pdf_file.name,
                'original_path': str(pdf_file),
                'test_path': str(dest_path),
                'hash': file_hash,
                'size_bytes': pdf_file.stat().st_size,
                'copied_at': datetime.now().isoformat(),
                'used_in_tests': []
            }
            
            # Adicionar ao registry
            self.registry['samples'].append(sample_info)
            copied_samples.append(sample_info)
        
        # Salvar registry
        self._save_registry()
        
        logger.info(f"✅ {len(copied_samples)} amostras prontas para teste")
        
        return copied_samples
    
    def register_test_usage(self, sample_id: str, test_name: str, results: Dict):
        """Registra uso de amostra em teste"""
        sample = next(
            (s for s in self.registry['samples'] if s['sample_id'] == sample_id),
            None
        )
        
        if not sample:
            logger.warning(f"Amostra não encontrada: {sample_id}")
            return
        
        usage = {
            'test_name': test_name,
            'timestamp': datetime.now().isoformat(),
            'results': results
        }
        
        sample['used_in_tests'].append(usage)
        self._save_registry()
        
        logger.debug(f"Uso registrado: {sample_id} em {test_name}")
    
    def get_samples_list(self) -> List[str]:
        """Retorna lista de caminhos das amostras"""
        return [s['test_path'] for s in self.registry['samples']]
    
    def generate_report(self) -> str:
        """Gera relatório da massa de testes"""
        report = []
        report.append("=" * 70)
        report.append("RELATÓRIO DA MASSA DE TESTES")
        report.append("=" * 70)
        report.append(f"\nDatadump: {self.registry['datadump_source']}")
        report.append(f"Total de amostras: {self.registry['total_samples']}")
        report.append(f"Criado em: {self.registry['created_at']}")
        report.append(f"Última atualização: {self.registry.get('last_updated', 'N/A')}")
        
        if self.registry['samples']:
            report.append(f"\n{'='*70}")
            report.append("AMOSTRAS:")
            report.append(f"{'='*70}")
            
            for i, sample in enumerate(self.registry['samples'], 1):
                report.append(f"\n{i}. {sample['sample_id']}")
                report.append(f"   Original: {sample['original_filename']}")
                report.append(f"   Tamanho: {sample['size_bytes']:,} bytes")
                report.append(f"   Copiado: {sample['copied_at']}")
                report.append(f"   Testes: {len(sample['used_in_tests'])}")
        
        return "\n".join(report)


def main():
    """Main"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gerencia massa de testes')
    parser.add_argument('--datadump', required=True, help='Caminho do datadump')
    parser.add_argument('--copy', type=int, help='Número de amostras a copiar')
    parser.add_argument('--criteria', choices=['random', 'first', 'size'], 
                       default='random', help='Critério de seleção')
    parser.add_argument('--report', action='store_true', help='Gerar relatório')
    
    args = parser.parse_args()
    
    manager = TestDataManager(args.datadump)
    
    if args.copy:
        samples = manager.copy_samples(args.copy, args.criteria)
        print(f"\n✅ {len(samples)} amostras copiadas")
        print(f"\nPasta de testes: {manager.samples_dir}")
    
    if args.report:
        print(manager.generate_report())


if __name__ == "__main__":
    main()
