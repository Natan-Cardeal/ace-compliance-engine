import csv
import sqlite3
from pathlib import Path

# Raiz do projeto ACE
ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "ace.sqlite"
EXPORT_DIR = ROOT / "db" / "exports"


def export_all_tables():
    if not DB_PATH.exists():
        raise SystemExit(f"Banco de dados não encontrado: {DB_PATH}")

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Lista todas as tabelas do SQLite (exceto internas)
    cur.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name"
    )
    tables = [r["name"] for r in cur.fetchall()]

    print(f"Encontradas {len(tables)} tabelas:\n  " + ', '.join(tables) + "\n")

    for table in tables:
        out_path = EXPORT_DIR / f"{table}.csv"
        print(f"Exportando tabela {table} -> {out_path}")

        cur.execute(f"SELECT * FROM {table}")
        rows = cur.fetchall()
        if not rows:
            # ainda assim escreve header
            col_names = [d[0] for d in cur.description]
            with out_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(col_names)
            continue

        col_names = rows[0].keys()
        with out_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(col_names)
            for row in rows:
                writer.writerow([row[c] for c in col_names])

    conn.close()
    print("\nExport finalizado. Arquivos em:", EXPORT_DIR)


if __name__ == "__main__":
    export_all_tables()
