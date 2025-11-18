"""
Parser ACORD 25 - General Liability
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from ace.extraction.layout import PageText
from ace.extraction.parser_config import GL_LABELS
from ace.extraction.models import ExtractedCOI, ExtractedPolicy, ExtractedCoverage
from ace.utils.logger import get_logger
from ace.extraction.classifier import classify_document, DocType

from ace.utils.exceptions import ParsingException

logger = get_logger('ace.extraction.parser_acord25')

try:
    from ace.extraction.claude_client import parse_with_haiku
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    logger.warning("Claude Haiku não disponível")


def _full_text(pages: List[PageText]) -> str:
    return '\n'.join(p.text for p in pages)


def _find_gl_section(text: str) -> Optional[str]:
    patterns = [
        r'GENERAL LIABILITY[\s\S]{0,2000}(?=AUTOMOBILE|UMBRELLA|WORKERS|EXCESS|\Z)',
        r'COMMERCIAL GENERAL LIABILITY[\s\S]{0,2000}(?=AUTOMOBILE|UMBRELLA|WORKERS|EXCESS|\Z)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return None


def extract_dates(pages: List[PageText]) -> Tuple[Optional[str], Optional[str]]:
    text = _full_text(pages)
    date_pattern = r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b'
    matches = list(re.finditer(date_pattern, text))
    
    if len(matches) >= 2:
        def parse_date(m):
            month, day, year = m.groups()
            if len(year) == 2:
                year = '20' + year
            try:
                return datetime(int(year), int(month), int(day)).strftime('%Y-%m-%d')
            except:
                return None
        
        eff = parse_date(matches[0])
        exp = parse_date(matches[1])
        
        if eff and exp:
            logger.info(f"Datas extraídas: {eff} a {exp}")
            return eff, exp
    
    logger.warning(f"Datas incompletas: eff={None}, exp={None}")
    return None, None


def extract_policy_number(pages: List[PageText]) -> Optional[str]:
    text = _full_text(pages)
    gl_section = _find_gl_section(text)
    if not gl_section:
        logger.warning("Linha GL não encontrada, usando texto completo")
        gl_section = text
    
    patterns = [
        r'POLICY\s*(?:NUMBER|NO\.?|#)[\s:]*([A-Z0-9\-]{6,20})',
        r'POL(?:ICY)?\s*#?[\s:]*([A-Z0-9\-]{6,20})',
        r'\bGL[\s\-]?(\d{6,15})\b',
    ]
    
    candidates = []
    for pattern in patterns:
        matches = re.finditer(pattern, gl_section, re.IGNORECASE)
        for m in matches:
            policy_num = m.group(1).strip()
            if 6 <= len(policy_num) <= 20 and not policy_num.isdigit():
                candidates.append(policy_num)
    
    if not candidates:
        logger.warning("Policy number não encontrado")
        return None
    
    policy_number = candidates[0]
    logger.info(f"Policy number extraído: {policy_number}")
    return policy_number


def _extract_limit_multi_strategy(limit_type: str, text: str, custom_labels: dict = None) -> Optional[float]:
    labels = custom_labels.get(limit_type, []) if custom_labels else GL_LABELS.get(limit_type, [])
    
    if not labels:
        return None
    
    for label in labels:
        pattern = rf'{re.escape(label)}[\s:]*\$?\s*([\d,]+(?:\.\d{{2}})?)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                value = float(match.group(1).replace(',', ''))
                logger.debug(f"{limit_type}: USD {value:,.2f}")
                return value
            except:
                continue
    
    for label in labels:
        pattern = rf'{re.escape(label)}[\s\S]{{0,50}}\$?\s*([\d,]+(?:\.\d{{2}})?)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                value = float(match.group(1).replace(',', ''))
                logger.debug(f"{limit_type}: USD {value:,.2f}")
                return value
            except:
                continue
    
    gl_section = _find_gl_section(text)
    if gl_section:
        amounts = re.findall(r'\$?\s*([\d,]+(?:\.\d{2})?)', gl_section)
        amounts = [float(a.replace(',', '')) for a in amounts if a.replace(',', '').replace('.', '').isdigit()]
        amounts = [a for a in amounts if 100_000 <= a <= 100_000_000]
        
        if amounts:
            value = amounts[0]
            logger.warning(f"{limit_type}: USD {value:,.2f} (baixa confiança)")
            return value
    
    return None


def _filter_bizarre_values(limits: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
    filtered = {}
    
    for code, value in limits.items():
        if value is None:
            filtered[code] = None
            continue
        
        if code in ['GL_EACH_OCC', 'GL_AGGREGATE', 'GL_PERS_ADV', 'GL_PROD_AGG']:
            if value < 100_000:
                logger.warning(f"Rejeitado {code}: USD {value:,.2f} muito baixo")
                filtered[code] = None
                continue
        
        if code == 'GL_MED_EXP' and value > 100_000:
            logger.warning(f"Rejeitado {code}: USD {value:,.2f} muito alto")
            filtered[code] = None
            continue
        
        if code == 'GL_DAMAGE_PREM' and value > 2_000_000:
            logger.warning(f"Rejeitado {code}: USD {value:,.2f} muito alto")
            filtered[code] = None
            continue
        
        filtered[code] = value
    
    each_occ = filtered.get('GL_EACH_OCC')
    gen_agg = filtered.get('GL_AGGREGATE')
    
    if each_occ and gen_agg and each_occ > gen_agg:
        logger.warning(f"Trocando valores: EACH_OCC > AGGREGATE")
        filtered['GL_EACH_OCC'] = gen_agg
        filtered['GL_AGGREGATE'] = each_occ
    
    return filtered


def extract_limits(pages: List[PageText]) -> Dict[str, Optional[float]]:
    full_text = _full_text(pages)
    
    limits = {
        'GL_EACH_OCC': _extract_limit_multi_strategy('EACH_OCCURRENCE', full_text),
        'GL_AGGREGATE': _extract_limit_multi_strategy('GENERAL_AGGREGATE', full_text),
        'GL_PERS_ADV': _extract_limit_multi_strategy('PERSONAL_ADV_INJURY', full_text),
        'GL_PROD_AGG': _extract_limit_multi_strategy('PRODUCTS_AGG', full_text),
        'GL_DAMAGE_PREM': _extract_limit_multi_strategy('DAMAGE_PREMISES', full_text),
        'GL_MED_EXP': _extract_limit_multi_strategy('MEDICAL_EXPENSE', full_text),
    }
    
    found = sum(1 for v in limits.values() if v is not None)
    logger.info(f"Limites brutos: {found}/6")
    
    limits = _filter_bizarre_values(limits)
    
    filtered = sum(1 for v in limits.values() if v is not None)
    logger.info(f"Limites filtrados: {filtered}/6")
    
    return limits


def validate_and_score(limits: Dict[str, Optional[float]]) -> Tuple[float, List[str]]:
    issues = []
    each_occ = limits.get('GL_EACH_OCC')
    gen_agg = limits.get('GL_AGGREGATE')
    
    if not each_occ and not gen_agg:
        issues.append("Sem limites principais")
        logger.error("Validação falhou")
        return 0.0, issues
    
    if not each_occ or not gen_agg:
        issues.append("Falta limite principal")
        logger.warning("Limite faltando")
    
    if each_occ and gen_agg:
        if each_occ > gen_agg:
            issues.append("EACH_OCC > AGGREGATE")
        
        ratio = gen_agg / each_occ if each_occ > 0 else 0
        if ratio < 1.5:
            issues.append("AGGREGATE muito próximo de EACH_OCC")
    
    valid = sum(1 for v in limits.values() if v is not None)
    has_both = 1.0 if each_occ and gen_agg else 0.5
    ratio_ok = 1.0 if not issues or len(issues) <= 1 else 0.5
    
    quality = (valid / 6) * has_both * ratio_ok
    
    logger.info(f"Quality: {quality:.2f}, issues: {len(issues)}")
    if issues:
        for issue in issues:
            logger.warning(f"  - {issue}")
    
    return quality, issues


def build_extracted_coi(certificate_id, policy_number, eff_date, exp_date, limits, quality_score):
    policies = []
    if policy_number or eff_date:
        policies.append(ExtractedPolicy(
            lob_code="GL",
            carrier_name=None,
            policy_number=policy_number,
            effective_date=eff_date,
            expiration_date=exp_date,
            cancellation_notice_days=None,
            source_method="REGEX_PARSER",
            confidence_score=0.8 if policy_number else 0.5,
        ))
    
    coverages = []
    for code, amount in limits.items():
        if amount is not None:
            coverages.append(ExtractedCoverage(
                policy_index=0,
                coverage_code=code,
                limit_amount=amount,
                limit_currency="USD",
                deductible_amount=None,
                deductible_currency="USD",
                source_method="REGEX_PARSER",
                confidence_score=0.8,
            ))
    
    logger.info(f"COI criado: {len(coverages)} coverages")
    
    return ExtractedCOI(
        certificate_id=certificate_id,
        policies=policies,
        coverages=coverages,
        clauses=[],
        source="REGEX_PARSER",
        quality_score=quality_score,
    )


def parse_acord25_gl_limits(certificate_id: int, pages: List[PageText]) -> Optional[ExtractedCOI]:
    logger.info(f"=== Parsing certificate {certificate_id} ===")
    
    try:
        eff_date, exp_date = extract_dates(pages)
        policy_number = extract_policy_number(pages)
        limits = extract_limits(pages)
        quality, issues = validate_and_score(limits)
        
        if quality == 0.0:
            logger.error("Parsing falhou completamente")
            
            if CLAUDE_AVAILABLE and hasattr(pages[0], '_source_pdf'):
                logger.warning("Tentando Haiku...")
                try:
                    ocr_text = _full_text(pages)
                    result = parse_with_haiku(certificate_id, pages[0]._source_pdf, ocr_text)
                    if result and result.quality_score >= 0.7:
                        logger.info(f"Haiku salvou! Quality: {result.quality_score:.2f}")
                        return result
                except Exception as e:
                    logger.error(f"Haiku falhou: {e}")
            
            return None
        
        if quality >= 0.7:
            result = build_extracted_coi(certificate_id, policy_number, eff_date, exp_date, limits, quality)
            logger.info(f"=== Concluído: quality={quality:.2f} ===")
            return result
        
        logger.warning(f"Quality baixo: {quality:.2f}")
        
        if CLAUDE_AVAILABLE and hasattr(pages[0], '_source_pdf'):
            try:
                ocr_text = _full_text(pages)
                result = parse_with_haiku(certificate_id, pages[0]._source_pdf, ocr_text)
                if result and result.quality_score >= 0.7:
                    logger.info(f"Haiku melhorou! Quality: {result.quality_score:.2f}")
                    return result
            except Exception as e:
                logger.error(f"Haiku falhou: {e}")
        
        result = build_extracted_coi(certificate_id, policy_number, eff_date, exp_date, limits, quality)
        logger.warning(f"=== Concluído (quality baixo): {quality:.2f} ===")
        return result
        
    except Exception as e:
        logger.critical(f"Erro crítico: {e}", exc_info=True)
        return None



