"""
Quick Start - ACE Validator
Teste rápido do sistema de validação

Execute: python quick_start_validator.py
"""

import os
import sys
from pathlib import Path


def check_environment():
    """Verifica se ambiente está configurado"""
    print("\n🔍 Verificando ambiente...\n")
    
    checks = {
        "Python 3.x": sys.version_info >= (3, 7),
        "API Key configurada": bool(os.getenv("ANTHROPIC_API_KEY")),
        "Módulo requests": False,
        "Estrutura de pastas": False,
    }
    
    # Check requests
    try:
        import requests
        checks["Módulo requests"] = True
    except ImportError:
        pass
    
    # Check estrutura
    repo_root = Path(__file__).parent.parent.parent
    checks["Estrutura de pastas"] = (
        (repo_root / "ace" / "extraction").exists() and
        (repo_root / "tools" / "ace_validator" / "core").exists()
    )
    
    # Print results
    all_ok = True
    for check, status in checks.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {check}")
        if not status:
            all_ok = False
    
    print()
    
    if not all_ok:
        print("⚠️  Configuração incompleta!\n")
        
        if not checks["API Key configurada"]:
            print("Configure sua API key:")
            print("  export ANTHROPIC_API_KEY='sk-ant-...'")
            print("  ou crie arquivo .env na raiz do projeto\n")
        
        if not checks["Módulo requests"]:
            print("Instale requests:")
            print("  pip install --break-system-packages requests\n")
        
        if not checks["Estrutura de pastas"]:
            print("Execute na pasta correta:")
            print("  cd tools/ace_validator")
            print("  python quick_start_validator.py\n")
        
        return False
    
    print("✅ Ambiente OK! Pronto para executar.\n")
    return True


def run_quick_test():
    """Executa teste rápido"""
    from core.code_analyzer import CodeAnalyzer
    from core.git_handler import GitHandler
    
    print("🧪 TESTE RÁPIDO - ACE Validator\n")
    
    # 1. Análise de código
    print("1️⃣ Testando CodeAnalyzer...")
    repo_root = Path(__file__).parent.parent.parent
    analyzer = CodeAnalyzer(str(repo_root))
    
    context = analyzer.analyze_project(["ace/**/*.py"])
    print(f"   ✅ {context.total_files} arquivos Python encontrados")
    print(f"   ✅ {context.total_lines:,} linhas de código\n")
    
    # 2. Git Handler
    print("2️⃣ Testando GitHandler...")
    git = GitHandler(str(repo_root))
    
    summary = git.get_repo_summary()
    print(f"   ✅ Branch: {summary['current_branch']}")
    print(f"   ✅ Last commit: {summary['last_commit']}\n")
    
    commits = git.get_recent_commits(n=3)
    if commits:
        print(f"   ✅ {len(commits)} commits recentes encontrados")
    else:
        print("   ⚠️  Nenhum commit (repo pode não estar inicializado)")
    print()
    
    # 3. Reporter
    print("3️⃣ Testando Reporter...")
    from core.reporter import Reporter
    
    reporter = Reporter("reports_test")
    print("   ✅ Reporter inicializado")
    print("   ✅ Pasta reports_test criada\n")
    
    print("✅ TESTE COMPLETO!\n")
    print("Próximos passos:")
    print("  • Execute: python main.py full")
    print("  • Ou: python main.py --help")


def show_quick_commands():
    """Mostra comandos rápidos"""
    print("\n📚 COMANDOS RÁPIDOS\n")
    
    commands = [
        ("python main.py full", "Validação completa do projeto"),
        ("python main.py parser parser_acord25", "Valida parser ACORD25"),
        ("python main.py commits -n 10", "Revisa 10 commits recentes"),
        ("python main.py improve 'ace/extraction/*.py'", "Sugere melhorias"),
        ("python main.py --help", "Ajuda completa"),
    ]
    
    max_cmd_len = max(len(cmd) for cmd, _ in commands)
    
    for cmd, desc in commands:
        print(f"  {cmd:<{max_cmd_len}}  # {desc}")
    
    print()


def main():
    """Main"""
    print("\n" + "=" * 70)
    print("🚀 ACE VALIDATOR - QUICK START")
    print("=" * 70)
    
    # Check environment
    if not check_environment():
        print("❌ Corrija os problemas acima antes de continuar.\n")
        sys.exit(1)
    
    # Run quick test
    try:
        run_quick_test()
    except Exception as e:
        print(f"\n❌ Erro durante teste: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Show commands
    show_quick_commands()
    
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
