"""
Parser ACORD 25 – foco em linha de Commercial General Liability (GL).

Responsável por:
- localizar a linha GL no formulário;
- extrair número da apólice, datas de vigência;
- extrair limites principais de GL:
  - EACH OCCURRENCE
  - GENERAL AGGREGATE
  - PERSONAL & ADV INJURY
  - PRODUCTS/COMP/OP AGG
  - DAMAGE TO PREMISES (EA OCC)
  - MED EXP (ANY ONE PERSON)

Retorna um ExtractedCOI com uma policy GL e coverages associadas.
"""

from __future__ import annotations

import re
from typing import List, Optional

from .layout import PageText
from .models import ExtractedCOI, ExtractedPolicy, ExtractedCoverage


# ---------- Utilitários de texto ----------


def _full_text(pages: List[PageText]) -> str:
    return "\n".join((p.text or "") for p in pages)


def _find_gl_row_text(pages: List[PageText]) -> str:
    """
    Tenta encontrar um bloco de texto que represente a linha GL do ACORD.

    Procuramos por janelas de ~4 linhas contendo "GENERAL" e "LIAB" ou
    "COMMERCIAL GENERAL LIABILITY". Se não acharmos, voltamos o texto completo.
    """
    for page in pages:
        lines = page.lines or (page.text or "").splitlines()
        if not lines:
            continue

        for i in range(0, max(0, len(lines) - 4)):
            window_lines = lines[i : i + 5]
            window = " ".join(window_lines)
            upper = window.upper()
            if ("GENERAL" in upper and "LIAB" in upper) or "COMMERCIAL GENERAL LIABILITY" in upper:
                return "\n".join(window_lines)

    # Fallback: texto completo
    return _full_text(pages)


def _parse_mmddyyyy_to_iso(s: str) -> Optional[str]:
    """
    Converte datas no formato mm/dd/yyyy ou m/d/yyyy para ISO (yyyy-mm-dd).
    """
    m = re.search(r"(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})", s)
    if not m:
        return None
    month = int(m.group(1))
    day = int(m.group(2))
    year = int(m.group(3))
    if not (1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100):
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


def _normalize_date_token(s: str) -> str:
    """
    Remove tudo exceto dígitos para comparação de tokens de data.
    Ex: "06/01/2023" -> "06012023"
    """
    return re.sub(r"[^0-9]", "", s or "")


