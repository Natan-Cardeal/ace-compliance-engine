import json
import os
import textwrap
from typing import List

import requests

# Lê chave e modelo do ambiente
API_KEY = os.getenv("ANTHROPIC_API_KEY") or os.getenv("ACE_ANTHROPIC_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "Defina ANTHROPIC_API_KEY ou ACE_ANTHROPIC_API_KEY antes de rodar "
        "este script."
    )

MODEL = os.getenv("ACE_ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
API_URL = "https://api.anthropic.com/v1/messages"

# Arquivos que queremos que o Claude revise
FILES_TO_REVIEW: List[str] = [
    "scripts/oracle_generate_gl_ground_truth.py",
    "scripts/inspect_gl_ground_truth_llm.py",
    "scripts/compare_gl_with_ground_truth.py",
    "scripts/create_oracle_samples_gl_from_db.py",
    "ace/extraction/layout.py",
    "ace/extraction/ocr.py",
]


def load_files() -> str:
    """Carrega o conteúdo dos arquivos relevantes para mandar ao Claude."""
    chunks = []
    for path in FILES_TO_REVIEW:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # ignora arquivos com encoding estranho
            continue

        # Evita prompts gigantes: corta arquivos muito longos
        max_len = 12000
        if len(content) > max_len:
            content = content[:max_len] + "\n\n# [trecho truncado pelo reviewer]\n"

        chunks.append(f"=== {path} ===\n{content}")
    return "\n\n".join(chunks)


def build_system_prompt() -> str:
    """Prompt de sistema com os pilares que estamos seguindo."""
    return textwrap.dedent(
        """
        Você é um engenheiro de software sênior ajudando a evoluir o ACE,
        um engine de extração de dados de Certificates of Insurance (COI) ACORD 25.

        Pilares do ACE (siga SEMPRE):

        1. Robustez e segurança:
           - Evitar crashs por exceções não tratadas.
           - Tratar erros de OCR/LLM/BD de forma previsível, com logs claros.
           - Nunca confiar cegamente em dados externos sem validação básica.

        2. Qualidade de extração:
           - Maximizar precisão dos campos (policy_number, datas, limites GL).
           - Deixar explícito quando há incerteza (notes, _llm_error, _parse_error).
           - Separar claramente o que veio do parser tradicional vs. LLM-oráculo.

        3. Observabilidade e avaliação:
           - Facilitar comparação entre ACE e oráculo (CSV, métricas por campo).
           - Produzir saídas legíveis para debugging (inspect_gl_ground_truth, etc.).

        4. Modularidade e testabilidade:
           - Funções pequenas, com responsabilidades claras.
           - Scripts em scripts/ apenas orquestram; lógica de domínio em ace/*.
           - Facilitar a criação de testes unitários no futuro.

        Siga esses pilares ao analisar o código e propor mudanças.
        """
    )


def build_user_prompt(files_blob: str) -> str:
    """Prompt de usuário com contexto específico do bug do oráculo GL."""
    return textwrap.dedent(
        f"""
        Contexto:

        - O ACE já consegue extrair limites GL diretamente do layout/OCR.
        - Queremos um "oráculo" LLM que leia os mesmos COIs e gere um ground truth em
          db/gl_ground_truth.csv com as colunas:
            - certificate_id
            - policy_number
            - effective_date
            - expiration_date
            - gl_aggregate
            - gl_each_occurrence
            - notes
            - _llm_error
            - _parse_error

        - Já rodamos compare_gl_with_ground_truth.py e vimos:
            - avaliados = 0 em todos os campos
            - only_pred > 0 (ou seja, ACE tem valor, oráculo não tem)
        - inspect_gl_ground_truth_llm.py mostrou notas do tipo:
            "Dados extraídos insuficientes – apenas certificate_id e storage_path
             foram fornecidos, sem informações da apólice."

        Suspeita:
        - oracle_generate_gl_ground_truth.py provavelmente NÃO está passando o texto do PDF
          (nem o texto extraído pelo OCR/layout) para o modelo {MODEL}.
        - Ou o CSV gl_ground_truth.csv está sendo gerado com todos os campos nulos,
          exceto notes.

        ARQUIVOS RELEVANTES (código atual):

        {files_blob}

        TAREFAS PARA VOCÊ:

        1. Diagnosticar por que o ground truth GL está vindo apenas com notes e
           todos os campos de dados (policy_number, datas, limites) estão nulos.

        2. Verificar se:
           - o texto real do COI (PDF após OCR/layout) está sendo lido corretamente;
           - esse texto está sendo realmente incluído no prompt enviado ao LLM;
           - o response do LLM está sendo parsado e gravado corretamente em db/gl_ground_truth.csv.

        3. Propor correções concretas, com trechos de código COMPLETOS, para:
           - scripts/oracle_generate_gl_ground_truth.py (principal)
           - pequenos ajustes em inspect_gl_ground_truth_llm.py ou compare_gl_with_ground_truth.py,
             se necessário.

        4. Garantir que após as correções:
           - o oráculo leia o texto completo (ou pelo menos um recorte suficiente) do COI;
           - chame o modelo {MODEL} via API /v1/messages;
           - escreva gl_ground_truth.csv com os campos corretos;
           - trate erros de HTTP/LLM/parse com _llm_error e _parse_error, sem quebrar o fluxo.

        Formato da resposta (IMPORTANTE):

        - Responda em **português**, em **markdown**.
        - Estrutura:
          1. Diagnóstico (o que está errado hoje)
          2. Mudanças sugeridas (em alto nível)
          3. Código proposto (blocos completos de Python, prontos para substituir
             os arquivos relevantes)
          4. Checklist rápido para testar após aplicar as mudanças

        Seja direto, específico e pragmático.
        """
    )


def call_claude(system_prompt: str, user_prompt: str) -> str:
    """Chama a API /v1/messages da Anthropic no formato correto."""
    headers = {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    payload = {
        "model": MODEL,
        "max_tokens": 4000,
        "temperature": 0,
        # >>> AQUI a diferença principal: system vai no top-level, não em messages <<<
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": user_prompt}],
            }
        ],
    }

    resp = requests.post(API_URL, headers=headers, data=json.dumps(payload))
    print(f"Status HTTP: {resp.status_code}")
    if resp.status_code != 200:
        print("Corpo da resposta de erro:")
        print(resp.text[:2000])
        raise SystemExit(1)

    data = resp.json()
    content_blocks = data.get("content") or []
    texts = []
    for block in content_blocks:
        if block.get("type") == "text":
            texts.append(block.get("text", ""))
    return "\n\n".join(texts)


def main() -> None:
    files_blob = load_files()
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(files_blob)
    answer = call_claude(system_prompt, user_prompt)
    print("\n=== RESPOSTA DO CLAUDE ===\n")
    print(answer)


if __name__ == "__main__":
    main()
