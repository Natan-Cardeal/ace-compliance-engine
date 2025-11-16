from ace.data_model.db import get_connection, DB_PATH


def main() -> None:
    conn = get_connection()
    try:
        print(f"Usando banco em: {DB_PATH}\n")

        # 1) Quantos certificados por status
        rows = conn.execute(
            """
            SELECT extraction_status, COUNT(*) as total
              FROM certificates
             GROUP BY extraction_status
             ORDER BY extraction_status
            """
        ).fetchall()

        print("== Certificates por extraction_status ==")
        for r in rows:
            print(f"  {r['extraction_status']}: {r['total']}")
        print()

        # 2) Quantos têm GL com EACH_OCC + AGG
        total = conn.execute("SELECT COUNT(*) AS c FROM certificates").fetchone()["c"]

        gl_ok = conn.execute(
            """
            SELECT COUNT(DISTINCT c.id) AS c
              FROM certificates c
              JOIN policies p ON p.certificate_id = c.id AND p.lob_code = 'GL'
              JOIN coverages cv1 ON cv1.policy_id = p.id AND cv1.coverage_code = 'GL_EACH_OCC'
              JOIN coverages cv2 ON cv2.policy_id = p.id AND cv2.coverage_code = 'GL_AGGREGATE'
            """
        ).fetchone()["c"]

        print("== Cobertura GL extraída (EACH_OCC + AGG) ==")
        print(f"  Certificates com GL (EACH_OCC & AGG): {gl_ok}")
        print(f"  Total de certificates:                 {total}")
        if total:
            pct = 100.0 * gl_ok / total
            print(f"  Cobertura GL (%%):                     {pct:.1f}%")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
