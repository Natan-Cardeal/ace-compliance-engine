from ace.data_model.db import get_connection, DB_PATH


def seed_dummy_gl_requirement() -> None:
    """
    Cria um requirement GL simples para client_id=1, project_id=1.
    """
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO coverage_requirements (
                client_id,
                project_id,
                property_id,
                lob_code,
                requirement_scope,
                requirement_name,
                effective_from,
                effective_to,
                is_active,
                gl_each_occurrence_min,
                gl_general_aggregate_min,
                auto_csl_min,
                requires_wc_coverage,
                employers_liability_each_acc_min,
                requires_additional_insured,
                requires_waiver_subrogation,
                requires_primary_non_contributory,
                requirement_notes,
                created_by
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, date('now'), NULL, 1,
                ?, ?, NULL, 0, NULL,
                0, 0, 0,
                ?, ?
            )
            """,
            (
                1,          # client_id
                1,          # project_id
                None,       # property_id
                "GL",       # lob_code
                "PROJECT",  # requirement_scope
                "Requirement GL padrão projeto 1",
                1_000_000.0,   # gl_each_occurrence_min
                2_000_000.0,   # gl_general_aggregate_min
                "MVP seed requirement",
                "system_seed",
            ),
        )
        conn.commit()
        print("Requirement GL dummy criado com sucesso.")
    finally:
        conn.close()


if __name__ == "__main__":
    print(f"Usando banco em: {DB_PATH}")
    seed_dummy_gl_requirement()
