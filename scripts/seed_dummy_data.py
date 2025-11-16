from pathlib import Path
import hashlib

from ace.data_model.db import get_connection, DB_PATH


def seed_dummy_certificate() -> None:
    """
    Cria um document + certificate de teste.
    Não precisa existir um PDF real ainda; usamos um caminho fictício.
    """
    repo_root = DB_PATH.parent  # ...\ACE\db -> parent é ...\ACE
    fake_pdf_path = repo_root / "docs" / "example_coi.pdf"

    # Hash só pra ter algo estável
    file_hash = hashlib.sha256(str(fake_pdf_path).encode("utf-8")).hexdigest()

    conn = get_connection()
    try:
        # 1) Insere (ou reaproveita) document
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO documents (file_hash, storage_path, doc_type, source_system)
            VALUES (?, ?, ?, ?)
            """,
            (file_hash, str(fake_pdf_path), "COI_ACORD25", "MANUAL_SEED"),
        )

        if cur.lastrowid:
            document_id = cur.lastrowid
        else:
            row = conn.execute(
                "SELECT id FROM documents WHERE file_hash = ?",
                (file_hash,),
            ).fetchone()
            document_id = row["id"]

        # 2) Insere certificate ligado a esse document
        cur = conn.execute(
            """
            INSERT INTO certificates (document_id, client_id, project_id, vendor_id, certificate_date)
            VALUES (?, ?, ?, ?, date('now'))
            """,
            (document_id, 1, 1, 1),
        )
        certificate_id = cur.lastrowid

        conn.commit()
        print(f"Seed criado com sucesso. certificate_id = {certificate_id}")
    finally:
        conn.close()


if __name__ == "__main__":
    print(f"Usando banco em: {DB_PATH}")
    seed_dummy_certificate()
