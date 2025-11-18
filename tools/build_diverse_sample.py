"""
Analisa base de PDFs recursivamente e cria amostra representativa
"""

import os
import random
import shutil
from pathlib import Path
from collections import Counter
from typing import List, Tuple

from ace.extraction.ocr import extract_text_from_pdf
from ace.utils.logger import get_logger

logger = get_logger('sample_builder')


def extract_keywords(text: str) -> List[str]:
    """Extrai keywords relevantes do texto"""
    keywords = []
    
    text_upper = text.upper()
    
    # Tipos de documento
    if "ACORD 25" in text_upper:
        keywords.append("ACORD_25")
    if "CERTIFICATE OF LIABILITY" in text_upper:
        keywords.append("LIABILITY_CERT")
    if "WORKERS COMPENSATION" in text_upper or "WORKERS' COMPENSATION" in text_upper:
        keywords.append("WORKERS_COMP")
    if "AUTOMOBILE" in text_upper or "AUTO LIABILITY" in text_upper:
        keywords.append("AUTO")
    if "UMBRELLA" in text_upper or "EXCESS" in text_upper:
        keywords.append("UMBRELLA")
    if "ENDORSEMENT" in text_upper:
        keywords.append("ENDORSEMENT")
    if "CERTIFICATE" in text_upper and not keywords:
        keywords.append("CERTIFICATE_GENERIC")
    
    # Seguradoras comuns
    insurers = ["TRAVELERS", "HARTFORD", "ZURICH", "CNA", "LIBERTY", "NATIONWIDE", "STATE FARM"]
    for insurer in insurers:
        if insurer in text_upper:
            keywords.append(f"CARRIER_{insurer}")
    
    # Limites GL
    if "EACH OCCURRENCE" in text_upper:
        keywords.append("HAS_GL_LIMITS")
    
    return keywords


def analyze_pdf_directory(directory: str, max_files: int = None) -> List[Tuple[str, List[str], str]]:
    """
    Analisa diretório de PDFs RECURSIVAMENTE
    
    Returns:
        List[(filepath, keywords, relative_path)]
    """
    base_path = Path(directory)
    
    # Buscar TODOS os PDFs recursivamente
    logger.info(f"🔍 Buscando PDFs em: {directory}")
    logger.info(f"   (incluindo todas as subpastas)")
    
    pdf_files = list(base_path.rglob("*.pdf"))
    
    logger.info(f"📁 Total de PDFs encontrados: {len(pdf_files)}")
    
    # Mostrar estrutura de pastas
    folders = set(p.parent for p in pdf_files)
    logger.info(f"📂 Pastas com PDFs: {len(folders)}")
    
    if max_files:
        logger.info(f"⚠️  Limitando análise a {max_files} arquivos")
        pdf_files = pdf_files[:max_files]
    
    logger.info(f"\n🔬 Analisando {len(pdf_files)} PDFs...")
    
    results = []
    errors = 0
    empty = 0
    
    for i, pdf_path in enumerate(pdf_files, 1):
        if i % 10 == 0:
            logger.info(f"   Progresso: {i}/{len(pdf_files)} ({i/len(pdf_files)*100:.1f}%)")
        
        try:
            # Caminho relativo para organização
            rel_path = pdf_path.relative_to(base_path)
            
            # Extrair texto
            text = extract_text_from_pdf(str(pdf_path))
            
            if text and len(text) > 100:
                keywords = extract_keywords(text)
                if not keywords:
                    keywords = ["UNKNOWN"]
                results.append((str(pdf_path), keywords, str(rel_path)))
            else:
                empty += 1
                
        except Exception as e:
            errors += 1
            if errors <= 5:  # Mostrar só os primeiros 5 erros
                logger.error(f"   Erro em {pdf_path.name}: {e}")
            continue
    
    logger.info(f"\n✅ Análise concluída!")
    logger.info(f"   Sucesso: {len(results)}")
    logger.info(f"   Vazios: {empty}")
    logger.info(f"   Erros: {errors}")
    
    return results


