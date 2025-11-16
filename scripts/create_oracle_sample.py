import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "ace.sqlite"
OUT_PATH = ROOT / "db" / "oracle_samples_gl.csv"


def main() -> None:
    # tamanho da amostra (default = 50 certificados)
    sample_size = 50
    if len(sys.argv) == 2:
        try:
            sample_size = int(sys.argv[1])
        except ValueError:
            print(f"Valor de amostra inválido: {sys.argv[1]!r}, usando default {sample_size}")

    if not DB_PATH.exists():
        raise SystemExit(f"Banco não encontrado: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Importante:
    # - usamos extraction_status (SUCCESS/FAILED/PENDING)
    # - fazemos JOIN com documents pra pegar storage_path
    cur.execute(
        """
        SELECT
            c.id AS certificate_id,
            c.extraction_status,
            d.storage_path
        FROM certificates c
        JOIN documents d ON d.id = c.document_id
        WHERE c.extraction_status IN ('SUCCESS', 'FAILED')
        ORDER BY c.id
        LIMIT ?
        """,
        (sample_size,),
    )
    rows = cur.fetchall()
    conn.close()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["certificate_id", "extraction_status", "storage_path"])
        for certificate_id, extraction_status, storage_path in rows:
            writer.writerow([certificate_id, extraction_status, storage_path])

    print(f"Amostra criada: {len(rows)} certificados salvos em {OUT_PATH}")


if __name__ == "__main__":
    main()
