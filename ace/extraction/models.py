from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ExtractedPolicy:
    """
    Representa uma policy extraída de um COI (antes de persistir no banco).
    """
    lob_code: str
    carrier_name: Optional[str] = None
    policy_number: Optional[str] = None
    effective_date: Optional[str] = None   # YYYY-MM-DD
    expiration_date: Optional[str] = None  # YYYY-MM-DD
    cancellation_notice_days: Optional[int] = None
    source_method: str = "PARSER"          # PARSER, ML_FALLBACK, etc.
    confidence_score: float = 1.0


@dataclass
class ExtractedCoverage:
    """
    Representa um limite/cobertura extraído.
    policy_index aponta para a posição da policy na lista de policies do ExtractedCOI.
    """
    policy_index: int
    coverage_code: str
    limit_amount: Optional[float] = None
    limit_currency: str = "USD"
    deductible_amount: Optional[float] = None
    deductible_currency: str = "USD"
    source_method: str = "PARSER"
    confidence_score: float = 1.0


@dataclass
class ExtractedClause:
    """
    Representa uma cláusula (AI, WOS, etc.) extraída.
    """
    policy_index: int
    clause_code: str
    clause_description: Optional[str] = None
    source_method: str = "PARSER"
    confidence_score: float = 1.0


@dataclass
class ExtractedCOI:
    """
    Objeto agregado com tudo o que foi extraído de um certificado.
    """
    certificate_id: int
    policies: List[ExtractedPolicy] = field(default_factory=list)
    coverages: List[ExtractedCoverage] = field(default_factory=list)
    clauses: List[ExtractedClause] = field(default_factory=list)
    source: str = "PARSER"           # PARSER ou ML_FALLBACK
    quality_score: float = 1.0
