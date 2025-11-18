"""
Logger Estruturado para ACE
Implementa logging com níveis, contexto e correlação
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class ACELogger:
    """Logger estruturado do ACE"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str, log_file: Optional[str] = None) -> logging.Logger:
        """
        Retorna logger configurado
        
        Args:
            name: Nome do logger (ex: 'ace.extraction')
            log_file: Caminho do arquivo de log (opcional)
        
        Returns:
            Logger configurado
        """
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        
        # Evitar duplicação de handlers
        if logger.handlers:
            return logger
        
        # Formato estruturado
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler (se especificado)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        cls._loggers[name] = logger
        return logger


# Função helper para uso rápido
def get_logger(name: str) -> logging.Logger:
    """Atalho para obter logger"""
    return ACELogger.get_logger(name, 'logs/ace.log')
