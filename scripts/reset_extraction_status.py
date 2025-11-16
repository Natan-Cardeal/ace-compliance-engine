from ace.data_model.db import get_connection, DB_PATH


def reset_some_certificates_to_pending(limit: int = 5) -> None:
    """
    Seleciona um lote de certificates que NÃO estão PENDING
    e reseta extraction_status para 'PENDING'.
    Útil para reprocessar com uma nova versão do extractor/OCR.
    """
    conn = get_connection()
    try:
        print(f"Usando banco em: {DB_PATH}")

        rows = conn.execute(
            """
            SELECT id, extraction_status
            FROM certificates
            WHERE extraction_status IS NOT NULL
              AND extraction_status <> 'PENDING'
            ORDER BY id
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        if not rows:
            print("Nenhum certificate elegível para reset.")
            return

        print("Certificates que serão resetados para PENDING:")
        ids = []
        for r in rows:
            print(f"  id={r['id']}  status_atual={r['extraction_status']}")
            ids.append(r["id"])

        conn.executemany(
            """
            UPDATE certificates
               SET extraction_status = 'PENDING'
             WHERE id = ?
            """,
            [(cid,) for cid in ids],
        )
        conn.commit()
        print(f"Resetados {len(ids)} certificates para PENDING.")

    finally:
        conn.close()


if __name__ == "__main__":
    reset_some_certificates_to_pending()
