import csv
import os
import sys
import sqlite3
from typing import List

DB_PATH = os.path.join("db", "ace.sqlite")
SAMPLES_PATH = os.path.join("db", "oracle_samples_gl.csv")


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def create_sample(sample_size: int) -> None:
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Banco não encontrado: {DB_PATH}")

    with get_connection() as conn:
        cur = conn.cursor()
        # Pegamos só certificados com GL extraído com sucesso
        cur.execute(
            """
            SELECT id AS certificate_id
            FROM certificates
            WHERE extraction_status = 'SUCCESS'
            ORDER BY id
            LIMIT ?
            """,
            (sample_size,),
        )
        rows = cur.fetchall()

    os.makedirs(os.path.dirname(SAMPLES_PATH), exist_ok=True)

    with open(SAMPLES_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["certificate_id"])
        writer.writeheader()
        for (cid,) in rows:
            writer.writerow({"certificate_id": cid})

    print(f"Criado arquivo de amostra: {SAMPLES_PATH}")
    print(f"Total de certificados na amostra: {len(rows)}")


def main() -> None:
    sample_size = int(sys.argv[1]) if len(sys.argv) >= 2 else 50
    create_sample(sample_size)


if __name__ == "__main__":
    main()
