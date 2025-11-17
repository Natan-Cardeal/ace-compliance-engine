"""
Cliente Claude API - Haiku para parsing
"""

import os
import json
import base64
from typing import Optional, Dict

import anthropic
import pdfplumber

from ace.utils.logger import get_logger
from ace.utils.exceptions import ParsingException
from ace.extraction.models import ExtractedCOI, ExtractedPolicy, ExtractedCoverage

logger = get_logger('ace.extraction.claude_client')

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

if not ANTHROPIC_API_KEY:
    logger.warning("ANTHROPIC_API_KEY não configurada")


def _pdf_to_base64_image(pdf_path: str, page: int = 0) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        if page >= len(pdf.pages):
            page = 0
        
        img = pdf.pages[page].to_image(resolution=150)
        
        from io import BytesIO
        buffer = BytesIO()
        img.original.save(buffer, format='PNG')
        img_bytes = buffer.getvalue()
        
        return base64.b64encode(img_bytes).decode('utf-8')


def parse_with_haiku(certificate_id: int, pdf_path: str, ocr_text: str = None) -> Optional[ExtractedCOI]:
    if not ANTHROPIC_API_KEY:
        logger.error("Claude API não configurada")
        return None
    
    logger.info(f"Usando Claude Haiku para certificate {certificate_id}")
    
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    if ocr_text and len(ocr_text) > 500:
        logger.info("Tentando com texto OCR...")
        result = _parse_with_text(client, certificate_id, ocr_text)
        if result and result.quality_score >= 0.8:
            logger.info(f"Sucesso com texto! Quality: {result.quality_score:.2f}")
            return result
        logger.warning("Texto insuficiente, tentando imagem...")
    
    logger.info("Usando imagem...")
    result = _parse_with_image(client, certificate_id, pdf_path)
    
    if result:
        logger.info(f"Sucesso com imagem! Quality: {result.quality_score:.2f}")
    else:
        logger.error("Claude Haiku falhou")
    
    return result


def _parse_with_text(client: anthropic.Anthropic, certificate_id: int, text: str) -> Optional[ExtractedCOI]:
    prompt = f"""Extract insurance data from this ACORD 25 Certificate of Insurance.

OCR TEXT:
{text[:8000]}

Return ONLY a valid JSON object:
{{
    "policy_number": "string or null",
    "effective_date": "YYYY-MM-DD or null",
    "expiration_date": "YYYY-MM-DD or null",
    "limits": {{
        "GL_EACH_OCC": number or null,
        "GL_AGGREGATE": number or null,
        "GL_PERS_ADV": number or null,
        "GL_PROD_AGG": number or null,
        "GL_DAMAGE_PREM": number or null,
        "GL_MED_EXP": number or null
    }}
}}

RULES:
1. Extract ONLY General Liability limits
2. Numbers only (no commas or dollar signs)
3. If not found, use null
4. DO NOT include text outside JSON

RESPOND WITH ONLY THE JSON OBJECT."""

    try:
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        json_text = response.content[0].text
        json_text = json_text.replace('```json', '').replace('```', '').strip()
        data = json.loads(json_text)
        
        return _build_coi_from_json(certificate_id, data)
        
    except Exception as e:
        logger.error(f"Erro parsing texto: {e}")
        return None


def _parse_with_image(client: anthropic.Anthropic, certificate_id: int, pdf_path: str) -> Optional[ExtractedCOI]:
    try:
        img_base64 = _pdf_to_base64_image(pdf_path, page=0)
    except Exception as e:
        logger.error(f"Erro convertendo PDF: {e}")
        return None
    
    prompt = """Extract insurance data from this ACORD 25 image.

Return ONLY a valid JSON object:
{
    "policy_number": "string or null",
    "effective_date": "YYYY-MM-DD or null",
    "expiration_date": "YYYY-MM-DD or null",
    "limits": {
        "GL_EACH_OCC": number or null,
        "GL_AGGREGATE": number or null,
        "GL_PERS_ADV": number or null,
        "GL_PROD_AGG": number or null,
        "GL_DAMAGE_PREM": number or null,
        "GL_MED_EXP": number or null
    }
}

RULES:
1. Extract ONLY General Liability limits
2. Numbers only (no commas or dollar signs)
3. If not found, use null
4. DO NOT include text outside JSON

RESPOND WITH ONLY THE JSON OBJECT."""

    try:
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1000,
            temperature=0,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img_base64
                        }
                    },
                    {"type": "text", "text": prompt}
                ]
            }]
        )
        
        json_text = response.content[0].text
        json_text = json_text.replace('```json', '').replace('```', '').strip()
        data = json.loads(json_text)
        
        return _build_coi_from_json(certificate_id, data)
        
    except Exception as e:
        logger.error(f"Erro parsing imagem: {e}")
        return None


def _build_coi_from_json(certificate_id: int, data: Dict) -> ExtractedCOI:
    policies = []
    if data.get('policy_number') or data.get('effective_date'):
        policies.append(ExtractedPolicy(
            lob_code="GL",
            carrier_name=None,
            policy_number=data.get('policy_number'),
            effective_date=data.get('effective_date'),
            expiration_date=data.get('expiration_date'),
            cancellation_notice_days=None,
            source_method="CLAUDE_HAIKU",
            confidence_score=0.9,
        ))
    
    coverages = []
    limits = data.get('limits', {})
    for code, amount in limits.items():
        if amount is not None and amount > 0:
            coverages.append(ExtractedCoverage(
                policy_index=0,
                coverage_code=code,
                limit_amount=float(amount),
                limit_currency="USD",
                deductible_amount=None,
                deductible_currency="USD",
                source_method="CLAUDE_HAIKU",
                confidence_score=0.9,
            ))
    
    quality = 0.9 if len(coverages) >= 2 else 0.5
    
    return ExtractedCOI(
        certificate_id=certificate_id,
        policies=policies,
        coverages=coverages,
        clauses=[],
        source="CLAUDE_HAIKU",
        quality_score=quality,
    )
