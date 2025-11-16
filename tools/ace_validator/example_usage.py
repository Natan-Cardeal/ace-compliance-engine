"""
Exemplo de uso do ACE Validator
Execute este script para testar funcionalidades bÃ¡sicas
"""

import os
from core.git_handler import GitHandler
from core.code_analyzer import CodeAnalyzer
from core.claude_client import ClaudeClient, AnalysisRequest


def example_git_operations():
    """Exemplo: operaÃ§Ãµes Git"""
    print("\n" + "="*60)
    print("EXEMPLO 1: OperaÃ§Ãµes Git")
    print("="*60)
    
    # Inicializa handler (ajuste o caminho)
    git = GitHandler("C:/Users/Natan/PyCharmMiscProject/ACE")
    
    # Resumo do repositÃ³rio
    print("\nðŸ“Š Resumo do RepositÃ³rio:")
    summary = git.get_repo_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Ãšltimos commits
    print("\nðŸ“ Ãšltimos 3 commits:")
    commits = git.get_recent_commits(n=3)
    for commit in commits:
        print(f"\n  {commit.hash} - {commit.author}")
        print(f"  {commit.date.strftime('%Y-%m-%d %H:%M')}")
        print(f"  {commit.message}")


def example_code_analysis():
    """Exemplo: anÃ¡lise de cÃ³digo"""
    print("\n" + "="*60)
    print("EXEMPLO 2: AnÃ¡lise de CÃ³digo")
    print("="*60)
    
    analyzer = CodeAnalyzer("C:/Users/Natan/PyCharmMiscProject/ACE")
    
    # AnÃ¡lise do projeto
    print("\nðŸ“ Analisando projeto...")
    context = analyzer.analyze_project(include_patterns=["ace/**/*.py"])
    
    print(f"\n  Total de arquivos: {context.total_files}")
    print(f"  Total de linhas: {context.total_lines:,}")
    print(f"  MÃ³dulos: {', '.join(context.modules)}")
    
    # MÃ³dulo especÃ­fico
    print("\nðŸ“¦ MÃ³dulo ace/extraction:")
    module_info = analyzer.get_module_summary("ace/extraction")
    print(f"  Arquivos: {module_info.get('files_count', 0)}")
    print(f"  FunÃ§Ãµes: {module_info.get('total_functions', 0)}")
    print(f"  Classes: {module_info.get('total_classes', 0)}")


def example_claude_analysis():
    """Exemplo: anÃ¡lise com Claude (requer API key)"""
    print("\n" + "="*60)
    print("EXEMPLO 3: AnÃ¡lise com Claude")
    print("="*60)
    
    # Verifica se API key estÃ¡ configurada
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nâš ï¸  ANTHROPIC_API_KEY nÃ£o configurada")
        print("   Configure com: export ANTHROPIC_API_KEY='sk-ant-...'")
        print("   Pulando exemplo...\n")
        return
    
    print("\nðŸ¤– Inicializando Claude client...")
    claude = ClaudeClient(api_key)
    
    # Exemplo simples: anÃ¡lise de snippet de cÃ³digo
    code_snippet = """
def parse_gl_limits(text: str) -> dict:
    # Parser bÃ¡sico de GL limits
    limits = {}
    
    if "EACH OCCURRENCE" in text:
        limits["each_occ"] = extract_amount(text, "EACH OCCURRENCE")
    
    return limits
"""
    
    print("ðŸ“ Analisando snippet de cÃ³digo...")
    
    request = AnalysisRequest(
        context="Parser de ACORD 25 - General Liability",
        code_files={"snippet.py": code_snippet},
        question="Este parser estÃ¡ robusto o suficiente?",
        focus_areas=["Tratamento de erros", "Edge cases"]
    )
    
    try:
        analysis = claude.analyze_code(request)
        print(f"\nâœ… AnÃ¡lise concluÃ­da!")
        print(f"   Score: {analysis.score}/100")
        print(f"   {analysis.summary}")
    except Exception as e:
        print(f"\nâŒ Erro na anÃ¡lise: {e}")


def main():
    """Executa todos os exemplos"""
    print("\n" + "ðŸ”§ ACE VALIDATOR - EXEMPLOS DE USO ".center(60, "="))
    
    try:
        example_git_operations()
    except Exception as e:
        print(f"\nâŒ Erro no exemplo Git: {e}")
    
    try:
        example_code_analysis()
    except Exception as e:
        print(f"\nâŒ Erro no exemplo de anÃ¡lise: {e}")
    
    try:
        example_claude_analysis()
    except Exception as e:
        print(f"\nâŒ Erro no exemplo Claude: {e}")
    
    print("\n" + "="*60)
    print("âœ… Exemplos concluÃ­dos!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
