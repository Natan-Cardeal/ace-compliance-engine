from typing import Dict, Any, Optional

from ace.data_model.db import get_connection


def _get_requirement_gl(conn, client_id: int, project_id: int) -> Optional[Dict[str, Any]]:
    """
    Pega um requirement GL ativo para esse client/project.
    MVP: pega o primeiro que bater.
    """
    row = conn.execute(
        """
        SELECT *
        FROM coverage_requirements
        WHERE lob_code = 'GL'
          AND is_active = 1
          AND client_id = ?
          AND project_id = ?
        ORDER BY effective_from DESC
        LIMIT 1
        """,
        (client_id, project_id),
    ).fetchone()

    return dict(row) if row else None


def _get_gl_limits_from_certificate(conn, certificate_id: int) -> Optional[Dict[str, float]]:
    """
    Encontra os limites GL_EACH_OCC e GL_AGGREGATE do certificado.
    MVP: pega o primeiro policy GL e seus coverages.
    """
    policy = conn.execute(
        """
        SELECT id
        FROM policies
        WHERE certificate_id = ?
          AND lob_code = 'GL'
        ORDER BY id
        LIMIT 1
        """,
        (certificate_id,),
    ).fetchone()

    if not policy:
        return None

    policy_id = policy["id"]

    rows = conn.execute(
        """
        SELECT coverage_code, limit_amount
        FROM coverages
        WHERE policy_id = ?
          AND coverage_code IN ('GL_EACH_OCC', 'GL_AGGREGATE')
        """,
        (policy_id,),
    ).fetchall()

    limits = {}
    for r in rows:
        limits[r["coverage_code"]] = r["limit_amount"]

    if not limits:
        return None

    return limits


def evaluate_gl_for_certificate(certificate_id: int) -> None:
    """
    Avalia GL para um certificate_id:
    - Busca client_id/project_id
    - Pega requirement GL
    - Pega limites GL do COI
    - Compara e grava em compliance_evaluation
    """
    conn = get_connection()
    try:
        cert = conn.execute(
            """
            SELECT id, client_id, project_id
            FROM certificates
            WHERE id = ?
            """,
            (certificate_id,),
        ).fetchone()

        if not cert:
            raise ValueError(f"Certificate {certificate_id} não encontrado.")

        client_id = cert["client_id"]
        project_id = cert["project_id"]

        requirement = _get_requirement_gl(conn, client_id, project_id)
        if not requirement:
            print(f"Nenhum requirement GL encontrado para client={client_id}, project={project_id}.")
            status = "NOT_EVALUATED"
            gap_count = 1
            gap_summary = "NO_REQUIREMENT_FOUND"
            requirement_id = None
        else:
            limits = _get_gl_limits_from_certificate(conn, certificate_id)
            if not limits:
                print(f"Nenhuma coverage GL encontrada para certificate={certificate_id}.")
                status = "NOT_EVALUATED"
                gap_count = 1
                gap_summary = "NO_GL_COVERAGE_FOUND"
                requirement_id = requirement["id"]
            else:
                gaps = []

                each_min = requirement.get("gl_each_occurrence_min") or 0
                agg_min = requirement.get("gl_general_aggregate_min") or 0

                each_val = limits.get("GL_EACH_OCC") or 0
                agg_val = limits.get("GL_AGGREGATE") or 0

                if each_val < each_min:
                    gaps.append(f"EACH_OCCURRENCE_BELOW_MIN ({each_val} < {each_min})")

                if agg_val < agg_min:
                    gaps.append(f"AGGREGATE_BELOW_MIN ({agg_val} < {agg_min})")

                if gaps:
                    status = "NON_COMPLIANT"
                    gap_summary = "; ".join(gaps)
                else:
                    status = "COMPLIANT"
                    gap_summary = "OK"

                gap_count = len(gaps)
                requirement_id = requirement["id"]

        # Grava em compliance_evaluation
        conn.execute(
            """
            INSERT INTO compliance_evaluation (
                certificate_id,
                lob_code,
                engine_version,
                requirement_id,
                status,
                gap_count,
                gap_summary,
                expiration_risk
            )
            VALUES (?, 'GL', ?, ?, ?, ?, ?, ?)
            """,
            (
                certificate_id,
                "engine_gl_v0",
                requirement_id,
                status,
                gap_count,
                gap_summary,
                None,  # expiration_risk ainda não calculado
            ),
        )

        conn.commit()
        print(f"Avaliação GL para certificate {certificate_id}: {status} (gaps={gap_count})")

    finally:
        conn.close()
