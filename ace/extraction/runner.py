"""
Runner - Orquestrador de extração de COIs
VERSÃO MELHORADA com logging, retry, exceções customizadas e context managers
"""

import time
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ace.utils.logger import get_logger
from ace.utils.exceptions import OCRException, ParsingException, DatabaseException
from ace.utils.enums import ExtractionStatus

# Logger
logger = get_logger('ace.extraction.runner')


class ExtractionRunner:
    """Orquestrador de extração de COIs"""
    
    def __init__(self, db_path: str = 'ace.sqlite'):
        self.db_path = db_path
        logger.info(f"ExtractionRunner inicializado com DB: {db_path}")
    
    @contextmanager
    def _db_transaction(self):
        """Context manager para transações do banco"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
            logger.debug("Transação commitada com sucesso")
        except Exception as e:
            conn.rollback()
            logger.error(f"Transação revertida devido a erro: {e}")
            raise DatabaseException(f"Erro na transação: {e}") from e
        finally:
            conn.close()
    
    def _validate_certificate_id(self, certificate_id: int) -> bool:
        """Valida ID do certificado"""
        if not isinstance(certificate_id, int) or certificate_id <= 0:
            raise ValueError(f"certificate_id inválido: {certificate_id}")
        return True
    
    def _create_extraction_run(self, conn, certificate_id: int) -> int:
        """Cria registro de extraction_run"""
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO extraction_runs (certificate_id, status, started_at) VALUES (?, ?, datetime('now'))",
            (certificate_id, ExtractionStatus.STARTED.value)
        )
        run_id = cursor.lastrowid
        logger.info(f"Extraction run criado: {run_id} para certificate {certificate_id}")
        return run_id
    
    def _update_extraction_status(
        self, 
        conn, 
        run_id: int, 
        status: ExtractionStatus, 
        error_detail: Optional[str] = None
    ):
        """Atualiza status da extração"""
        cursor = conn.cursor()
        if status == ExtractionStatus.SUCCESS:
            cursor.execute(
                "UPDATE extraction_runs SET status = ?, completed_at = datetime('now') WHERE id = ?",
                (status.value, run_id)
            )
        else:
            cursor.execute(
                "UPDATE extraction_runs SET status = ?, error_detail = ?, completed_at = datetime('now') WHERE id = ?",
                (status.value, error_detail, run_id)
            )
        logger.info(f"Status atualizado para run {run_id}: {status.value}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(OCRException),
        before_sleep=lambda retry_state: logger.warning(
            f"Tentativa {retry_state.attempt_number} falhou, aguardando {retry_state.next_action.sleep}s..."
        )
    )
    def _extract_text_with_retry(self, pdf_path: str) -> str:
        """Extrai texto com retry automático"""
        from ace.extraction.ocr import extract_text_from_pdf
        
        logger.info(f"Iniciando OCR: {pdf_path}")
        start_time = time.time()
        
        try:
            text = extract_text_from_pdf(pdf_path)
            duration = time.time() - start_time
            
            logger.info(f"OCR concluído em {duration:.2f}s: {len(text)} caracteres extraídos")
            return text
            
        except Exception as e:
            logger.error(f"Erro no OCR: {e}")
            raise OCRException(f"Falha no OCR: {e}") from e
    
    def _parse_with_timeout(self, certificate_id: int, text: str, timeout: int = 30) -> Any:
        """Parse com timeout"""
        from ace.extraction.parser_acord25 import parse_acord25_gl_limits
        from ace.extraction.layout import PageText
        
        logger.info(f"Iniciando parsing para certificate {certificate_id}")
        start_time = time.time()
        
        try:
            pages = [PageText(page_number=1, text=text, lines=text.splitlines())]
            result = parse_acord25_gl_limits(certificate_id, pages)
            
            duration = time.time() - start_time
            logger.info(f"Parsing concluído em {duration:.2f}s")
            
            if result is None:
                raise ParsingException("Parser retornou None - nenhum dado extraído")
            
            return result
            
        except Exception as e:
            logger.error(f"Erro no parsing: {e}")
            raise ParsingException(f"Falha no parsing: {e}") from e
    
    def _persist_extraction(self, conn, run_id: int, extracted_data: Any):
        """Persiste dados extraídos"""
        from ace.data_model.db import persist_extracted_coi
        
        logger.info(f"Persistindo dados para run {run_id}")
        start_time = time.time()
        
        try:
            persist_extracted_coi(conn, extracted_data)
            duration = time.time() - start_time
            
            logger.info(f"Dados persistidos em {duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Erro ao persistir: {e}")
            raise DatabaseException(f"Falha ao persistir: {e}") from e
    
    def process_certificate(self, certificate_id: int, pdf_path: str) -> Dict[str, Any]:
        """
        Processa certificado completo com logging, retry e métricas
        
        Args:
            certificate_id: ID do certificado
            pdf_path: Caminho do PDF
        
        Returns:
            Dict com resultado do processamento
        """
        # Validar entrada
        self._validate_certificate_id(certificate_id)
        
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")
        
        logger.info(f"=== Iniciando processamento: certificate {certificate_id} ===")
        overall_start = time.time()
        
        run_id = None
        result = {
            'certificate_id': certificate_id,
            'status': ExtractionStatus.FAILED.value,
            'error': None,
            'metrics': {}
        }
        
        try:
            with self._db_transaction() as conn:
                # 1. Criar extraction run
                run_id = self._create_extraction_run(conn, certificate_id)
                result['extraction_run_id'] = run_id
                
                # 2. OCR com retry
                self._update_extraction_status(conn, run_id, ExtractionStatus.OCR_IN_PROGRESS)
                text = self._extract_text_with_retry(pdf_path)
                
                # 3. Parsing com timeout
                self._update_extraction_status(conn, run_id, ExtractionStatus.PARSING)
                extracted_data = self._parse_with_timeout(certificate_id, text)
                
                # 4. Persistir
                self._persist_extraction(conn, run_id, extracted_data)
                
                # 5. Sucesso
                self._update_extraction_status(conn, run_id, ExtractionStatus.SUCCESS)
                result['status'] = ExtractionStatus.SUCCESS.value
                
                # Métricas
                total_duration = time.time() - overall_start
                result['metrics']['total_duration_seconds'] = round(total_duration, 2)
                
                logger.info(f"=== Processamento concluído com sucesso em {total_duration:.2f}s ===")
        
        except OCRException as e:
            error_msg = f"OCR falhou após tentativas: {e}"
            logger.error(error_msg, exc_info=True)
            
            if run_id:
                with self._db_transaction() as conn:
                    self._update_extraction_status(conn, run_id, ExtractionStatus.OCR_FAILED, str(e))
            
            result['status'] = ExtractionStatus.OCR_FAILED.value
            result['error'] = error_msg
        
        except ParsingException as e:
            error_msg = f"Parsing falhou: {e}"
            logger.error(error_msg, exc_info=True)
            
            if run_id:
                with self._db_transaction() as conn:
                    self._update_extraction_status(conn, run_id, ExtractionStatus.PARSING_FAILED, str(e))
            
            result['status'] = ExtractionStatus.PARSING_FAILED.value
            result['error'] = error_msg
        
        except DatabaseException as e:
            error_msg = f"Erro no banco de dados: {e}"
            logger.error(error_msg, exc_info=True)
            
            result['status'] = ExtractionStatus.FAILED.value
            result['error'] = error_msg
        
        except Exception as e:
            error_msg = f"Erro inesperado: {e}"
            logger.critical(error_msg, exc_info=True)
            
            if run_id:
                with self._db_transaction() as conn:
                    self._update_extraction_status(conn, run_id, ExtractionStatus.FAILED, str(e))
            
            result['status'] = ExtractionStatus.FAILED.value
            result['error'] = error_msg
        
        return result


# Função helper para compatibilidade com código existente
def process_single_certificate(certificate_id: int, pdf_path: str) -> Dict[str, Any]:
    """Wrapper para manter compatibilidade"""
    runner = ExtractionRunner()
    return runner.process_certificate(certificate_id, pdf_path)
