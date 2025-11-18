"""
Document Classifier - Identifica tipo de documento antes do parsing

Tipos suportados:
- ACORD_25_COI: Certificate of Insurance ACORD 25
- WORKERS_COMP: Workers Compensation forms
- AUTO_LIABILITY: Auto liability certificates
- ENDORSEMENT: Policy endorsements
- UNKNOWN: Tipo não identificado
"""

from typing import Tuple, List, Dict
from dataclasses import dataclass
from enum import Enum


class DocType(Enum):
    """Tipos de documentos suportados"""
    ACORD_25_COI = "acord_25_coi"
    WORKERS_COMP = "workers_comp"
    AUTO_LIABILITY = "auto_liability"
    ENDORSEMENT = "endorsement"
    CERTIFICATE_GENERIC = "certificate_generic"
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """Resultado da classificação"""
    doc_type: DocType
    confidence: float  # 0.0 a 1.0
    indicators: List[str]  # Keywords encontrados
    page_numbers: List[int] = None  # Páginas onde encontrou (futuro)


class DocumentClassifier:
    """
    Classifica documentos de seguro baseado em keywords e padrões
    """
    
    # Patterns para cada tipo
    PATTERNS = {
        DocType.ACORD_25_COI: {
            'required': [
                r'ACORD\s*25',
                r'CERTIFICATE\s+OF\s+(LIABILITY\s+)?INSURANCE',
            ],
            'strong': [
                r'GENERAL\s+LIABILITY',
                r'EACH\s+OCCURRENCE',
                r'AGGREGATE',
                r'PRODUCTS.*COMP.*OP.*AGG',
            ],
            'weight': 1.0
        },
        
        DocType.WORKERS_COMP: {
            'required': [
                r'WORKERS?\s*\'?\s*COMP',
            ],
            'strong': [
                r'WC\s+STATUTORY\s+LIMITS',
                r'EMPLOYERS?\s+LIABILITY',
                r'DISEASE.*POLICY\s+LIMIT',
                r'DISEASE.*EACH\s+EMPLOYEE',
            ],
            'weight': 0.9
        },
        
        DocType.AUTO_LIABILITY: {
            'required': [
                r'AUTOMOBILE\s+LIABILITY',
                r'AUTO\s+LIABILITY',
            ],
            'strong': [
                r'ANY\s+AUTO',
                r'OWNED\s+AUTOS\s+ONLY',
                r'SCHEDULED\s+AUTOS',
                r'HIRED\s+AUTOS',
                r'NON.*OWNED\s+AUTOS',
            ],
            'weight': 0.8
        },
        
        DocType.ENDORSEMENT: {
            'required': [
                r'ENDORSEMENT',
                r'THIS\s+ENDORSEMENT\s+CHANGES\s+THE\s+POLICY',
            ],
            'strong': [
                r'POLICY\s+NUMBER',
                r'ENDORSEMENT\s+NUMBER',
                r'EFFECTIVE\s+DATE\s+OF\s+ENDORSEMENT',
            ],
            'weight': 0.7
        },
        
        DocType.CERTIFICATE_GENERIC: {
            'required': [
                r'CERTIFICATE',
            ],
            'strong': [
                r'INSURED',
                r'POLICY\s+NUMBER',
                r'COVERAGE',
            ],
            'weight': 0.5
        }
    }
    
    def __init__(self):
        import re
        self.re = re
    
    def classify(self, text: str, min_confidence: float = 0.3) -> ClassificationResult:
        """
        Classifica um documento baseado no texto
        
        Args:
            text: Texto extraído do PDF
            min_confidence: Confiança mínima para não retornar UNKNOWN
            
        Returns:
            ClassificationResult com tipo, confiança e indicadores
        """
        if not text or len(text) < 100:
            return ClassificationResult(
                doc_type=DocType.UNKNOWN,
                confidence=0.0,
                indicators=["Texto insuficiente"]
            )
        
        text_upper = text.upper()
        scores: Dict[DocType, Tuple[float, List[str]]] = {}
        
        # Avaliar cada tipo
        for doc_type, patterns in self.PATTERNS.items():
            score, indicators = self._evaluate_type(text_upper, patterns)
            if score > 0:
                scores[doc_type] = (score, indicators)
        
        if not scores:
            return ClassificationResult(
                doc_type=DocType.UNKNOWN,
                confidence=0.0,
                indicators=["Nenhum pattern encontrado"]
            )
        
        # Pegar o tipo com maior score
        best_type, (confidence, indicators) = max(scores.items(), key=lambda x: x[1][0])
        
        if confidence < min_confidence:
            return ClassificationResult(
                doc_type=DocType.UNKNOWN,
                confidence=confidence,
                indicators=indicators
            )
        
        return ClassificationResult(
            doc_type=best_type,
            confidence=confidence,
            indicators=indicators
        )
    
    def _evaluate_type(self, text: str, patterns: dict) -> Tuple[float, List[str]]:
        """
        Avalia se o texto corresponde a um tipo específico
        
        Returns:
            (score, indicators_found)
        """
        required = patterns.get('required', [])
        strong = patterns.get('strong', [])
        weight = patterns.get('weight', 1.0)
        
        indicators = []
        
        # Verificar patterns obrigatórios
        required_found = 0
        for pattern in required:
            if self.re.search(pattern, text):
                required_found += 1
                indicators.append(pattern.replace(r'\s+', ' ').replace(r'\s*', ''))
        
        # Se não achou todos os required, score 0
        if required_found < len(required):
            return (0.0, indicators)
        
        # Contar patterns fortes
        strong_found = 0
        for pattern in strong:
            if self.re.search(pattern, text):
                strong_found += 1
                indicators.append(pattern.replace(r'\s+', ' ').replace(r'\s*', ''))
        
        # Score = base (required) + bonus (strong) * weight
        base_score = 0.5
        strong_bonus = 0.1 * strong_found
        
        score = min(1.0, (base_score + strong_bonus) * weight)
        
        return (score, indicators)
    
    def classify_multi_page(self, pages_text: List[str]) -> List[ClassificationResult]:
        """
        Classifica múltiplas páginas (futuro)
        
        Args:
            pages_text: Lista de textos, um por página
            
        Returns:
            Lista de ClassificationResult, um por página
        """
        results = []
        for i, page_text in enumerate(pages_text, 1):
            result = self.classify(page_text)
            result.page_numbers = [i]
            results.append(result)
        return results


# Singleton
_classifier = None

def get_classifier() -> DocumentClassifier:
    """Retorna instância singleton do classificador"""
    global _classifier
    if _classifier is None:
        _classifier = DocumentClassifier()
    return _classifier


def classify_document(text: str) -> ClassificationResult:
    """
    Função helper para classificar documento
    
    Args:
        text: Texto extraído do PDF
        
    Returns:
        ClassificationResult
    """
    classifier = get_classifier()
    return classifier.classify(text)
