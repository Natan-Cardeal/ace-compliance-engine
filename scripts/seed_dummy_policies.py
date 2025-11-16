from ace.data_model.db import get_connection, DB_PATH


def get_any_certificate_id(conn):
    row = conn.execute(
        "SELECT id FROM certificates ORDER BY id LIMIT 1"
    ).fetchone()
    if not row:
        raise RuntimeError("Nenhum certificate encontrado. Rode o seed_dummy_data primeiro.")
    return row["id"]


def seed_dummy_gl_policy() -> None:
    conn = get_connection()
    try:
        certificate_id = get_any_certificate_id(conn)
        print(f"Usando certificate_id={certificate_id} para criar policy GL dummy.")

        # 1) Insere policy GL
        cur = conn.execute(
            """
            INSERT INTO policies (
                certificate_id,
                lob_code,
                carrier_name,
                policy_number,
                effective_date,
                expiration_date,
                cancellation_notice_days,
                source_method,
                confidence_score
            )
            VALUES (?, ?, ?, ?, date('now'), date('now','+1 year'), ?, 'PARSER', 1.0)
            """,
            (
                certificate_id,
                "GL",
                "DUMMY CARRIER",
                "POL-GL-123",
                30,  # cancellation_notice_days
            ),
        )
        policy_id = cur.lastrowid

        # 2) Insere coverages GL (each occurrence e general aggregate)
        conn.execute(
            """
            INSERT INTO coverages (
                policy_id,
                coverage_code,
                limit_amount,
                limit_currency,
                source_method,
                confidence_score
            )
            VALUES (?, ?, ?, 'USD', 'PARSER', 1.0)
            """,
            (policy_id, "GL_EACH_OCC", 1_000_000.0),
        )

        conn.execute(
            """
            INSERT INTO coverages (
                policy_id,
                coverage_code,
                limit_amount,
                limit_currency,
                source_method,
                confidence_score
            )
            VALUES (?, ?, ?, 'USD', 'PARSER', 1.0)
            """,
            (policy_id, "GL_AGGREGATE", 2_000_000.0),
        )

        conn.commit()
        print(f"Policy GL dummy criada com policy_id={policy_id}.")
    finally:
        conn.close()


if __name__ == "__main__":
    print(f"Usando banco em: {DB_PATH}")
    seed_dummy_gl_policy()
