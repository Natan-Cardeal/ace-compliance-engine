from ace.data_model.db import get_connection
from .ocr import extract_text_with_ocr, OcrMode
from .parser_acord25 import parse_acord25_gl_limits
from .persistence import persist_extracted_coi


def run_extraction_for_certificate(certificate_id: int) -> None:
    """
    Pipeline de extração para um certificate_id:
      1) Busca document + storage_path
      2) Cria extraction_run (status=STARTED)
      3) Extrai texto do PDF com OCR obrigatório
      4) Roda parser ACORD 25 (GL)
      5) Persiste resultado
      6) Atualiza extraction_status em certificates
    """
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT c.id AS certificate_id,
                   d.id AS document_id,
                   d.storage_path
            FROM certificates c
            JOIN documents d ON d.id = c.document_id
            WHERE c.id = ?
            """,
            (certificate_id,),
        ).fetchone()

        if not row:
            raise ValueError(f"Certificate {certificate_id} não encontrado.")

        document_id = row["document_id"]
        storage_path = row["storage_path"]

        # 1) Cria extraction_run com status STARTED
        cur = conn.execute(
            """
            INSERT INTO extraction_runs (
                document_id,
                run_type,
                ocr_provider,
                parser_version,
                ml_model_version,
                started_at,
                status
            )
            VALUES (?, ?, ?, ?, ?, datetime('now'), ?)
            """,
            (document_id, "INITIAL", None, "parser_acord25_v0", None, "STARTED"),
        )
        extraction_run_id = cur.lastrowid
        conn.commit()

    finally:
        conn.close()

    # 2) Extrai texto com OCR obrigatório (Tesseract)
    try:
        ocr_result = extract_text_with_ocr(storage_path, mode=OcrMode.REQUIRED)
        pages = ocr_result.pages
        ocr_provider = ocr_result.provider
    except Exception as e:
        # Se OCR falhar, marca extraction_run/certificate como FAILED_OCR
        conn = get_connection()
        try:
            conn.execute(
                """
                UPDATE extraction_runs
                   SET status = ?, finished_at = datetime('now'), ocr_provider = ?
                 WHERE id = ?
                """,
                ("FAILED_OCR", "TESSERACT", extraction_run_id),
            )
            conn.execute(
                """
                UPDATE certificates
                   SET extraction_status = ?
                 WHERE id = ?
                """,
                ("FAILED", certificate_id),
            )
            conn.commit()
        finally:
            conn.close()

        print(f"[extractor] Falha de OCR para certificate {certificate_id}: {e}")
        return

    # 3) Parser ACORD 25 GL sobre texto já OCRizado
    extracted = parse_acord25_gl_limits(certificate_id, pages)

    if extracted is None:
        # Não conseguiu extrair limites GL mesmo após OCR
        conn = get_connection()
        try:
            conn.execute(
                """
                UPDATE extraction_runs
                   SET status = ?, finished_at = datetime('now'), ocr_provider = ?
                 WHERE id = ?
                """,
                ("FAILED_NO_GL_LIMITS", ocr_provider, extraction_run_id),
            )
            conn.execute(
                """
                UPDATE certificates
                   SET extraction_status = ?
                 WHERE id = ?
                """,
                ("FAILED", certificate_id),
            )
            conn.commit()
        finally:
            conn.close()

        print(f"[extractor] Não foi possível encontrar limites GL no certificate {certificate_id}.")
        return

    # 4) Persistir resultado (policies/coverages) vinculados ao extraction_run
    persist_extracted_coi(extracted, extraction_run_id=extraction_run_id)

    # 5) Atualizar extraction_run + certificate como SUCCESS
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE extraction_runs
               SET status = ?, finished_at = datetime('now'), ocr_provider = ?
             WHERE id = ?
            """,
            ("SUCCESS", ocr_provider, extraction_run_id),
        )
        conn.execute(
            """
            UPDATE certificates
               SET extraction_status = ?
             WHERE id = ?
            """,
            ("SUCCESS", certificate_id),
        )
        conn.commit()
    finally:
        conn.close()

    print(f"[extractor] Extração GL concluída com sucesso (OCR={ocr_provider}) para certificate {certificate_id}.")
