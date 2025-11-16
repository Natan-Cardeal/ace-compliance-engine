import re
from typing import List, Optional

from .layout import PageText
from .models import (
    ExtractedCOI,
    ExtractedPolicy,
    ExtractedCoverage,
)


def _parse_limit(label: str, text: str) -> Optional[float]:
    """
    Procura um valor numérico logo depois do label.
    Ex.: "EACH OCCURRENCE $1,000,000" -> 1000000.0
    O label é tratado como um literal (não regex) e é case-insensitive.
    """
    escaped = re.escape(label)
    pattern = rf"{escaped}\s+([\$]?\s*[\d,]+(?:\.\d{{2}})?)"
    m = re.search(pattern, text, flags=re.IGNORECASE)
    if not m:
        return None

    raw = m.group(1)
    digits = re.sub(r"[^\d.]", "", raw)
    if not digits:
        return None

    try:
        return float(digits)
    except ValueError:
        return None


def _parse_limit_multi(labels: List[str], text: str) -> Optional[float]:
    """
    Tenta vários rótulos equivalentes (aliases) até achar um valor.
    """
    for label in labels:
        value = _parse_limit(label, text)
        if value is not None:
            return value
    return None


def _normalize_date(s: str) -> str:
    """
    Remove espaços em volta de "/" em algo tipo '10 / 01 / 2024' -> '10/01/2024'.
    """
    return re.sub(r"\s*/\s*", "/", s.strip())


def _parse_mmddyyyy_to_iso(s: str) -> Optional[str]:
    """
    Converte '5/7/2024' ou '05/07/2024' em '2024-05-07'.
    Aceita 1 ou 2 dígitos para mês e dia.
    """
    s = _normalize_date(s)
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if not m:
        return None
    month, day, year = m.groups()
    month = month.zfill(2)
    day = day.zfill(2)
    return f"{year}-{month}-{day}"


def _find_gl_row_text(pages: List[PageText]) -> str:
    """
    Procura a "linha" GL em janelas de até 4 linhas.
    Critério: janela contem COMMERCIAL + GENERAL + algo começando com LIAB.
    Se não achar, devolve texto completo como fallback.
    """
    for p in pages:
        n = len(p.lines)
        for i in range(n):
            window_lines = p.lines[i : i + 4]
            window_text = " ".join(window_lines)
            up = window_text.upper()
            if (
                "COMMERCIAL" in up
                and "GENERAL" in up
                and "LIAB" in up  # pega LIABILITY, LIABI LITY etc.
            ):
                return window_text

    # fallback bem amplo
    return "\n".join(p.text for p in pages)


def _parse_gl_policy_metadata(pages: List[PageText]):
    """
    Heurísticas para extrair:
      - policy_number
      - effective_date
      - expiration_date
    usando a linha GL (janela de 4 linhas).
    """
    row = _find_gl_row_text(pages)

    # Datas no formato MM/DD/YYYY com 1 ou 2 dígitos em mês/dia, com ou sem espaços
    date_pattern = r"\b(\d{1,2}\s*/\s*\d{1,2}\s*/\s*\d{4})\b"
    date_strings = re.findall(date_pattern, row)

    eff_iso = _parse_mmddyyyy_to_iso(date_strings[0]) if len(date_strings) >= 1 else None
    exp_iso = _parse_mmddyyyy_to_iso(date_strings[1]) if len(date_strings) >= 2 else None

    # Tokens alfanuméricos (inclui - e /)
    tokens = re.findall(r"[A-Z0-9\-\/]+", row)
    # normaliza as datas para comparar com tokens
    normalized_dates = {_normalize_date(d) for d in date_strings}

    policy_number = None

    # Procura o token imediatamente antes da primeira data
    for idx, tok in enumerate(tokens):
        if _normalize_date(tok) in normalized_dates:
            if idx > 0:
                candidate = tokens[idx - 1]
                # heurística simples: tem dígito e pelo menos 6 chars
                if any(ch.isdigit() for ch in candidate) and len(candidate) >= 6:
                    policy_number = candidate
            break

    return policy_number, eff_iso, exp_iso


