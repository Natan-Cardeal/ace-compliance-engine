import sys

from ace.data_model.db import get_connection, DB_PATH
from ace.extraction.runner import run_extraction_for_certificate


def process_extraction_queue(batch_size: int = 10) -> None:
    """
    Pega um lote de certificates com extraction_status = 'PENDING'
    e roda o pipeline de extração para cada um.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id
            FROM certificates
            WHERE extraction_status = 'PENDING'
            ORDER BY id
            LIMIT ?
            """,
            (batch_size,),
        ).fetchall()

        certificate_ids = [row["id"] for row in rows]

    finally:
        conn.close()

    if not certificate_ids:
        print("Nenhum certificate PENDING encontrado.")
        return

    print(f"Processando {len(certificate_ids)} certificados: {certificate_ids}")

    for cid in certificate_ids:
        try:
            run_extraction_for_certificate(cid)
        except Exception as e:
            # MVP: loga e continua
            print(f"[ERRO] Falha ao extrair certificate {cid}: {e}")


def main() -> None:
    batch_size = 10
    if len(sys.argv) >= 2:
        batch_size = int(sys.argv[1])

    print(f"Usando banco em: {DB_PATH}")
    process_extraction_queue(batch_size=batch_size)


if __name__ == "__main__":
    main()
