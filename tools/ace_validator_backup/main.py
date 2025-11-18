"""
ACE Validator - CLI Principal
Sistema de validação integrado com Git + Claude API
"""

import argparse
import json
from pathlib import Path
from core.git_handler import GitHandler
from core.code_analyzer import CodeAnalyzer
from core.claude_client import ClaudeClient, AnalysisRequest


class ACEValidator:
    """Validador principal do ACE"""
    
    def __init__(self, repo_path: str, api_key: str = None):
        self.git = GitHandler(repo_path)
        self.analyzer = CodeAnalyzer(repo_path)
        self.claude = ClaudeClient(api_key)
        self.repo_path = Path(repo_path)
    
    def validate_full_project(self):
        """Validação completa do projeto"""
        print("\n🔍 VALIDAÇÃO COMPLETA DO ACE\n")
        
        # 1. Resumo do repositório
        print("📊 Resumo do Repositório:")
        repo_summary = self.git.get_repo_summary()
        for key, value in repo_summary.items():
            print(f"  • {key}: {value}")
        
        # 2. Análise do código
        print("\n📁 Análise do Projeto:")
        project_context = self.analyzer.analyze_project(
            include_patterns=["ace/**/*.py", "scripts/**/*.py"]
        )
        print(f"  • Total de arquivos: {project_context.total_files}")
        print(f"  • Total de linhas: {project_context.total_lines:,}")
        print(f"  • Módulos: {', '.join(project_context.modules)}")
        
        # 3. Validação com Claude
        print("\n🤖 Validação com Claude API:")
        
        # Extrai arquivos principais
        key_files = self.analyzer.extract_key_files([
            "ace/extraction/parser_acord25.py",
            "ace/extraction/runner.py",
            "ace/extraction/ocr.py"
        ])
        
        if not key_files:
            print("  ⚠️  Arquivos principais não encontrados")
            return
        
        # Monta contexto ACE
        context = self._build_ace_context(project_context)
        
        # Análise via Claude
        request = AnalysisRequest(
            context=context,
            code_files=key_files,
            question="Avalie a qualidade e robustez do pipeline de extração de COIs",
            focus_areas=[
                "Tratamento de erros",
                "Performance e escalabilidade",
                "Qualidade do parsing ACORD 25",
                "Arquitetura do código"
            ]
        )
        
        print("  • Enviando para análise...")
        analysis = self.claude.analyze_code(request)
        
        print(f"\n📋 Resultado da Análise:")
        print(f"\n{analysis.summary}\n")
        print(f"Score geral: {analysis.score}/100\n")
        
        if analysis.findings:
            print("Principais achados:")
            for finding in analysis.findings[:5]:
                severity_icon = {
                    "high": "🔴",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(finding.get("severity", "low"), "⚪")
                
                print(f"  {severity_icon} {finding.get('area', 'N/A')}")
                print(f"     {finding.get('description', 'N/A')}")
                if "file" in finding:
                    print(f"     Arquivo: {finding['file']}")
                print()
        
        if analysis.recommendations:
            print("Recomendações:")
            for i, rec in enumerate(analysis.recommendations[:5], 1):
                print(f"  {i}. {rec}")
        
        # Salva relatório
        self._save_report(analysis, project_context)
    
    def validate_parser(self, parser_name: str = "parser_acord25"):
        """Valida parser específico"""
        print(f"\n🔍 Validando {parser_name}.py\n")
        
        parser_file = f"ace/extraction/{parser_name}.py"
        parser_path = self.repo_path / parser_file
        
        if not parser_path.exists():
            print(f"❌ Arquivo não encontrado: {parser_file}")
            return
        
        parser_code = parser_path.read_text(encoding='utf-8')
        
        # Test cases exemplo
        test_cases = [
            {
                "name": "GL completo",
                "input": "texto com GL_EACH_OCC e GL_AGGREGATE",
                "expected": "extrair ambos limites"
            }
        ]
        
        print("🤖 Validando com Claude API...")
        result = self.claude.validate_parser(parser_code, test_cases)
        
        print(f"\n{'✅' if result.get('is_valid') else '❌'} Status: {'Válido' if result.get('is_valid') else 'Problemas encontrados'}")
        print(f"📊 Cobertura de testes: {result.get('test_coverage', 0)}/100\n")
        
        if result.get('issues'):
            print("Problemas encontrados:")
            for issue in result['issues']:
                print(f"  • {issue}")
        
        if result.get('suggestions'):
            print("\nSugestões de melhoria:")
            for suggestion in result['suggestions']:
                print(f"  • {suggestion}")
    
    def review_recent_changes(self, n_commits: int = 5):
        """Revisa commits recentes"""
        print(f"\n🔍 Revisando últimos {n_commits} commits\n")
        
        commits = self.git.get_recent_commits(n=n_commits)
        
        for commit in commits:
            print(f"📝 {commit.hash} - {commit.author}")
            print(f"   {commit.date.strftime('%Y-%m-%d %H:%M')}")
            print(f"   {commit.message}")
            
            if commit.files_changed:
                py_files = [f for f in commit.files_changed if f.endswith('.py')]
                if py_files:
                    print(f"   Arquivos Python: {len(py_files)}")
                    for f in py_files[:3]:
                        print(f"     - {f}")
            print()
    
    def suggest_improvements(self, file_pattern: str):
        """Sugere melhorias para arquivos"""
        print(f"\n💡 Sugestões de melhoria para: {file_pattern}\n")
        
        files = list(self.repo_path.glob(file_pattern))
        
        if not files:
            print(f"❌ Nenhum arquivo encontrado: {file_pattern}")
            return
        
        context = self._build_ace_context(None)
        
        for file_path in files[:3]:  # Limita a 3 arquivos
            rel_path = file_path.relative_to(self.repo_path)
            print(f"📄 {rel_path}")
            
            code = file_path.read_text(encoding='utf-8')
            suggestions = self.claude.suggest_improvements(
                str(rel_path),
                code,
                context
            )
            
            for suggestion in suggestions:
                print(f"  • {suggestion}")
            print()
    
    def _build_ace_context(self, project_context = None) -> str:
        """Constrói contexto do ACE para Claude"""
        context = """
O ACE (ACORD Compliance Engine) é um sistema para:
- Processar Certificates of Insurance (COIs) em formato ACORD 25
- Extrair dados estruturados de PDFs (com OCR quando necessário)
- Armazenar em SQLite para análise

Stack:
- Python 3.x
- SQLite (ace.sqlite)
- pdfplumber + pytesseract (OCR)
- Estrutura modular: ace/extraction, ace/data_model, scripts/

Foco atual: extração de General Liability (GL) limits
"""
        
        if project_context:
            context += f"""
Estatísticas do projeto:
- {project_context.total_files} arquivos Python
- {project_context.total_lines:,} linhas de código
- Módulos: {', '.join(project_context.modules)}
"""
        
        return context
    
    def _save_report(self, analysis, project_context):
        """Salva relatório em arquivo"""
        report_dir = Path("reports")
        report_dir.mkdir(exist_ok=True)
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"ace_validation_{timestamp}.json"
        
        report = {
            "timestamp": timestamp,
            "project": {
                "files": project_context.total_files,
                "lines": project_context.total_lines,
                "modules": project_context.modules
            },
            "analysis": {
                "summary": analysis.summary,
                "score": analysis.score,
                "findings": analysis.findings,
                "recommendations": analysis.recommendations
            }
        }
        
        report_file.write_text(json.dumps(report, indent=2))
        print(f"\n💾 Relatório salvo: {report_file}")


def main():
    parser = argparse.ArgumentParser(description="ACE Validator - Validação com Git + Claude")
    parser.add_argument("--repo", default="C:/Users/Natan/PyCharmMiscProject/ACE",
                       help="Caminho do repositório ACE")
    parser.add_argument("--api-key", help="Anthropic API Key (ou use ANTHROPIC_API_KEY env)")
    
    subparsers = parser.add_subparsers(dest="command", help="Comando a executar")
    
    # full: validação completa
    subparsers.add_parser("full", help="Validação completa do projeto")
    
    # parser: valida parser específico
    parser_cmd = subparsers.add_parser("parser", help="Valida parser específico")
    parser_cmd.add_argument("name", default="parser_acord25", nargs="?",
                           help="Nome do parser (ex: parser_acord25)")
    
    # commits: revisa commits recentes
    commits_cmd = subparsers.add_parser("commits", help="Revisa commits recentes")
    commits_cmd.add_argument("-n", type=int, default=5, help="Número de commits")
    
    # improve: sugere melhorias
    improve_cmd = subparsers.add_parser("improve", help="Sugere melhorias")
    improve_cmd.add_argument("pattern", help="Padrão de arquivo (ex: ace/extraction/*.py)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Inicializa validador
    validator = ACEValidator(args.repo, args.api_key)
    
    # Executa comando
    if args.command == "full":
        validator.validate_full_project()
    elif args.command == "parser":
        validator.validate_parser(args.name)
    elif args.command == "commits":
        validator.review_recent_changes(args.n)
    elif args.command == "improve":
        validator.suggest_improvements(args.pattern)


if __name__ == "__main__":
    main()