def parse_acord25_gl_limits(
    certificate_id: int,
    pages: List[PageText],
) -> Optional[ExtractedCOI]:
    """
    Parser ACORD 25 focado em GL (MVP melhorado):
    - Junta texto de todas as páginas
    - Procura rótulos GL com aliases (inclui casos como 'EACHOCCURRENCE')
    - Extrai limites principais de GL:
        * EACH OCCURRENCE
        * GENERAL AGGREGATE
        * PERSONAL & ADV INJURY
        * PRODUCTS / COMPLETED OPERATIONS AGG
        * DAMAGE TO RENTED PREMISES
        * MED EXPENSE
    - Tenta extrair também policy_number + datas EFF/EXP da linha GL.
    """
    full_text = "\n".join(p.text for p in pages)

    # Aliases para EACH OCCURRENCE
    each_labels = [
        "EACH OCCURRENCE",
        "EACHOCCURRENCE",   # caso do ACORD com palavras coladas
        "EACH OCCUR.",
        "EACH OCCUR",
        "EACH OCC.",
        "EACH OCC",
    ]

    # Aliases para GENERAL AGGREGATE
    agg_labels = [
        "GENERAL AGGREGATE",
        "GEN'L AGGREGATE",
        "GENL AGGREGATE",
        "GEN'L AGG.",
        "GENL AGG.",
    ]

    # Personal & Advertising Injury
    pers_adv_labels = [
        "PERSONAL & ADV INJURY",
        "PERSONAL AND ADV INJURY",
        "PERSONAL & ADVERTISING INJURY",
        "PERSONAL AND ADVERTISING INJURY",
        "PERS & ADV INJ",
        "PERS/ADV INJ",
    ]

    # Products / Completed Operations Aggregate
    prod_agg_labels = [
        "PRODUCTS - COMP/OP AGG",
        "PRODUCTS-COMP/OP AGG",
        "PRODUCTS & COMP/OP AGG",
        "PRODUCTS/COMPLETED OPERATIONS AGG",
        "PRODUCTS - COMPLETED OPERATIONS",
        "PRODUCTS/COMPLETED OPS AGG",
    ]

    # Damage to rented premises
    damage_prem_labels = [
        "DAMAGE TO PREMISES (EA OCCURRENCE)",
        "DAMAGE TO PREMISES (EA OCC)",
        "DAMAGE TO RENTED PREMISES",
        "DAMAGE TO RENTED PREM",
    ]

    # Medical expenses
    med_exp_labels = [
        "MED EXP (ANY ONE PERSON)",
        "MED EXP (ANY ONE PERS)",
        "MEDICAL EXPENSE (ANY ONE PERSON)",
        "MEDICAL EXP (ANY ONE PERSON)",
    ]

    each_occ = _parse_limit_multi(each_labels, full_text)
    gen_agg = _parse_limit_multi(agg_labels, full_text)
    pers_adv = _parse_limit_multi(pers_adv_labels, full_text)
    prod_agg = _parse_limit_multi(prod_agg_labels, full_text)
    damage_prem = _parse_limit_multi(damage_prem_labels, full_text)
    med_exp = _parse_limit_multi(med_exp_labels, full_text)

    # Se não achamos nenhum dos dois principais, consideramos falha de parser
    if each_occ is None and gen_agg is None:
        return None

    # Metadados da policy GL (número e datas)
    policy_number, eff_date, exp_date = _parse_gl_policy_metadata(pages)

    # Políticas e coberturas
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
            confidence_score=1.0,
        )
    )

    def add_cov(code: str, amount: Optional[float]):
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
                confidence_score=1.0,
            )
        )

    add_cov("GL_EACH_OCC", each_occ)
    add_cov("GL_AGGREGATE", gen_agg)
    add_cov("GL_PERS_ADV", pers_adv)
    add_cov("GL_PROD_AGG", prod_agg)
    add_cov("GL_DAMAGE_PREM", damage_prem)
    add_cov("GL_MED_EXP", med_exp)

    quality = 1.0 if each_occ is not None and gen_agg is not None else 0.7

    return ExtractedCOI(
        certificate_id=certificate_id,
        policies=policies,
        coverages=coverages,
        clauses=[],
        source="PARSER",
        quality_score=quality,
    )
