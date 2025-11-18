"""
Parser Config - VERSÃO MELHORADA
Com validação strict e ranges ajustados
"""

import re
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class ParserConfig:
    """Configuração do parser"""
    
    # Timeouts
    max_parsing_time_seconds: int = 30
    
    # Quality thresholds
    min_quality_score: float = 0.5
    max_quality_score: float = 1.0
    
    # Flags
    strict_validation: bool = True  # ✅ MUDOU: agora é True por padrão
    allow_fallbacks: bool = True
    reject_inconsistent: bool = True  # ✅ NOVO: rejeitar dados inconsistentes
    
    # Limits ranges (USD) - ✅ AJUSTADO para ser mais realístico
    limit_ranges: Dict[str, tuple] = None
    
    def __post_init__(self):
        if self.limit_ranges is None:
            self.limit_ranges = {
                'GL_EACH_OCC': (100_000, 10_000_000),
                'GL_AGGREGATE': (300_000, 20_000_000),
                'GL_PERS_ADV': (100_000, 10_000_000),
                'GL_PROD_AGG': (300_000, 20_000_000),
                'GL_DAMAGE_PREM': (50_000, 1_000_000),
                'GL_MED_EXP': (5_000, 50_000),
                # ✅ NOVOS limites para outras policies
                'AL_COMBINED': (1_000_000, 10_000_000),
                'AL_EACH_ACC': (500_000, 5_000_000),
                'WC_EACH_ACC': (100_000, 1_000_000),
                'WC_DISEASE_EACH': (100_000, 1_000_000),
                'WC_DISEASE_LIMIT': (500_000, 1_000_000),
                'UMB_EACH_OCC': (1_000_000, 10_000_000),
                'UMB_AGGREGATE': (1_000_000, 10_000_000),
            }


# Labels para GL (existente - mantido)
GL_LABELS = {
    'EACH_OCCURRENCE': [
        'EACH OCCURRENCE',
        'EACHOCCURRENCE',
        'EACH OCCUR.',
        'EACH OCCUR',
        'EACH OCC.',
        'EACH OCC',
        'EA OCCURRENCE',
        'EA OCC',
    ],
    'GENERAL_AGGREGATE': [
        'GENERAL AGGREGATE',
        "GEN'L AGGREGATE",
        'GENL AGGREGATE',
        "GEN'L AGG.",
        'GENL AGG.',
        'GEN AGGREGATE',
        'GEN AGG',
    ],
    'PERSONAL_ADV_INJURY': [
        'PERSONAL & ADV INJURY',
        'PERSONAL AND ADV INJURY',
        'PERSONAL & ADVERTISING INJURY',
        'PERSONAL AND ADVERTISING INJURY',
        'PERS & ADV INJ',
        'PERS/ADV INJ',
        'PERS ADV INJ',
    ],
    'PRODUCTS_AGG': [
        'PRODUCTS - COMP/OP AGG',
        'PRODUCTS-COMP/OP AGG',
        'PRODUCTS & COMP/OP AGG',
        'PRODUCTS/COMPLETED OPERATIONS AGG',
        'PRODUCTS - COMPLETED OPERATIONS',
        'PRODUCTS/COMPLETED OPS AGG',
        'PROD/COMP OP AGG',
    ],
    'DAMAGE_PREMISES': [
        'DAMAGE TO PREMISES (EA OCCURRENCE)',
        'DAMAGE TO PREMISES (EA OCC)',
        'DAMAGE TO RENTED PREMISES',
        'DAMAGE TO RENTED PREM',
        'PREMISES (EA OCCURRENCE)',
        'PREMISES (EA OCC)',
        'DMG TO RENTED PREM',
    ],
    'MEDICAL_EXPENSE': [
        'MED EXP (ANY ONE PERSON)',
        'MED EXP (ANY ONE PERS)',
        'MEDICAL EXPENSE (ANY ONE PERSON)',
        'MEDICAL EXP (ANY ONE PERSON)',
        'MED EXP',
    ],
}

# ✅ NOVO: Labels para Auto Liability
AL_LABELS = {
    'COMBINED_SINGLE_LIMIT': [
        'COMBINED SINGLE LIMIT',
        'COMBINED SINGLE LIM',
        'CSL',
        'SINGLE LIMIT',
    ],
    'BODILY_INJURY_PER_PERSON': [
        'BODILY INJURY (PER PERSON)',
        'BODILY INJURY PER PERSON',
        'BI (PER PERSON)',
        'BI PER PERSON',
    ],
    'BODILY_INJURY_PER_ACCIDENT': [
        'BODILY INJURY (PER ACCIDENT)',
        'BODILY INJURY PER ACCIDENT',
        'BI (PER ACCIDENT)',
        'BI PER ACCIDENT',
    ],
    'PROPERTY_DAMAGE': [
        'PROPERTY DAMAGE',
        'PROP DAMAGE',
        'PD',
    ],
}

# ✅ NOVO: Labels para Workers Compensation
WC_LABELS = {
    'EACH_ACCIDENT': [
        'EACH ACCIDENT',
        'EA ACCIDENT',
        'E.L. EACH ACCIDENT',
        'EL EACH ACCIDENT',
    ],
    'DISEASE_EACH_EMPLOYEE': [
        'DISEASE - EA EMPLOYEE',
        'DISEASE EA EMPLOYEE',
        'E.L. DISEASE - EA EMPLOYEE',
        'EL DISEASE EA EMPLOYEE',
    ],
    'DISEASE_POLICY_LIMIT': [
        'DISEASE - POLICY LIMIT',
        'DISEASE POLICY LIMIT',
        'E.L. DISEASE - POLICY LIMIT',
        'EL DISEASE POLICY LIMIT',
    ],
}

# ✅ NOVO: Labels para Umbrella
UMB_LABELS = {
    'EACH_OCCURRENCE': [
        'EACH OCCURRENCE',
        'EACH OCCUR',
        'EACH OCC',
    ],
    'AGGREGATE': [
        'AGGREGATE',
        'AGG',
    ],
}


# Regex patterns pré-compilados
COMPILED_PATTERNS = {
    'date': re.compile(r'(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})'),
    'money_same_line': re.compile(r'[\s:]+([\$]?\s*[\d,]+(?:\.\d{2})?)'),
    'money_window': re.compile(r'(.{0,80}?)([\$]?\s*[\d,]+(?:\.\d{2})?)'),
    'number_only': re.compile(r'[^\d.]'),
    'policy_candidate': re.compile(r'^[A-Z0-9\-\/]{6,}$'),
}


# Padrões de número de apólice
POLICY_NUMBER_PATTERNS = {
    'generic': r'^[A-Z]{2,4}[\-\s]?\d{6,}$',
    'travelers': r'^[A-Z]{3}\d{7}$',
    'hartford': r'^\d{2}[A-Z]{3}\d{6}$',
    'chubb': r'^[A-Z]\d{8}$',
}
