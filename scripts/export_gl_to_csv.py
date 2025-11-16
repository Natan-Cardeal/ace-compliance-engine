import csv
from pathlib import Path

from ace.data_model.db import get_connection, DB_PATH


OUTPUT_PATH = Path("db") / "gl_export.csv"


def export_gl_to_csv() -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        print(f"Usando banco em: {DB_PATH}")
        print(f"Exportando GL para: {OUTPUT_PATH}\n")

        # Cabeçalho do CSV
        fieldnames = [
            "certificate_id",
            "extraction_status",
            "ocr_provider",
            "file_path",
            "policy_number",
            "effective_date",
            "expiration_date",
            "GL_EACH_OCC",
            "GL_AGGREGATE",
            "GL_PERS_ADV",
            "GL_PROD_AGG",
            "GL_DAMAGE_PREM",
            "GL_MED_EXP",
        ]

        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

        with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            # Busca todos os certificates
            certs = cur.execute(
                """
                SELECT c.id AS certificate_id,
                       c.extraction_status,
                       d.storage_path,
                       p.id AS policy_id,
                       p.policy_number,
                       p.effective_date,
                       p.expiration_date,
                       (
                           SELECT er.ocr_provider
                             FROM extraction_runs er
                            WHERE er.document_id = d.id
                            ORDER BY er.id DESC
                            LIMIT 1
                       ) AS ocr_provider
                  FROM certificates c
                  JOIN documents d ON d.id = c.document_id
                  LEFT JOIN policies p
                         ON p.certificate_id = c.id
                        AND p.lob_code = 'GL'
                 ORDER BY c.id
                """
            ).fetchall()

            for cert in certs:
                cid = cert["certificate_id"]
                policy_id = cert["policy_id"]

                cov_map = {
                    "GL_EACH_OCC": None,
                    "GL_AGGREGATE": None,
                    "GL_PERS_ADV": None,
                    "GL_PROD_AGG": None,
                    "GL_DAMAGE_PREM": None,
                    "GL_MED_EXP": None,
                }

                if policy_id is not None:
                    covs = cur.execute(
                        """
                        SELECT coverage_code, limit_amount
                          FROM coverages
                         WHERE policy_id = ?
                           AND coverage_code IN (
                                'GL_EACH_OCC',
                                'GL_AGGREGATE',
                                'GL_PERS_ADV',
                                'GL_PROD_AGG',
                                'GL_DAMAGE_PREM',
                                'GL_MED_EXP'
                           )
                        """,
                        (policy_id,),
                    ).fetchall()
                    for c in covs:
                        cov_map[c["coverage_code"]] = c["limit_amount"]

                row = {
                    "certificate_id": cid,
                    "extraction_status": cert["extraction_status"],
                    "ocr_provider": cert["ocr_provider"],
                    "file_path": cert["storage_path"],
                    "policy_number": cert["policy_number"],
                    "effective_date": cert["effective_date"],
                    "expiration_date": cert["expiration_date"],
                }
                row.update(cov_map)
                writer.writerow(row)

        print("Exportação concluída.")

    finally:
        conn.close()


if __name__ == "__main__":
    export_gl_to_csv()
