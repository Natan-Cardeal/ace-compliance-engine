"""
Debug extractions structure
"""

import json
from pathlib import Path

# Pegar o relatório mais recente
reports_dir = Path("reports")
reports = sorted(reports_dir.glob("parser_validation_*.json"), reverse=True)

latest = reports[0]
print(f"📄 Lendo: {latest.name}\n")

with open(latest, 'r', encoding='utf-8') as f:
    data = json.load(f)

extractions = data['extractions']

print(f"Total de extractions: {len(extractions)}\n")

# Mostrar primeira extraction completa
print("=" * 70)
print("PRIMEIRA EXTRACTION:")
print("=" * 70)
print(json.dumps(extractions[0], indent=2))

print("\n" + "=" * 70)
print("KEYS DA PRIMEIRA EXTRACTION:")
print("=" * 70)
print(list(extractions[0].keys()))

# Verificar se tem certificate
has_cert = any(e.get('certificate') for e in extractions)
print(f"\nAlguma extraction tem 'certificate'? {has_cert}")

# Verificar outros campos possíveis
all_keys = set()
for e in extractions:
    all_keys.update(e.keys())

print(f"\nTodos os campos possíveis: {sorted(all_keys)}")
