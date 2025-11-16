import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_DIR = ROOT / "db"
GL_EXPORT_PATH = DB_DIR / "gl_export.csv"


def run():
    if not GL_EXPORT_PATH.exists():
        raise SystemExit(
            f"Arquivo de export GL não encontrado: {GL_EXPORT_PATH}\n"
            f"Rode primeiro o script que gera gl_export.csv."
        )

    status_counter = Counter()
    error_counter = Counter()

    with GL_EXPORT_PATH.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            status = (row.get("extraction_status") or "").upper()
            error = (row.get("extraction_error") or "").strip()
            status_counter[status] += 1
            if error:
                error_counter[error] += 1

    print("=== GL Extraction Summary ===\n")
    print("Por extraction_status:")
    for k, v in status_counter.items():
        print(f"  {k or '(vazio)'}: {v}")

    print("\nTop erros (extraction_error):")
    if not error_counter:
        print("  (nenhum erro registrado)")
    else:
        for err, count in error_counter.most_common(10):
            print(f"  {count:3d}x  {err}")


if __name__ == "__main__":
    run()
