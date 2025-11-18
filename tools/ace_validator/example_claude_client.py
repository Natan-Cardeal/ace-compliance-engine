"""
Exemplo de Uso - ClaudeClient

Demonstra como usar o ClaudeClient de forma standalone
para análise de código sem precisar do validador completo.
"""

import os
from pathlib import Path


def example_1_analyze_single_file():
    """Exemplo 1: Analisar um único arquivo"""
    print("\n" + "=" * 70)
    print("EXEMPLO 1: Análise de Arquivo Único")
    print("=" * 70 + "\n")
    
    from core.claude_client import ClaudeClient, AnalysisRequest
    
    # Inicializa cliente
    client = ClaudeClient()  # usa ANTHROPIC_API_KEY do ambiente
    
    # Código de exemplo
    sample_code = '''
def parse_coi(text: str) -> dict:
    """Parse Certificate of Insurance"""
    # TODO: implement parsing logic
    ...
    return {}
'''
    
    # Monta requisição
    request = AnalysisRequest(
        context="Sistema de parsing de COIs ACORD 25",
        code_files={"parser.py": sample_code},
        question="Este código está completo? O que falta?",
        focus_areas=["Completude", "Estrutura"]
    )
    
    # Analisa
    print("🤖 Analisando código com Claude...")
    result = client.analyze_code(request)
    
    # Resultados
    print(f"\n📋 Summary: {result.summary}")
    print(f"📊 Score: {result.score}/100\n")
    
    if result.findings:
        print("Findings:")
        for f in result.findings:
            print(f"  • {f.get('area')}: {f.get('description')}")
    
    print()


def example_2_validate_parser():
    """Exemplo 2: Validar parser com test cases"""
    print("\n" + "=" * 70)
    print("EXEMPLO 2: Validação de Parser")
    print("=" * 70 + "\n")
    
    from core.claude_client import ClaudeClient
    
    client = ClaudeClient()
    
    # Parser de exemplo
    parser_code = '''
def extract_gl_limit(text: str) -> float:
    """Extrai limite de GL"""
    import re
    match = re.search(r'EACH OCCURRENCE.*?(\d+,\d+)', text)
    if match:
        amount_str = match.group(1).replace(',', '')
        return float(amount_str)
    return 0.0
'''
    
    # Test cases
    test_cases = [
        {
            "name": "GL EACH OCCURRENCE válido",
            "input": "EACH OCCURRENCE $1,000,000",
            "expected": "1000000.0"
        },
        {
            "name": "Sem limite",
            "input": "texto sem limites",
            "expected": "0.0"
        }
    ]
    
    print("🤖 Validando parser...")
    result = client.validate_parser(parser_code, test_cases)
    
    print(f"\n✅ Válido: {result.get('is_valid')}")
    print(f"📊 Cobertura: {result.get('test_coverage')}/100\n")
    
    if result.get('issues'):
        print("⚠️  Issues:")
        for issue in result['issues']:
            print(f"  • {issue}")
    
    if result.get('suggestions'):
        print("\n💡 Suggestions:")
        for sug in result['suggestions']:
            print(f"  • {sug}")
    
    print()


def example_3_review_pipeline():
    """Exemplo 3: Revisar pipeline completo"""
    print("\n" + "=" * 70)
    print("EXEMPLO 3: Revisão de Pipeline")
    print("=" * 70 + "\n")
    
    from core.claude_client import ClaudeClient
    
    client = ClaudeClient()
    
    # Pipeline de exemplo
    pipeline_code = '''
def process_coi_pipeline(pdf_path: str) -> dict:
    """Pipeline completo de processamento"""
    # 1. OCR
    text = extract_text_from_pdf(pdf_path)
    
    # 2. Parse
    data = parse_acord25(text)
    
    # 3. Save to DB
    save_to_database(data)
    
    return {"status": "success", "data": data}
'''
    
    context = """
Pipeline de processamento de COIs que:
1. Extrai texto via OCR
2. Faz parsing ACORD 25
3. Salva no banco SQLite
"""
    
    print("🤖 Revisando pipeline...")
    result = client.review_extraction_pipeline(pipeline_code, context)
    
    print(f"\n📊 Architecture Score: {result.get('architecture_score')}/100")
    print(f"📊 Error Handling Score: {result.get('error_handling_score')}/100\n")
    
    if result.get('performance_concerns'):
        print("⚠️  Performance Concerns:")
        for concern in result['performance_concerns']:
            print(f"  • {concern}")
    
    if result.get('recommendations'):
        print("\n💡 Recommendations:")
        for rec in result['recommendations']:
            print(f"  • {rec}")
    
    print()


def example_4_suggest_improvements():
    """Exemplo 4: Sugerir melhorias"""
    print("\n" + "=" * 70)
    print("EXEMPLO 4: Sugestões de Melhorias")
    print("=" * 70 + "\n")
    
    from core.claude_client import ClaudeClient
    
    client = ClaudeClient()
    
    # Código com problemas
    code_with_issues = '''
def process(file):
    f = open(file)
    data = f.read()
    result = do_something(data)
    return result
'''
    
    context = "Sistema de processamento de arquivos"
    
    print("🤖 Gerando sugestões...")
    suggestions = client.suggest_improvements(
        "processor.py",
        code_with_issues,
        context
    )
    
    print("\n💡 Sugestões de melhoria:\n")
    for i, sug in enumerate(suggestions, 1):
        print(f"{i}. {sug}")
    
    print()


def main():
    """Main - executa todos os exemplos"""
    
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n❌ ERRO: ANTHROPIC_API_KEY não configurada\n")
        print("Configure:")
        print("  export ANTHROPIC_API_KEY='sk-ant-...'\n")
        return
    
    print("\n🎓 EXEMPLOS DE USO - ClaudeClient\n")
    print("Estes exemplos demonstram como usar o ClaudeClient")
    print("de forma standalone, sem precisar do validador completo.\n")
    
    # Menu
    print("Escolha um exemplo:")
    print("  1. Analisar arquivo único")
    print("  2. Validar parser com test cases")
    print("  3. Revisar pipeline completo")
    print("  4. Sugerir melhorias")
    print("  5. Executar todos")
    print("  0. Sair\n")
    
    try:
        choice = input("Opção (0-5): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n\nSaindo...\n")
        return
    
    examples = {
        "1": example_1_analyze_single_file,
        "2": example_2_validate_parser,
        "3": example_3_review_pipeline,
        "4": example_4_suggest_improvements,
    }
    
    if choice == "0":
        print("\n👋 Até mais!\n")
        return
    
    if choice == "5":
        # Executar todos
        for func in examples.values():
            try:
                func()
            except Exception as e:
                print(f"\n❌ Erro: {e}\n")
    elif choice in examples:
        try:
            examples[choice]()
        except Exception as e:
            print(f"\n❌ Erro: {e}\n")
            import traceback
            traceback.print_exc()
    else:
        print("\n❌ Opção inválida\n")
    
    print("=" * 70)
    print("\n💡 Dica: Revise o código deste exemplo em:")
    print(f"   {__file__}\n")


if __name__ == "__main__":
    main()