def _parse_gl_policy_metadata(
    certificate_id: int, pages: List[PageText]
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extrai número de apólice e datas de vigência a partir da linha GL.
    """
    row = _find_gl_row_text(pages)

    # Extrai datas
    date_pattern = r"\d{1,2}\s*/\s*\d{1,2}\s*/\s*\d{4}"
    date_strings = re.findall(date_pattern, row)
    eff_iso = _parse_mmddyyyy_to_iso(date_strings[0]) if len(date_strings) >= 1 else None
    exp_iso = _parse_mmddyyyy_to_iso(date_strings[1]) if len(date_strings) >= 2 else None

    # Tenta encontrar número de apólice como token anterior à primeira data
    tokens = re.findall(r"[A-Z0-9\-\/]+", row.upper())
    normalized_dates = {_normalize_date_token(d) for d in date_strings}

    policy_number: Optional[str] = None
    for idx, tok in enumerate(tokens):
        if _normalize_date_token(tok) in normalized_dates:
            # token anterior pode ser policy_number
            if idx > 0:
                candidate = tokens[idx - 1]
                # heurística: ter dígito e pelo menos 6 caracteres
                if any(ch.isdigit() for ch in candidate) and len(candidate) >= 6:
                    policy_number = candidate
            break

    return policy_number, eff_iso, exp_iso


# ---------- Parsing de limites ----------


def _parse_number(num_str: str) -> Optional[float]:
    if not num_str:
        return None
    # remove símbolos ($, , , espaços)
    cleaned = re.sub(r"[^\d.]", "", num_str)
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_limit(label: str, text: str) -> Optional[float]:
    """
    Procura por LABEL seguido de um valor monetário.

    Estratégia em 2 passos:
    1) Tenta capturar valor logo após o label (mesma linha).
    2) Se falhar, permite quebra de linha e usa uma janela pequena após o label.
    """
    escaped = re.escape(label)

    # 1) mesma linha / logo após
    pattern_same = rf"{escaped}[\s:]+([\$]?\s*[\d,]+(?:\.\d{{2}})?)"
    m = re.search(pattern_same, text, flags=re.IGNORECASE)
    if m:
        return _parse_number(m.group(1))

    # 2) tolerante a quebra de linha – até ~80 caracteres após o label
    pattern_window = rf"{escaped}(.{{0,80}}?)([\$]?\s*[\d,]+(?:\.\d{{2}})?)"
    m = re.search(pattern_window, text, flags=re.IGNORECASE | re.DOTALL)
    if m:
        return _parse_number(m.group(2))

    return None


def _parse_limit_multi(labels: List[str], text: str) -> Optional[float]:
    for label in labels:
        value = _parse_limit(label, text)
        if value is not None:
            return value
    return None


def _sanitize_limit(value: Optional[float]) -> Optional[float]:
    """
    Normaliza limites extraídos:
    - None permanece None
    - valores <= 0 são descartados (tratados como não encontrados)
    """
    if value is None:
        return None
    if value <= 0:
        return None
    return value


# ---------- Parser principal de GL ----------


def parse_acord25_gl_limits(
    certificate_id: int,
    pages: List[PageText],
) -> Optional[ExtractedCOI]:
    """
    Parser de GL para ACORD 25.

    Retorna ExtractedCOI com uma policy GL e coverages associadas,
    ou None se não encontrar limites mínimos de GL.
    """
    full_text = _full_text(pages)
    if not full_text.strip():
        return None

    # 1) Dados de policy (número, datas)
    policy_number, eff_date, exp_date = _parse_gl_policy_metadata(
        certificate_id, pages
    )

    # 2) Definição de labels/aliases
    each_labels = [
        "EACH OCCURRENCE",
        "EACHOCCURRENCE",
        "EACH OCCUR.",
        "EACH OCCUR",
        "EACH OCC.",
        "EACH OCC",
    ]

    agg_labels = [
        "GENERAL AGGREGATE",
        "GEN'L AGGREGATE",
        "GENL AGGREGATE",
        "GEN'L AGG.",
        "GENL AGG.",
    ]

    pers_adv_labels = [
        "PERSONAL & ADV INJURY",
        "PERSONAL AND ADV INJURY",
        "PERSONAL & ADVERTISING INJURY",
        "PERSONAL AND ADVERTISING INJURY",
        "PERS & ADV INJ",
        "PERS/ADV INJ",
    ]

    prod_agg_labels = [
        "PRODUCTS - COMP/OP AGG",
        "PRODUCTS-COMP/OP AGG",
        "PRODUCTS & COMP/OP AGG",
        "PRODUCTS/COMPLETED OPERATIONS AGG",
        "PRODUCTS - COMPLETED OPERATIONS",
        "PRODUCTS/COMPLETED OPS AGG",
    ]

    damage_prem_labels = [
        "DAMAGE TO PREMISES (EA OCCURRENCE)",
        "DAMAGE TO PREMISES (EA OCC)",
        "DAMAGE TO RENTED PREMISES",
        "DAMAGE TO RENTED PREM",
        "PREMISES (EA OCCURRENCE)",
        "PREMISES (EA OCC)",
    ]

    med_exp_labels = [
        "MED EXP (ANY ONE PERSON)",
        "MED EXP (ANY ONE PERS)",
        "MEDICAL EXPENSE (ANY ONE PERSON)",
        "MEDICAL EXP (ANY ONE PERSON)",
    ]

    # 3) Extração de limites numéricos
    each_occ = _sanitize_limit(_parse_limit_multi(each_labels, full_text))
    gen_agg = _sanitize_limit(_parse_limit_multi(agg_labels, full_text))
    pers_adv = _sanitize_limit(_parse_limit_multi(pers_adv_labels, full_text))
    prod_agg = _sanitize_limit(_parse_limit_multi(prod_agg_labels, full_text))
    damage_prem = _sanitize_limit(_parse_limit_multi(damage_prem_labels, full_text))
    med_exp = _sanitize_limit(_parse_limit_multi(med_exp_labels, full_text))

    # Se não conseguimos nenhum dos dois principais, abortamos
    if each_occ is None and gen_agg is None:
        return None

    # 4) Qualidade / consistência
    quality = 1.0

    if each_occ is None or gen_agg is None:
        quality = 0.7
    else:
        # Regra simples: EACH OCCURRENCE não deve ser maior que AGGREGATE
        if each_occ > gen_agg:
            print(
                f"[parser_acord25] Aviso: GL_EACH_OCC ({each_occ}) > GL_AGGREGATE ({gen_agg}) "
                f"no certificate {certificate_id}. Marcando qualidade baixa."
            )
            quality = 0.5

    # 5) Monta estrutura de saída
    policies: List[ExtractedPolicy] = []
    coverages: List[ExtractedCoverage] = []

    policy_index = 0
    policies.append(
        ExtractedPolicy(
            lob_code="GL",
            carrier_name=None,
            policy_number=policy_number,
            effective_date=eff_date,
            expiration_date=exp_date,
            cancellation_notice_days=None,
            source_method="PARSER",
            confidence_score=quality,
        )
    )

    def add_cov(code: str, amount: Optional[float]) -> None:
        if amount is None:
            return
        coverages.append(
            ExtractedCoverage(
                policy_index=policy_index,
                coverage_code=code,
                limit_amount=amount,
                limit_currency="USD",
                deductible_amount=None,
                deductible_currency="USD",
                source_method="PARSER",
                confidence_score=quality,
            )
        )

    add_cov("GL_EACH_OCC", each_occ)
    add_cov("GL_AGGREGATE", gen_agg)
    add_cov("GL_PERS_ADV", pers_adv)
    add_cov("GL_PROD_AGG", prod_agg)
    add_cov("GL_DAMAGE_PREM", damage_prem)
    add_cov("GL_MED_EXP", med_exp)

    return ExtractedCOI(
        certificate_id=certificate_id,
        policies=policies,
        coverages=coverages,
        clauses=[],  # ainda não tratamos clauses no GL
        source="PARSER",
        quality_score=quality,
    )
