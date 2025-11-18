"""
Validação robusta com cross-field checking
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple


def validate_dates_cross_check(eff_date: Optional[str], exp_date: Optional[str]) -> Tuple[bool, List[str]]:
    """Valida datas com cross-checking"""
    issues = []
    
    if not eff_date or not exp_date:
        return True, []
    
    try:
        eff = datetime.strptime(eff_date, '%Y-%m-%d')
        exp = datetime.strptime(exp_date, '%Y-%m-%d')
        
        if exp <= eff:
            issues.append(f"Expiration antes/igual a Effective")
            return False, issues
        
        delta_months = (exp.year - eff.year) * 12 + (exp.month - eff.month)
        if delta_months < 6:
            issues.append(f"Período muito curto: {delta_months} meses")
        elif delta_months > 24:
            issues.append(f"Período muito longo: {delta_months} meses")
        
        return len(issues) == 0, issues
        
    except Exception as e:
        issues.append(f"Erro parsing datas: {e}")
        return False, issues


def validate_limits_consistency(limits: Dict[str, Optional[float]]) -> Tuple[bool, List[str]]:
    """Valida consistência entre limites"""
    issues = []
    
    each_occ = limits.get('GL_EACH_OCC')
    gen_agg = limits.get('GL_AGGREGATE')
    
    if each_occ and gen_agg:
        if gen_agg < each_occ:
            issues.append(f"AGGREGATE < EACH_OCC")
        
        ratio = gen_agg / each_occ
        if ratio < 1.5:
            issues.append(f"AGGREGATE/EACH_OCC ratio baixo: {ratio:.2f}x")
    
    return len(issues) == 0, issues


def validate_policy_format(policy_number: Optional[str]) -> Tuple[bool, List[str]]:
    """Valida formato do policy number"""
    issues = []
    
    if not policy_number:
        return True, []
    
    invalid_words = ['number', 'policy', 'follows', 'provisions']
    
    policy_lower = policy_number.lower()
    for word in invalid_words:
        if word in policy_lower:
            issues.append(f"Policy contém palavra inválida")
            return False, issues
    
    if len(policy_number) < 6:
        issues.append(f"Policy muito curto")
        return False, issues
    
    return True, issues