def create_diverse_sample(results: List[Tuple[str, List[str], str]], sample_size: int = 100) -> List[Tuple[str, str]]:
    """
    Cria amostra diversa baseada em keywords
    
    Returns:
        List[(filepath, relative_path)]
    """
    # Contar keywords
    keyword_counts = Counter()
    for _, keywords, _ in results:
        keyword_counts.update(keywords)
    
    logger.info(f"\n📊 Keywords encontradas:")
    for kw, count in keyword_counts.most_common(20):
        logger.info(f"   {kw}: {count}")
    
    # Estratégia: pegar proporcionalmente de cada tipo
    by_primary_type = {}
    
    for filepath, keywords, rel_path in results:
        primary = keywords[0] if keywords else "UNKNOWN"
        
        if primary not in by_primary_type:
            by_primary_type[primary] = []
        by_primary_type[primary].append((filepath, rel_path))
    
    logger.info(f"\n📈 Distribuição por tipo primário:")
    for doc_type, files in sorted(by_primary_type.items(), key=lambda x: -len(x[1])):
        logger.info(f"   {doc_type}: {len(files)}")
    
    # Amostrar proporcionalmente
    sample = []
    total_docs = len(results)
    
    for doc_type, files in by_primary_type.items():
        proportion = len(files) / total_docs
        n_to_sample = max(1, int(sample_size * proportion))
        n_to_sample = min(n_to_sample, len(files))
        
        sampled = random.sample(files, n_to_sample)
        sample.extend(sampled)
        
        logger.info(f"   ✓ Amostrando {n_to_sample} de {doc_type}")
    
    # Se não chegou em sample_size, pegar aleatórios
    if len(sample) < sample_size:
        all_files = [(f, r) for f, _, r in results]
        remaining = [x for x in all_files if x not in sample]
        n_more = min(sample_size - len(sample), len(remaining))
        sample.extend(random.sample(remaining, n_more))
    
    return sample[:sample_size]


def main():
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", help="Diretório com PDFs (recursivo)")
    parser.add_argument("--sample-size", type=int, default=100)
    parser.add_argument("--max-analyze", type=int, default=None, help="Max PDFs para analisar")
    parser.add_argument("--output-dir", default="test_data/sample_pdfs/diverse_100")
    
    args = parser.parse_args()
    
    # Analisar RECURSIVAMENTE
    results = analyze_pdf_directory(args.source_dir, args.max_analyze)
    
    if not results:
        logger.error("❌ Nenhum PDF válido encontrado!")
        return
    
    logger.info(f"\n📦 Total analisado: {len(results)}")
    
    # Criar amostra
    sample = create_diverse_sample(results, args.sample_size)
    
    logger.info(f"\n🎯 Amostra criada: {len(sample)} PDFs")
    
    # Copiar para output
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"\n📁 Copiando arquivos para: {output_path}")
    
    for i, (filepath, rel_path) in enumerate(sample, 1):
        src = Path(filepath)
        # Nome inclui índice + parte do path relativo para identificação
        safe_name = str(rel_path).replace('\\', '_').replace('/', '_')
        dst = output_path / f"sample_{i:03d}_{safe_name}"
        
        # Truncar nome se muito longo
        if len(dst.name) > 200:
            dst = output_path / f"sample_{i:03d}_{src.name}"
        
        try:
            shutil.copy2(src, dst)
        except Exception as e:
            logger.warning(f"   Erro copiando {src.name}: {e}")
            continue
        
        if i % 10 == 0:
            logger.info(f"   Copiado: {i}/{len(sample)}")
    
    logger.info(f"\n✅ CONCLUÍDO!")
    logger.info(f"   Amostra salva em: {output_path}")
    logger.info(f"   Total de arquivos: {len(list(output_path.glob('*.pdf')))}")


if __name__ == "__main__":
    main()
