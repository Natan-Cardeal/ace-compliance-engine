from ace.data_model.db import get_connection, DB_PATH


def list_pdfs_for_upload(limit_success: int = 5, limit_failed: int = 5) -> None:
    conn = get_connection()
    try:
        print(f"Usando banco em: {DB_PATH}\n")

        print("=== Samples SUCCESS (extração OK) ===")
        rows = conn.execute(
            """
            SELECT c.id,
                   c.extraction_status,
                   d.storage_path
            FROM certificates c
            JOIN documents d ON d.id = c.document_id
            WHERE c.extraction_status = 'SUCCESS'
            ORDER BY c.id
            LIMIT ?
            """,
            (limit_success,),
        ).fetchall()

        if not rows:
            print("  (nenhum SUCCESS ainda)")
        else:
            for r in rows:
                print(f"  certificate_id={r['id']}")
                print(f"    status: {r['extraction_status']}")
                print(f"    arquivo: {r['storage_path']}")
                print()

        print("\n=== Samples FAILED (para debug) ===")
        rows = conn.execute(
            """
            SELECT c.id,
                   c.extraction_status,
                   d.storage_path
            FROM certificates c
            JOIN documents d ON d.id = c.document_id
            WHERE c.extraction_status LIKE 'FAILED%'
            ORDER BY c.id
            LIMIT ?
            """,
            (limit_failed,),
        ).fetchall()

        if not rows:
            print("  (nenhum FAILED ainda)")
        else:
            for r in rows:
                print(f"  certificate_id={r['id']}")
                print(f"    status: {r['extraction_status']}")
                print(f"    arquivo: {r['storage_path']}")
                print()

    finally:
        conn.close()


if __name__ == "__main__":
    list_pdfs_for_upload()
