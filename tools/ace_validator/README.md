# 🔍 ACE Validator - Guia Completo

Sistema de validação automática para o projeto ACE (ACORD Compliance Engine) integrado com Git e Claude API.

## 📋 Funcionalidades

- ✅ **Validação completa** do projeto com análise via Claude
- 🔍 **Validação específica** de parsers (ex: parser_acord25)
- 📊 **Relatórios** em múltiplos formatos (JSON, Markdown, HTML)
- 📝 **Revisão de commits** recentes
- 💡 **Sugestões de melhorias** para arquivos específicos
- 🎨 **Output colorido** no console

---

## 🚀 Instalação

### 1. Dependências

```bash
pip install --break-system-packages requests
```

### 2. Configurar API Key

```bash
# Criar .env na raiz do projeto
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# Ou exportar diretamente
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. Estrutura de pastas

```
ACE/
├── ace/
│   ├── extraction/
│   │   ├── parser_acord25.py
│   │   ├── runner.py
│   │   └── ocr.py
│   └── data_model/
├── scripts/
├── tools/
│   └── ace_validator/
│       ├── core/
│       │   ├── claude_client.py
│       │   ├── code_analyzer.py
│       │   ├── git_handler.py
│       │   └── reporter.py
│       ├── main.py
│       └── README.md
└── reports/  (criado automaticamente)
```

---

## 📖 Uso

### Comando 1: Validação Completa

Analisa TODO o projeto e gera relatórios:

```bash
cd tools/ace_validator
python main.py full
```

**Opções:**
```bash
# Escolher formatos de relatório
python main.py full --formats json markdown html

# Apenas console (sem arquivos)
python main.py full --formats console

# Especificar repositório
python main.py --repo /caminho/para/ACE full
```

**Output:**
- 📊 Estatísticas do projeto
- 🔀 Informações do Git
- 🤖 Análise via Claude
- 💾 Relatórios salvos em `reports/`

---

### Comando 2: Validar Parser Específico

Valida e testa um parser:

```bash
python main.py parser parser_acord25
```

**Verifica:**
- ✅ Código válido
- 📊 Cobertura de testes
- ⚠️ Problemas encontrados
- 💡 Sugestões de melhoria

---

### Comando 3: Revisar Commits

Revisa commits recentes:

```bash
# Últimos 5 commits (padrão)
python main.py commits

# Últimos 10 commits
python main.py commits -n 10
```

**Mostra:**
- 📝 Hash e autor
- 📅 Data do commit
- 📄 Arquivos Python modificados

---

### Comando 4: Sugerir Melhorias

Analisa arquivos e sugere melhorias:

```bash
# Todos parsers
python main.py improve "ace/extraction/parser*.py"

# Arquivo específico
python main.py improve "ace/extraction/runner.py"

# Todos arquivos de um módulo
python main.py improve "ace/extraction/*.py"
```

**Fornece:**
- 💡 5-10 sugestões práticas por arquivo
- 🎯 Foco em: clareza, performance, manutenibilidade, erros

---

## 📊 Formatos de Relatório

### JSON (`validation_YYYYMMDD_HHMMSS.json`)

Estruturado para processamento:

```json
{
  "timestamp": "2025-01-15 14:30:00",
  "project_info": {
    "total_files": 45,
    "total_lines": 3250
  },
  "analysis_summary": {
    "score": 85.5,
    "findings_count": 3
  },
  "findings": [...],
  "recommendations": [...]
}
```

### Markdown (`validation_YYYYMMDD_HHMMSS.md`)

Legível e versionável:

```markdown
# 📊 ACE Validation Report

**Score:** 85.5/100

## Findings

### 1. Error Handling 🟡 MEDIUM

**Description:** Missing try-catch in OCR pipeline
**File:** `ace/extraction/ocr.py`
```

### HTML (`validation_YYYYMMDD_HHMMSS.html`)

Visual com cores e layout:
- 📊 Score com barra de progresso
- 🎨 Findings com cores por severidade
- 📋 Layout profissional

---

## 🔧 Configuração Avançada

### Arquivo de configuração (futuro)

Crie `ace_validator/config.yaml`:

```yaml
# Patterns de arquivos para análise
include_patterns:
  - "ace/**/*.py"
  - "scripts/**/*.py"
  - "!**/__pycache__/**"

# Limites de análise
max_files_per_analysis: 10
max_tokens_per_request: 4000

# Outputs
report_formats:
  - json
  - markdown
  - html

# Severidades
severity_thresholds:
  high: 80
  medium: 50
  low: 0
```

---

## 🧪 Exemplos de Output

### Exemplo 1: Validação Completa

```bash
$ python main.py full

🔍 VALIDAÇÃO COMPLETA DO ACE

📊 Resumo do Repositório:
  • current_branch: main
  • last_commit: a3b5c7d2
  • repo_path: /Users/mestre/ACE

📁 Análise do Projeto:
  • Total de arquivos: 45
  • Total de linhas: 3,250
  • Módulos: ace, scripts, tools

🤖 Validação com Claude API:
  • Enviando para análise...

📋 Resultado da Análise:

O pipeline de extração está bem estruturado com separação clara de
responsabilidades. Parser ACORD25 mostra boa robustez na extração de GL.

Score geral: 85.5/100

Principais achados:
  🟡 Error Handling
     Missing comprehensive error handling in OCR pipeline
     Arquivo: ace/extraction/ocr.py

  🟢 Code Quality
     Well-documented functions with clear type hints
     Arquivo: ace/extraction/parser_acord25.py

Recomendações:
  1. Add retry logic to OCR calls
  2. Implement structured logging
  3. Add integration tests for GL parsing

📝 Gerando relatórios...

💾 Relatórios gerados:
  • JSON: reports/validation_20250115_143045.json
  • MARKDOWN: reports/validation_20250115_143045.md
  • CONSOLE: (exibido acima)
```

### Exemplo 2: Validar Parser

```bash
$ python main.py parser parser_acord25

🔍 Validando parser_acord25.py

🤖 Validando com Claude API...

✅ Status: Válido
📊 Cobertura de testes: 75/100

Sugestões de melhoria:
  • Add edge case handling for malformed dates
  • Implement validation for extracted amounts
  • Add logging for debugging
```

---

## 🐛 Troubleshooting

### Erro: "API key não encontrada"

```bash
# Verifique se está configurada
echo $ANTHROPIC_API_KEY

# Configure manualmente
export ANTHROPIC_API_KEY="sk-ant-..."

# Ou passe via argumento
python main.py --api-key "sk-ant-..." full
```

### Erro: "Nenhum commit encontrado"

```bash
# Inicialize Git se necessário
cd /caminho/para/ACE
git init
git add .
git commit -m "Initial commit"
```

### Erro: "Módulo 'requests' não encontrado"

```bash
pip install --break-system-packages requests
```

---

## 📚 Referências

- **Claude API:** https://docs.anthropic.com
- **ACORD Forms:** https://www.acord.org
- **ACE Project:** (documentação interna)

---

## 🎯 Próximos Passos

1. ✅ **Use agora:** `python main.py full`
2. 📊 **Revise relatórios** em `reports/`
3. 💡 **Implemente sugestões** da análise
4. 🔄 **Execute novamente** e compare scores

---

## 💬 Suporte

Para questões sobre o ACE Validator:
1. Revise este README
2. Execute com `--help`: `python main.py --help`
3. Contate a equipe de desenvolvimento

---

**Última atualização:** 2025-01-15
**Versão:** 1.0.0
