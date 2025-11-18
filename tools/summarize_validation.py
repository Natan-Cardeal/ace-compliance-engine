"""
Gera relatório resumido da validação
"""

import json
from pathlib import Path
from collections import Counter


def main():
    # Pegar o relatório mais recente
    reports_dir = Path("reports")
    reports = sorted(reports_dir.glob("parser_validation_*.json"), reverse=True)
    
    if not reports:
        print("❌ Nenhum relatório encontrado!")
        return
    
    latest = reports[0]
    print(f"📄 Lendo: {latest.name}\n")
    
    with open(latest, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    extractions = data['extractions']
    files_tested = data['files_tested']
    
    print("=" * 70)
    print("📊 RESUMO EXECUTIVO")
    print("=" * 70)
    print(f"Total testado: {files_tested}")
    
    # Contar sucessos
    success = [e for e in extractions if e.get('status') == 'success']
    failures = [e for e in extractions if e.get('status') != 'success']
    
    print(f"✅ Sucesso: {len(success)} ({len(success)/files_tested*100:.1f}%)")
    print(f"❌ Falhas: {len(failures)}")
    
    if success:
        # Quality média
        qualities = [e['quality_score'] for e in success]
        avg_quality = sum(qualities) / len(qualities)
        print(f"📈 Quality média: {avg_quality:.2f}")
        
        # Coverages média
        coverages = [e['coverages_count'] for e in success]
        avg_cov = sum(coverages) / len(coverages)
        print(f"📦 Coverages média: {avg_cov:.1f}")
    
    print(f"\n{'=' * 70}")
    print("📈 DISTRIBUIÇÃO DE QUALITY")
    print("=" * 70)
    
    quality_buckets = {
        '1.00 (Perfeito)': 0,
        '0.90-0.99': 0,
        '0.83-0.89': 0,
        '0.50-0.82': 0,
        '<0.50': 0
    }
    
    if success:
        for e in success:
            q = e['quality_score']
            if q == 1.00:
                quality_buckets['1.00 (Perfeito)'] += 1
            elif q >= 0.90:
                quality_buckets['0.90-0.99'] += 1
            elif q >= 0.83:
                quality_buckets['0.83-0.89'] += 1
            elif q >= 0.50:
                quality_buckets['0.50-0.82'] += 1
            else:
                quality_buckets['<0.50'] += 1
    
        for bucket, count in quality_buckets.items():
            if count > 0:
                pct = count / len(success) * 100
                print(f"  {bucket}: {count} ({pct:.1f}%)")
    
    print(f"\n{'=' * 70}")
    print("❌ FALHAS")
    print("=" * 70)
    
    if failures:
        for f in failures[:10]:  # Mostrar só as primeiras 10
            filename = Path(f['file']).name
            error = f.get('error', f.get('status', 'Unknown'))
            print(f"  {filename}: {error}")
        if len(failures) > 10:
            print(f"  ... e mais {len(failures) - 10} falhas")
    else:
        print("  ✅ Nenhuma falha!")
    
    print(f"\n{'=' * 70}")
    print("🎯 COVERAGE BREAKDOWN")
    print("=" * 70)
    
    if success:
        coverage_counts = Counter([e['coverages_count'] for e in success])
        
        for cov, count in sorted(coverage_counts.items(), reverse=True):
            pct = count / len(success) * 100
            print(f"  {cov} coverages: {count} ({pct:.1f}%)")
    
    print(f"\n{'=' * 70}")
    print("📄 CAMPOS EXTRAÍDOS")
    print("=" * 70)
    
    if success:
        field_counts = {
            'policy_number': 0,
            'effective_date': 0,
            'expiration_date': 0,
        }
        
        for e in success:
            if e.get('policy_number'):
                field_counts['policy_number'] += 1
            if e.get('effective_date'):
                field_counts['effective_date'] += 1
            if e.get('expiration_date'):
                field_counts['expiration_date'] += 1
        
        for field, count in field_counts.items():
            pct = count / len(success) * 100
            print(f"  {field}: {count} ({pct:.1f}%)")
    
    print(f"\n{'=' * 70}")
    print("💎 TOP 5 MELHORES")
    print("=" * 70)
    
    if success:
        top = sorted(success, key=lambda x: x['quality_score'], reverse=True)[:5]
        for e in top:
            filename = Path(e['file']).name[:50]
            print(f"  {filename}: Q={e['quality_score']:.2f}, Cov={e['coverages_count']}")
    
    print(f"\n{'=' * 70}")
    print("⚠️  TOP 5 PIORES")
    print("=" * 70)
    
    if success:
        bottom = sorted(success, key=lambda x: x['quality_score'])[:5]
        for e in bottom:
            filename = Path(e['file']).name[:50]
            print(f"  {filename}: Q={e['quality_score']:.2f}, Cov={e['coverages_count']}")
    
    print(f"\n{'=' * 70}")
    print("✅ CONCLUSÃO")
    print("=" * 70)
    
    success_rate = len(success) / files_tested * 100
    
    if success_rate == 100:
        print("🎉 PERFEITO! 100% de sucesso!")
    elif success_rate >= 95:
        print("✅ EXCELENTE! Taxa de sucesso > 95%")
    elif success_rate >= 90:
        print("👍 BOM! Taxa de sucesso > 90%")
    else:
        print("⚠️  PRECISA MELHORIAS! Taxa < 90%")
    
    if success:
        if avg_quality >= 0.90:
            print("💎 Quality excelente (>0.90)")
        elif avg_quality >= 0.80:
            print("👍 Quality bom (>0.80)")
        else:
            print("⚠️  Quality precisa melhorias (<0.80)")


if __name__ == "__main__":
    main()
