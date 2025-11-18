"""
Enums do ACE
Constantes e enumerações para evitar strings hardcoded
"""

from enum import Enum


class ExtractionStatus(str, Enum):
    """Status de extração de COI"""
    PENDING = 'PENDING'
    STARTED = 'STARTED'
    OCR_IN_PROGRESS = 'OCR_IN_PROGRESS'
    PARSING = 'PARSING'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    OCR_FAILED = 'OCR_FAILED'
    PARSING_FAILED = 'PARSING_FAILED'
    VALIDATION_FAILED = 'VALIDATION_FAILED'
    TIMEOUT = 'TIMEOUT'


class CoverageType(str, Enum):
    """Tipos de cobertura"""
    GL = 'GL'  # General Liability
    AL = 'AL'  # Auto Liability
    WC = 'WC'  # Workers Compensation
    UMB = 'UMB'  # Umbrella
