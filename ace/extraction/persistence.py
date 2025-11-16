from __future__ import annotations

from typing import Optional

from ace.data_model.db import get_connection
from ace.extraction.models import ExtractedCOI


def persist_extracted_coi(
    extracted: ExtractedCOI,
    extraction_run_id: Optional[int] = None,
) -> None:
    """
    Persiste o resultado de extração de um COI:

      - Limpa policies / coverages / clauses antigos desse certificate_id
      - Insere uma nova "fotografia" de policies + coverages + clauses
    """
    certificate_id = extracted.certificate_id

    conn = get_connection()
    try:
        cur = conn.cursor()

        # 1) Apagar dados antigos ligados a esse certificate
        cur.execute(
            """
            DELETE FROM policy_clauses
             WHERE policy_id IN (
                   SELECT id FROM policies WHERE certificate_id = ?
             )
            """,
            (certificate_id,),
        )

        cur.execute(
            """
            DELETE FROM coverages
             WHERE policy_id IN (
                   SELECT id FROM policies WHERE certificate_id = ?
             )
            """,
            (certificate_id,),
        )

        cur.execute(
            "DELETE FROM policies WHERE certificate_id = ?",
            (certificate_id,),
        )

        # 2) Inserir novas policies
        policy_id_map: dict[int, int] = {}  # policy_index -> policy_id

        for idx, p in enumerate(extracted.policies):
            cur.execute(
                """
                INSERT INTO policies (
                    certificate_id,
                    lob_code,
                    carrier_name,
                    policy_number,
                    effective_date,
                    expiration_date,
                    cancellation_notice_days
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    certificate_id,
                    p.lob_code,
                    p.carrier_name,
                    p.policy_number,
                    p.effective_date,
                    p.expiration_date,
                    p.cancellation_notice_days,
                ),
            )
            policy_id = cur.lastrowid
            policy_id_map[idx] = policy_id

        # 3) Inserir coverages
        for c in extracted.coverages:
            policy_id = policy_id_map[c.policy_index]
            cur.execute(
                """
                INSERT INTO coverages (
                    policy_id,
                    coverage_code,
                    limit_amount,
                    limit_currency,
                    deductible_amount,
                    deductible_currency
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    policy_id,
                    c.coverage_code,
                    c.limit_amount,
                    c.limit_currency,
                    c.deductible_amount,
                    c.deductible_currency,
                ),
            )

        # 4) Inserir clauses (se houver)
        for cl in extracted.clauses:
            policy_id = policy_id_map[cl.policy_index]
            cur.execute(
                """
                INSERT INTO policy_clauses (
                    policy_id,
                    clause_code,
                    clause_text
                )
                VALUES (?, ?, ?)
                """,
                (
                    policy_id,
                    cl.clause_code,
                    cl.clause_text,
                ),
            )

        conn.commit()
    finally:
        conn.close()
