from pathlib import Path
import sqlite3
from typing import Iterator


# ACE/ace/data_model/db.py -> parents[0]=data_model, [1]=ace, [2]=ACE (raiz do projeto)
REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "db" / "ace.sqlite"


def get_connection() -> sqlite3.Connection:
    """
    Abre uma conexão com o banco SQLite do ACE.
    Usa row_factory=sqlite3.Row para acessar colunas por nome.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def iter_rows(cursor: sqlite3.Cursor) -> Iterator[sqlite3.Row]:
    """
    Helper simples para iterar sobre resultados com tipagem.
    """
    for row in cursor:
        yield row
