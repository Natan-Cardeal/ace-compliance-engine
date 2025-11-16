import csv
import json
import os
import sys
import sqlite3
import textwrap
from typing import Dict, Any, List

import requests

# Caminhos principais
DB_PATH = os.path.join("db", "ace.sqlite")
SAMPLES_PATH = os.path.join("db", "oracle_samples_gl.csv")
OUTPUT_PATH = os.path.join("db", "gl_ground_truth.csv")

API_URL = "https://api.anthropic.com/v1/messages"


def get_db_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def load_sample_ids(limit: int | None = None) -> list[int]:
    if not os.path.exists(SAMPLES_PATH):
        raise FileNotFoundError(f"Arquivo de amostra não encontrado: {SAMPLES_PATH}")

    with open(SAMPLES_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    ids: list[int] = []
    for r in rows:
        raw = r.get("certificate_id") or r.get("id")
        if not raw:
            continue
        try:
            ids.append(int(raw))
        except ValueError:
            continue

    if limit is not None:
        ids = ids[:limit]
    return ids


def get_storage_path(conn: sqlite3.Connection, cert_id: int) -> str:
    cur = conn.cursor()
    cur.execute("SELECT storage_path FROM certificates WHERE id = ?", (cert_id,))
    row = cur.fetchone()
    if not row or not row[0]:
        raise RuntimeError(f"Sem storage_path para certificate_id={cert_id}")
    path = row[0]
    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)
    return path


# Reaproveita o mesmo extrator usado no ACE
from ace.extraction.layout import extract_text_from_pdf


def get_pdf_text(path: str) -> str:
    pages: List[str] = extract_text_from_pdf(path)
    if not pages:
        raise RuntimeError("Nenhum texto retornado pelo OCR/layout")

    # ACORD 25 costuma ser 1 página; para segurança, usamos no máximo 2
    text = "\n\n".join(pages[:2])
    text = text.replace("\x00", "")
    return text


def call_llm(text: str, certificate_id: int) -> Dict[str, Any]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY não configurada no ambiente")

    # Modelo configurável; default para o Sonnet 4.5 que você pediu
    model = os.environ.get("ACE_ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")

    system_prompt = (
        "Você é um especialista em seguros P&C dos EUA e em leitura de Certificates "
        "of Insurance (ACORD 25). Receberá o texto extraído de um COI (1–2 páginas) "
        "e deve extrair APENAS os campos de GENERAL LIABILITY:\n"
        "- policy_number: número da apólice de GL\n"
        "- effective_date: data de início da apólice GL no formato YYYY-MM-DD\n"
        "- expiration_date: data de expiração da apólice GL no formato YYYY-MM-DD\n"
        "- gl_aggregate: limite GENERAL AGGREGATE em dólares (somente dígitos)\n"
        "- gl_each_occurrence: limite EACH OCCURRENCE em dólares (somente dígitos)\n\n"
        "Se não tiver certeza de um valor, retorne null para esse campo e explique em 'notes'. "
        "Nunca invente limites ou datas. O resultado DEVE ser um único objeto JSON válido."
    )

    user_text = textwrap.dedent(
        f"""
        Texto completo do certificado (certificate_id={certificate_id}):

        {text}

        Retorne APENAS o objeto JSON com os campos:
        policy_number, effective_date, expiration_date,
        gl_aggregate, gl_each_occurrence, notes
        """
    )

    payload: Dict[str, Any] = {
        "model": model,
        "max_tokens": 400,
        "temperature": 0,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                ],
            }
        ],
    }

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    resp = requests.post(API_URL, headers=headers, json=payload, timeout=90)
    resp.raise_for_status()
    data = resp.json()

    # Conteúdo principal da resposta
    content = data["content"][0]["text"]

    try:
        obj = json.loads(content)
        if not isinstance(obj, dict):
            raise ValueError("Resposta JSON não é um objeto")
        return obj
    except Exception as e:
        raise RuntimeError(f"Falha ao parsear JSON: {e}. Resposta bruta: {content[:400]!r}")


def main() -> None:
    sample_size = int(sys.argv[1]) if len(sys.argv) >= 2 else None

    cert_ids = load_sample_ids(sample_size)
    print(f"Gerando ground truth GL para {len(cert_ids)} certificados...")
    os.makedirs("db", exist_ok=True)

    fieldnames = [
        "certificate_id",
        "policy_number",
        "effective_date",
        "expiration_date",
        "gl_aggregate",
        "gl_each_occurrence",
        "notes",
        "_llm_error",
        "_parse_error",
    ]

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f_out, get_db_connection() as conn:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        total = len(cert_ids)
        for idx, cert_id in enumerate(cert_ids, start=1):
            print(f"[{idx}/{total}] certificate_id={cert_id}...")

            row_out: Dict[str, Any] = {
                "certificate_id": cert_id,
                "policy_number": None,
                "effective_date": None,
                "expiration_date": None,
                "gl_aggregate": None,
                "gl_each_occurrence": None,
                "notes": "",
                "_llm_error": "",
                "_parse_error": "",
            }

            # 1) Carregar PDF e extrair texto
            try:
                pdf_path = get_storage_path(conn, cert_id)
                text = get_pdf_text(pdf_path)
            except Exception as e:
                row_out["_parse_error"] = f"Erro ao carregar/ler PDF: {e}"
                writer.writerow(row_out)
                continue

            # 2) Chamar o LLM
            try:
                llm_obj = call_llm(text, cert_id)
                for key in [
                    "policy_number",
                    "effective_date",
                    "expiration_date",
                    "gl_aggregate",
                    "gl_each_occurrence",
                    "notes",
                ]:
                    if key in llm_obj:
                        row_out[key] = llm_obj[key]
            except Exception as e:
                row_out["_llm_error"] = str(e)

            writer.writerow(row_out)

    print(f"Ground truth GL salvo em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
