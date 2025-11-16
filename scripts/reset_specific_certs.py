from ace.data_model.db import get_connection, DB_PATH


def reset_certificates(ids):
    conn = get_connection()
    try:
        print(f"Usando banco em: {DB_PATH}")
        print("Resetando certificates para PENDING:", ids)

        conn.executemany(
            "UPDATE certificates SET extraction_status = 'PENDING' WHERE id = ?",
            [(cid,) for cid in ids],
        )
        conn.commit()
        print("Done.")
    finally:
        conn.close()


if __name__ == "__main__":
    # 👇 escolha aqui os IDs que você quer reprocessar com o novo OCR
    # pelos seus logs anteriores, 2,3,4,6,7 são SUCCESS GL bonitos
    ids = [2, 3, 4, 6, 7]
    reset_certificates(ids)
