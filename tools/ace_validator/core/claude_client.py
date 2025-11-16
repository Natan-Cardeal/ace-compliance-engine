"""
Claude Client - Interface com a API do Claude (Anthropic)
"""

import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class AnalysisRequest:
    """Requisição de análise"""
    context: str
    code_files: Dict[str, str]  # filename -> content
    question: str
    focus_areas: List[str]


@dataclass
class AnalysisResponse:
    """Resposta da análise"""
    summary: str
    findings: List[Dict]
    recommendations: List[str]
    score: float  # 0-100


class ClaudeClient:
    """Cliente para API do Claude"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("API key não encontrada. Configure ANTHROPIC_API_KEY")
        
        self.model = "claude-sonnet-4-20250514"
        self.base_url = "https://api.anthropic.com/v1/messages"
    
    def analyze_code(self, request: AnalysisRequest) -> AnalysisResponse:
        """
        Analisa código usando Claude
        
        Args:
            request: Requisição com contexto e código
        
        Returns:
            Resposta estruturada com análise
        """
        # Monta prompt para Claude
        prompt = self._build_analysis_prompt(request)
        
        # Chama API
        response = self._call_api(prompt)
        
        # Parseia resposta
        return self._parse_response(response)
    
    def validate_parser(self, parser_code: str, test_cases: List[Dict]) -> Dict:
        """
        Valida um parser específico
        
        Args:
            parser_code: Código do parser
            test_cases: Lista de casos de teste
        
        Returns:
            Resultado da validação
        """
        prompt = f"""
Analise este parser Python e valide sua implementação:

CÓDIGO DO PARSER:
```python
{parser_code}
```

CASOS DE TESTE:
{json.dumps(test_cases, indent=2)}

Retorne um JSON com:
{{
  "is_valid": boolean,
  "issues": [lista de problemas encontrados],
  "suggestions": [lista de melhorias],
  "test_coverage": score de 0-100
}}
"""
        
        response = self._call_api(prompt)
        return json.loads(self._extract_json(response))
    
    def review_extraction_pipeline(self, pipeline_code: str, context: str) -> Dict:
        """
        Revisa pipeline de extração completo
        
        Args:
            pipeline_code: Código do pipeline
            context: Contexto do projeto ACE
        
        Returns:
            Análise do pipeline
        """
        prompt = f"""
Você é um especialista em pipelines de processamento de documentos.

CONTEXTO DO PROJETO:
{context}

CÓDIGO DO PIPELINE:
```python
{pipeline_code}
```

Analise o pipeline e retorne um JSON com:
{{
  "architecture_score": 0-100,
  "error_handling_score": 0-100,
  "performance_concerns": [lista],
  "security_issues": [lista],
  "recommendations": [lista],
  "critical_issues": [lista]
}}
"""
        
        response = self._call_api(prompt)
        return json.loads(self._extract_json(response))
    
    def suggest_improvements(self, file_path: str, code: str, context: str) -> List[str]:
        """
        Sugere melhorias para um arquivo específico
        
        Args:
            file_path: Caminho do arquivo
            code: Código atual
            context: Contexto do ACE
        
        Returns:
            Lista de sugestões
        """
        prompt = f"""
Arquivo: {file_path}

Contexto: {context}

Código atual:
```python
{code}
```

Liste 5-10 melhorias práticas que podem ser implementadas agora.
Foque em: clareza, performance, manutenibilidade, tratamento de erros.

Retorne apenas uma lista em Markdown com - item por linha.
"""
        
        response = self._call_api(prompt)
        lines = response.strip().split('\n')
        return [line.strip('- ').strip() for line in lines if line.strip().startswith('-')]
    
    def _build_analysis_prompt(self, request: AnalysisRequest) -> str:
        """Constrói prompt de análise"""
        
        files_section = "\n\n".join([
            f"### {filename}\n```python\n{content}\n```"
            for filename, content in request.code_files.items()
        ])
        
        focus_section = "\n".join([f"- {area}" for area in request.focus_areas])
        
        return f"""
CONTEXTO DO PROJETO ACE:
{request.context}

ARQUIVOS PARA ANÁLISE:
{files_section}

FOCOS DA ANÁLISE:
{focus_section}

QUESTÃO:
{request.question}

Retorne um JSON estruturado com:
{{
  "summary": "resumo da análise em 2-3 frases",
  "findings": [
    {{"area": "nome", "severity": "high|medium|low", "description": "...", "file": "..."}},
    ...
  ],
  "recommendations": ["rec1", "rec2", ...],
  "score": 0-100
}}
"""
    
    def _call_api(self, prompt: str, max_tokens: int = 4000) -> str:
        """
        Chama API do Claude
        
        Args:
            prompt: Prompt para enviar
            max_tokens: Máximo de tokens na resposta
        
        Returns:
            Texto da resposta
        """
        import requests
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        response = requests.post(self.base_url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        return result["content"][0]["text"]
    
    def _parse_response(self, response: str) -> AnalysisResponse:
        """Parseia resposta JSON do Claude"""
        try:
            data = json.loads(self._extract_json(response))
            return AnalysisResponse(
                summary=data.get("summary", ""),
                findings=data.get("findings", []),
                recommendations=data.get("recommendations", []),
                score=data.get("score", 0.0)
            )
        except:
            # Fallback se não for JSON válido
            return AnalysisResponse(
                summary=response[:200],
                findings=[],
                recommendations=[],
                score=0.0
            )
    
    def _extract_json(self, text: str) -> str:
        """Extrai JSON de resposta que pode conter markdown"""
        # Remove markdown code blocks
        text = text.replace("```json", "").replace("```", "")
        
        # Procura por { ... }
        start = text.find("{")
        end = text.rfind("}") + 1
        
        if start >= 0 and end > start:
            return text[start:end]
        
        return text
