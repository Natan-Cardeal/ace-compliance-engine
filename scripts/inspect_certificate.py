import sys

from ace.data_model.db import get_connection, DB_PATH


def inspect_certificate(certificate_id: int) -> None:
    conn = get_connection()
    try:
        cert = conn.execute(
            """
            SELECT c.id,
                   c.certificate_status,
                   c.extraction_status,
                   d.storage_path
            FROM certificates c
            JOIN documents d ON d.id = c.document_id
            WHERE c.id = ?
            """,
            (certificate_id,),
        ).fetchone()

        if not cert:
            print(f"Certificate {certificate_id} não encontrado.")
            return

        print(f"Certificate {cert['id']}")
        print(f"  status: {cert['certificate_status']}")
        print(f"  extraction_status: {cert['extraction_status']}")
        print(f"  arquivo: {cert['storage_path']}")
        print()

        print("Policies:")
        policies = conn.execute(
            """
            SELECT id, lob_code, carrier_name, policy_number,
                   effective_date, expiration_date
            FROM policies
            WHERE certificate_id = ?
            ORDER BY id
            """,
            (certificate_id,),
        ).fetchall()

        if not policies:
            print("  (nenhuma policy)")
            return

        for p in policies:
            print(f"  Policy {p['id']} [{p['lob_code']}]")
            print(f"    carrier: {p['carrier_name']}")
            print(f"    policy_number: {p['policy_number']}")
            print(f"    effective: {p['effective_date']}  expiration: {p['expiration_date']}")

            covs = conn.execute(
                """
                SELECT coverage_code, limit_amount, limit_currency
                FROM coverages
                WHERE policy_id = ?
                ORDER BY coverage_code
                """,
                (p["id"],),
            ).fetchall()

            if not covs:
                print("    coverages: (nenhuma)")
            else:
                print("    coverages:")
                for c in covs:
                    print(f"      {c['coverage_code']}: {c['limit_amount']} {c['limit_currency']}")
            print()

    finally:
        conn.close()


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: py scripts\\inspect_certificate.py <certificate_id>")
        raise SystemExit(1)

    certificate_id = int(sys.argv[1])
    print(f"Usando banco em: {DB_PATH}")
    inspect_certificate(certificate_id)


if __name__ == "__main__":
    main()
