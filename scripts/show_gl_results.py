from ace.data_model.db import get_connection, DB_PATH


def show_gl_results(certificate_ids: list[int] | None = None, limit: int = 20) -> None:
    """
    Mostra um resumo de GL para alguns certificates:
      - extraction_status
      - ocr_provider do último extraction_run
      - metadados da policy GL (policy_number, datas)
      - coverages GL principais (todos os sub-limits mapeados)
    """
    conn = get_connection()
    try:
        print(f"Usando banco em: {DB_PATH}\n")

        if not certificate_ids:
            rows = conn.execute(
                """
                SELECT id
                  FROM certificates
                 WHERE extraction_status = 'SUCCESS'
                 ORDER BY id
                 LIMIT ?
                """,
                (limit,),
            ).fetchall()
            certificate_ids = [r["id"] for r in rows]

        for cid in certificate_ids:
            cert = conn.execute(
                """
                SELECT c.id,
                       c.extraction_status,
                       d.id AS document_id,
                       d.storage_path
                  FROM certificates c
                  JOIN documents d ON d.id = c.document_id
                 WHERE c.id = ?
                """,
                (cid,),
            ).fetchone()

            if not cert:
                print(f"Certificate {cid} não encontrado.")
                print("-" * 60)
                continue

            er = conn.execute(
                """
                SELECT ocr_provider, status
                  FROM extraction_runs
                 WHERE document_id = ?
                 ORDER BY id DESC
                 LIMIT 1
                """,
                (cert["document_id"],),
            ).fetchone()

            ocr_provider = er["ocr_provider"] if er else None
            run_status = er["status"] if er else None

            # Policy GL principal
            policy = conn.execute(
                """
                SELECT id,
                       carrier_name,
                       policy_number,
                       effective_date,
                       expiration_date
                  FROM policies
                 WHERE certificate_id = ?
                   AND lob_code = 'GL'
                 ORDER BY id
                 LIMIT 1
                """,
                (cid,),
            ).fetchone()

            # Coverages GL (todos códigos relevantes)
            covs = conn.execute(
                """
                SELECT cv.coverage_code, cv.limit_amount, cv.limit_currency
                  FROM coverages cv
                  JOIN policies p ON p.id = cv.policy_id
                 WHERE p.certificate_id = ?
                   AND p.lob_code = 'GL'
                   AND cv.coverage_code IN (
                        'GL_EACH_OCC',
                        'GL_AGGREGATE',
                        'GL_PERS_ADV',
                        'GL_PROD_AGG',
                        'GL_DAMAGE_PREM',
                        'GL_MED_EXP'
                   )
                 ORDER BY cv.coverage_code
                """,
                (cid,),
            ).fetchall()

            print(f"Certificate {cert['id']}")
            print(f"  extraction_status: {cert['extraction_status']}")
            print(f"  último extraction_run.status: {run_status}")
            print(f"  ocr_provider: {ocr_provider}")
            print(f"  arquivo: {cert['storage_path']}")

            if policy:
                print("  Policy GL:")
                print(f"    policy_number:   {policy['policy_number']}")
                print(f"    effective_date:  {policy['effective_date']}")
                print(f"    expiration_date: {policy['expiration_date']}")
            else:
                print("  Policy GL: (nenhuma policy encontrada)")

            if not covs:
                print("  GL coverages: (nenhuma encontrada)")
            else:
                print("  GL coverages:")
                for c in covs:
                    print(
                        f"    {c['coverage_code']}: {c['limit_amount']} {c['limit_currency']}"
                    )

            print("-" * 60)

    finally:
        conn.close()


if __name__ == "__main__":
    ids = [30, 31, 32, 33, 34]
    show_gl_results(certificate_ids=ids)

