# ACE Validator

Sistema de validação integrado com **Git + Claude API** para o ACORD Compliance Engine.

## 🎯 Funcionalidades

- ✅ Validação completa do projeto ACE
- 📊 Análise de parsers (ACORD 25, GL limits, etc)
- 🔍 Revisão de commits recentes
- 💡 Sugestões de melhorias via Claude
- 📋 Relatórios automatizados

## 🚀 Instalação

### 1. Clone/copie o ace_validator

```bash
cd C:\Users\Natan\PyCharmMiscProject
# ace_validator já está aqui
```

### 2. Instale dependências

```bash
cd ace_validator
pip install -r requirements.txt --break-system-packages
```

### 3. Configure API Key

```bash
# Copie o .env.example
cp .env.example .env

# Edite .env e adicione sua Anthropic API Key
```

Ou exporte diretamente:

```powershell
# PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-your-key-here"
```

## 📖 Uso

### Validação Completa

Analisa todo o projeto ACE:

```bash
python main.py full
```

Saída exemplo:
```
🔍 VALIDAÇÃO COMPLETA DO ACE

📊 Resumo do Repositório:
  • repo_path: C:\Users\Natan\PyCharmMiscProject\ACE
  • current_branch: main
  • last_commit: abc123de

📁 Análise do Projeto:
  • Total de arquivos: 45
  • Total de linhas: 3,240
  • Módulos: ace, scripts

🤖 Validação com Claude API:
  • Enviando para análise...

📋 Resultado da Análise:
Score geral: 87/100

🔴 Tratamento de erros
   Parser ACORD 25 não valida campos nulos
   Arquivo: ace/extraction/parser_acord25.py

💾 Relatório salvo: reports/ace_validation_20241115_143022.json
```

### Validar Parser Específico

```bash
python main.py parser parser_acord25
```

### Revisar Commits Recentes

```bash
# Últimos 5 commits (default)
python main.py commits

# Últimos 10 commits
python main.py commits -n 10
```

### Sugerir Melhorias

```bash
# Para arquivos de extração
python main.py improve "ace/extraction/*.py"

# Para um arquivo específico
python main.py improve "ace/extraction/runner.py"
```

## 🏗️ Arquitetura

```
ace_validator/
├── core/
│   ├── git_handler.py       # Operações Git
│   ├── code_analyzer.py     # Análise de código Python
│   ├── claude_client.py     # Interface com Claude API
│   └── reporter.py          # Geração de relatórios
├── validators/
│   ├── extraction_validator.py
│   ├── database_validator.py
│   └── pipeline_validator.py
├── reports/                 # Relatórios gerados
├── main.py                  # CLI principal
└── requirements.txt
```

## 🔧 Casos de Uso

### 1. Validar mudanças antes de commit

```bash
# Revisa commits não enviados
python main.py commits -n 1

# Valida arquivos modificados
python main.py improve "ace/extraction/*.py"
```

### 2. Code review automatizado

```bash
# Após fazer modificações no parser GL
python main.py parser parser_acord25

# Validação completa antes de release
python main.py full
```

### 3. Onboarding de novo dev

```bash
# Gera relatório completo do projeto
python main.py full

# Dev lê o relatório em reports/
```

## 🎨 Personalização

### Análise customizada

Edite `main.py` para focar em áreas específicas:

```python
focus_areas=[
    "Tratamento de erros",
    "Performance com 10k+ PDFs",
    "Qualidade do OCR",
    "Segurança de dados"
]
```

### Validadores específicos

Crie validadores em `validators/`:

```python
# validators/ocr_validator.py

class OCRValidator:
    def validate_tesseract_config(self, config):
        # Validação específica de OCR
        ...
```

## 📊 Relatórios

Os relatórios são salvos em `reports/ace_validation_TIMESTAMP.json`:

```json
{
  "timestamp": "20241115_143022",
  "project": {
    "files": 45,
    "lines": 3240,
    "modules": ["ace", "scripts"]
  },
  "analysis": {
    "summary": "Pipeline robusto, algumas melhorias em error handling",
    "score": 87,
    "findings": [...],
    "recommendations": [...]
  }
}
```

## 🔐 Segurança

- **Nunca commite** `.env` com API keys
- Use `.gitignore` para excluir relatórios com dados sensíveis
- Claude API não armazena código enviado (verify em settings)

## 🤝 Contribuindo

Para adicionar novos validadores:

1. Crie classe em `validators/`
2. Implemente método `validate()`
3. Adicione comando ao `main.py`

## 📝 Notas

- Requer Git instalado no sistema
- Recomendado: Claude Sonnet 4 (melhor para análise técnica)
- Custo por análise completa: ~$0.10-0.30 USD (depende do tamanho do código)

## 🆘 Troubleshooting

**Erro: "API key not found"**
```bash
# Verifique se .env existe ou export manualmente
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Erro: "Repository not found"**
```bash
# Passe caminho explícito
python main.py --repo "C:/caminho/correto/ACE" full
```

**Análise muito lenta**
```bash
# Reduza escopo para arquivos específicos
python main.py improve "ace/extraction/parser*.py"
```

---

**Desenvolvido para Jones Software - ACORD Compliance Engine**
