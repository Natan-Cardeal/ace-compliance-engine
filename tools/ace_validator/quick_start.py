"""
Quick Start - Configuração rápida do ACE Validator
"""

import os
import sys
from pathlib import Path


def setup_env():
    """Configura variáveis de ambiente"""
    print("🔧 Configuração do ACE Validator\n")
    
    # 1. API Key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("📌 ANTHROPIC_API_KEY não encontrada")
        api_key = input("   Cole sua Anthropic API Key (ou Enter para pular): ").strip()
        
        if api_key:
            # Salva em .env
            env_file = Path(".env")
            if env_file.exists():
                content = env_file.read_text()
                if "ANTHROPIC_API_KEY" not in content:
                    with open(env_file, "a") as f:
                        f.write(f"\nANTHROPIC_API_KEY={api_key}\n")
            else:
                env_file.write_text(f"ANTHROPIC_API_KEY={api_key}\n")
            
            print("   ✅ API Key salva em .env")
        else:
            print("   ⚠️  Você pode configurar depois editando .env")
    else:
        print("✅ ANTHROPIC_API_KEY configurada")
    
    # 2. Caminho do ACE
    print("\n📂 Caminho do repositório ACE")
    default_path = "C:/Users/Natan/PyCharmMiscProject/ACE"
    
    if Path(default_path).exists():
        print(f"   ✅ Encontrado em: {default_path}")
        ace_path = default_path
    else:
        ace_path = input("   Cole o caminho do ACE: ").strip()
    
    # 3. Testa instalação
    print("\n🧪 Testando instalação...")
    
    try:
        from core.git_handler import GitHandler
        from core.code_analyzer import CodeAnalyzer
        print("   ✅ Módulos core carregados")
    except ImportError as e:
        print(f"   ❌ Erro ao importar módulos: {e}")
        print("   Execute: pip install -r requirements.txt --break-system-packages")
        return
    
    # 4. Testa Git
    try:
        git = GitHandler(ace_path)
        summary = git.get_repo_summary()
        print(f"   ✅ Git OK - Branch: {summary.get('current_branch', 'N/A')}")
    except Exception as e:
        print(f"   ⚠️  Git: {e}")
    
    # 5. Próximos passos
    print("\n" + "="*60)
    print("✅ Setup concluído!\n")
    print("Próximos passos:")
    print("  1. python main.py full          # Validação completa")
    print("  2. python main.py commits       # Revisar commits")
    print("  3. python example_usage.py      # Ver exemplos")
    print("="*60 + "\n")


if __name__ == "__main__":
    setup_env()
