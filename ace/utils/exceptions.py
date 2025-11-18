"""
Exceções Customizadas do ACE
Hierarquia de exceções para tratamento granular
"""


class ACEException(Exception):
    """Exceção base do ACE"""
    pass


class OCRException(ACEException):
    """Erro durante processamento OCR"""
    pass


class ParsingException(ACEException):
    """Erro durante parsing de documento"""
    pass


class ValidationException(ACEException):
    """Erro de validação de dados"""
    pass


class DatabaseException(ACEException):
    """Erro de operação no banco de dados"""
    pass


class ConfigurationException(ACEException):
    """Erro de configuração"""
    pass
