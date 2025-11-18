"""
Reporter - Sistema de geração de relatórios para ACE Validator

Suporta múltiplos formatos:
- JSON: estruturado para APIs e processamento
- Markdown: legível e versionável
- HTML: visual com gráficos
- Console: output colorido no terminal
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class ValidationReport:
    """Estrutura de um relatório de validação"""
    timestamp: str
    project_info: Dict[str, Any]
    git_info: Dict[str, Any]
    analysis_summary: Dict[str, Any]
    findings: List[Dict[str, Any]]
    recommendations: List[str]
    score: float
    metadata: Dict[str, Any]


class Reporter:
    """Gerador de relatórios de validação"""
    
    def __init__(self, output_dir: str = "reports"):
        """
        Inicializa o reporter
        
        Args:
            output_dir: Diretório para salvar relatórios
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_report(
        self,
        analysis_result: Any,
        project_context: Any,
        git_summary: Dict,
        formats: List[str] = ["json", "markdown"]
    ) -> Dict[str, Path]:
        """
        Gera relatório em múltiplos formatos
        
        Args:
            analysis_result: Resultado da análise do Claude
            project_context: Contexto do projeto
            git_summary: Resumo do repositório Git
            formats: Lista de formatos ("json", "markdown", "html", "console")
        
        Returns:
            Dict com formato -> caminho do arquivo gerado
        """
        # Monta estrutura do relatório
        report = self._build_report_structure(
            analysis_result,
            project_context,
            git_summary
        )
        
        generated_files = {}
        
        # Gera cada formato solicitado
        if "json" in formats:
            json_path = self._generate_json(report)
            generated_files["json"] = json_path
        
        if "markdown" in formats:
            md_path = self._generate_markdown(report)
            generated_files["markdown"] = md_path
        
        if "html" in formats:
            html_path = self._generate_html(report)
            generated_files["html"] = html_path
        
        if "console" in formats:
            self._print_console(report)
        
        return generated_files
    
    def _build_report_structure(
        self,
        analysis_result: Any,
        project_context: Any,
        git_summary: Dict
    ) -> ValidationReport:
        """Constrói estrutura unificada do relatório"""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Project info
        project_info = {
            "root_path": getattr(project_context, "root_path", "N/A"),
            "total_files": getattr(project_context, "total_files", 0),
            "total_lines": getattr(project_context, "total_lines", 0),
            "modules": getattr(project_context, "modules", []),
        }
        
        # Git info
        git_info = {
            "branch": git_summary.get("current_branch", "unknown"),
            "last_commit": git_summary.get("last_commit", "unknown"),
            "repo_path": git_summary.get("repo_path", "N/A"),
        }
        
        # Analysis summary
        analysis_summary = {
            "summary": getattr(analysis_result, "summary", "No summary available"),
            "score": getattr(analysis_result, "score", 0.0),
            "findings_count": len(getattr(analysis_result, "findings", [])),
            "recommendations_count": len(getattr(analysis_result, "recommendations", [])),
        }
        
        # Findings
        findings = getattr(analysis_result, "findings", [])
        
        # Recommendations
        recommendations = getattr(analysis_result, "recommendations", [])
        
        # Metadata
        metadata = {
            "validator_version": "1.0.0",
            "model": "claude-sonnet-4-20250514",
            "report_id": f"ACE_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        }
        
        return ValidationReport(
            timestamp=timestamp,
            project_info=project_info,
            git_info=git_info,
            analysis_summary=analysis_summary,
            findings=findings,
            recommendations=recommendations,
            score=getattr(analysis_result, "score", 0.0),
            metadata=metadata,
        )
    
    def _generate_json(self, report: ValidationReport) -> Path:
        """Gera relatório JSON"""
        timestamp_file = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"validation_{timestamp_file}.json"
        
        # Converte dataclass para dict
        report_dict = asdict(report)
        
        # Salva com indentação bonita
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def _generate_markdown(self, report: ValidationReport) -> Path:
        """Gera relatório Markdown"""
        timestamp_file = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"validation_{timestamp_file}.md"
        
        md_content = self._build_markdown_content(report)
        
        output_path.write_text(md_content, encoding="utf-8")
        
        return output_path
    
    def _generate_html(self, report: ValidationReport) -> Path:
        """Gera relatório HTML"""
        timestamp_file = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"validation_{timestamp_file}.html"
        
        html_content = self._build_html_content(report)
        
        output_path.write_text(html_content, encoding="utf-8")
        
        return output_path
    
    def _print_console(self, report: ValidationReport):
        """Imprime relatório no console com cores"""
        print("\n" + "=" * 70)
        print("📊 ACE VALIDATION REPORT")
        print("=" * 70)
        
        print(f"\n⏰ Timestamp: {report.timestamp}")
        print(f"🆔 Report ID: {report.metadata['report_id']}")
        
        print("\n📁 PROJECT INFO:")
        print(f"   • Files: {report.project_info['total_files']}")
        print(f"   • Lines: {report.project_info['total_lines']:,}")
        print(f"   • Modules: {', '.join(report.project_info['modules'])}")
        
        print("\n🔀 GIT INFO:")
        print(f"   • Branch: {report.git_info['branch']}")
        print(f"   • Last Commit: {report.git_info['last_commit']}")
        
        print(f"\n📈 OVERALL SCORE: {report.score:.1f}/100")
        
        score_bar = self._get_score_bar(report.score)
        print(f"   {score_bar}")
        
        print(f"\n📋 SUMMARY:")
        print(f"   {report.analysis_summary['summary']}")
        
        if report.findings:
            print(f"\n🔍 FINDINGS ({len(report.findings)}):")
            for idx, finding in enumerate(report.findings[:5], 1):
                severity = finding.get("severity", "low")
                icon = self._get_severity_icon(severity)
                print(f"   {idx}. {icon} {finding.get('area', 'N/A')}")
                print(f"      {finding.get('description', 'N/A')}")
                if "file" in finding:
                    print(f"      📄 {finding['file']}")
        
        if report.recommendations:
            print(f"\n💡 RECOMMENDATIONS ({len(report.recommendations)}):")
            for idx, rec in enumerate(report.recommendations[:5], 1):
                print(f"   {idx}. {rec}")
        
        print("\n" + "=" * 70 + "\n")
    
    def _build_markdown_content(self, report: ValidationReport) -> str:
        """Constrói conteúdo Markdown do relatório"""
        
        lines = [
            "# 📊 ACE Validation Report",
            "",
            f"**Generated:** {report.timestamp}",
            f"**Report ID:** {report.metadata['report_id']}",
            "",
            "---",
            "",
            "## 📁 Project Information",
            "",
            f"- **Root Path:** `{report.project_info['root_path']}`",
            f"- **Total Files:** {report.project_info['total_files']}",
            f"- **Total Lines:** {report.project_info['total_lines']:,}",
            f"- **Modules:** {', '.join(report.project_info['modules'])}",
            "",
            "## 🔀 Git Information",
            "",
            f"- **Branch:** `{report.git_info['branch']}`",
            f"- **Last Commit:** `{report.git_info['last_commit']}`",
            f"- **Repository:** `{report.git_info['repo_path']}`",
            "",
            "---",
            "",
            "## 📈 Analysis Results",
            "",
            f"### Overall Score: {report.score:.1f}/100",
            "",
            self._get_score_badge_md(report.score),
            "",
            "### 📋 Summary",
            "",
            report.analysis_summary['summary'],
            "",
        ]
        
        if report.findings:
            lines.extend([
                f"## 🔍 Findings ({len(report.findings)})",
                "",
            ])
            
            for idx, finding in enumerate(report.findings, 1):
                severity = finding.get("severity", "low")
                severity_badge = self._get_severity_badge_md(severity)
                
                lines.extend([
                    f"### {idx}. {finding.get('area', 'N/A')} {severity_badge}",
                    "",
                    f"**Description:** {finding.get('description', 'N/A')}",
                    "",
                ])
                
                if "file" in finding:
                    lines.append(f"**File:** `{finding['file']}`")
                    lines.append("")
        
        if report.recommendations:
            lines.extend([
                f"## 💡 Recommendations ({len(report.recommendations)})",
                "",
            ])
            
            for idx, rec in enumerate(report.recommendations, 1):
                lines.append(f"{idx}. {rec}")
            
            lines.append("")
        
        lines.extend([
            "---",
            "",
            "## 🔧 Metadata",
            "",
            f"- **Validator Version:** {report.metadata['validator_version']}",
            f"- **Model:** {report.metadata['model']}",
            "",
            "*Report generated by ACE Validator*",
        ])
        
        return "\n".join(lines)
    
    def _build_html_content(self, report: ValidationReport) -> str:
        """Constrói conteúdo HTML do relatório"""
        
        # Score color
        score_color = self._get_score_color(report.score)
        
        # Findings HTML
        findings_html = ""
        if report.findings:
            findings_items = []
            for finding in report.findings:
                severity = finding.get("severity", "low")
                severity_class = f"severity-{severity}"
                
                file_info = ""
                if "file" in finding:
                    file_info = f"<div class='finding-file'>📄 {finding['file']}</div>"
                
                findings_items.append(f"""
                <div class="finding {severity_class}">
                    <div class="finding-header">
                        <span class="finding-area">{finding.get('area', 'N/A')}</span>
                        <span class="severity-badge">{severity.upper()}</span>
                    </div>
                    <div class="finding-description">{finding.get('description', 'N/A')}</div>
                    {file_info}
                </div>
                """)
            
            findings_html = "\n".join(findings_items)
        
        # Recommendations HTML
        recommendations_html = ""
        if report.recommendations:
            rec_items = [f"<li>{rec}</li>" for rec in report.recommendations]
            recommendations_html = "<ol>" + "\n".join(rec_items) + "</ol>"
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ACE Validation Report - {report.metadata['report_id']}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }}
        
        header h1 {{
            font-size: 2em;
            margin-bottom: 10px;
        }}
        
        .meta {{
            opacity: 0.9;
            font-size: 0.9em;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section h2 {{
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .info-card {{
            background: #f9f9f9;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }}
        
        .info-card h3 {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .info-card .value {{
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
        }}
        
        .score-container {{
            text-align: center;
            padding: 30px;
            background: #f9f9f9;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        
        .score-value {{
            font-size: 4em;
            font-weight: bold;
            color: {score_color};
        }}
        
        .score-label {{
            font-size: 1.2em;
            color: #666;
            margin-top: 10px;
        }}
        
        .score-bar {{
            width: 100%;
            height: 20px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 20px;
        }}
        
        .score-fill {{
            height: 100%;
            background: {score_color};
            width: {report.score}%;
            transition: width 0.3s ease;
        }}
        
        .summary-box {{
            background: #f0f4ff;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #667eea;
            font-size: 1.1em;
            line-height: 1.8;
        }}
        
        .finding {{
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 15px;
        }}
        
        .finding-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .finding-area {{
            font-weight: bold;
            font-size: 1.1em;
            color: #333;
        }}
        
        .severity-badge {{
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        
        .severity-high {{
            border-left: 4px solid #ef4444;
        }}
        
        .severity-high .severity-badge {{
            background: #fee2e2;
            color: #991b1b;
        }}
        
        .severity-medium {{
            border-left: 4px solid #f59e0b;
        }}
        
        .severity-medium .severity-badge {{
            background: #fef3c7;
            color: #92400e;
        }}
        
        .severity-low {{
            border-left: 4px solid #10b981;
        }}
        
        .severity-low .severity-badge {{
            background: #d1fae5;
            color: #065f46;
        }}
        
        .finding-description {{
            color: #666;
            line-height: 1.6;
        }}
        
        .finding-file {{
            margin-top: 10px;
            padding: 8px 12px;
            background: #f9f9f9;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            color: #555;
        }}
        
        ol {{
            padding-left: 20px;
        }}
        
        ol li {{
            margin-bottom: 10px;
            padding-left: 5px;
        }}
        
        footer {{
            background: #f9f9f9;
            padding: 20px 30px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
            border-top: 1px solid #e0e0e0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 ACE Validation Report</h1>
            <div class="meta">
                <div>Report ID: {report.metadata['report_id']}</div>
                <div>Generated: {report.timestamp}</div>
            </div>
        </header>
        
        <div class="content">
            <div class="section">
                <h2>📁 Project Information</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <h3>Total Files</h3>
                        <div class="value">{report.project_info['total_files']}</div>
                    </div>
                    <div class="info-card">
                        <h3>Total Lines</h3>
                        <div class="value">{report.project_info['total_lines']:,}</div>
                    </div>
                    <div class="info-card">
                        <h3>Git Branch</h3>
                        <div class="value">{report.git_info['branch']}</div>
                    </div>
                    <div class="info-card">
                        <h3>Last Commit</h3>
                        <div class="value">{report.git_info['last_commit']}</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>📈 Overall Score</h2>
                <div class="score-container">
                    <div class="score-value">{report.score:.1f}</div>
                    <div class="score-label">out of 100</div>
                    <div class="score-bar">
                        <div class="score-fill"></div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>📋 Summary</h2>
                <div class="summary-box">
                    {report.analysis_summary['summary']}
                </div>
            </div>
            
            <div class="section">
                <h2>🔍 Findings ({len(report.findings)})</h2>
                {findings_html if findings_html else '<p>No findings reported.</p>'}
            </div>
            
            <div class="section">
                <h2>💡 Recommendations ({len(report.recommendations)})</h2>
                {recommendations_html if recommendations_html else '<p>No recommendations provided.</p>'}
            </div>
        </div>
        
        <footer>
            <div>ACE Validator v{report.metadata['validator_version']}</div>
            <div>Powered by {report.metadata['model']}</div>
        </footer>
    </div>
</body>
</html>
"""
        
        return html
    
    def _get_severity_icon(self, severity: str) -> str:
        """Retorna ícone para severidade"""
        icons = {
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢",
        }
        return icons.get(severity.lower(), "⚪")
    
    def _get_score_color(self, score: float) -> str:
        """Retorna cor baseada no score"""
        if score >= 80:
            return "#10b981"  # verde
        elif score >= 60:
            return "#f59e0b"  # amarelo
        else:
            return "#ef4444"  # vermelho
    
    def _get_score_bar(self, score: float) -> str:
        """Retorna barra de progresso ASCII"""
        filled = int(score / 5)  # 20 blocos = 100%
        empty = 20 - filled
        return f"[{'█' * filled}{'░' * empty}]"
    
    def _get_score_badge_md(self, score: float) -> str:
        """Retorna badge Markdown para score"""
        if score >= 80:
            color = "brightgreen"
            label = "Excellent"
        elif score >= 60:
            color = "yellow"
            label = "Good"
        else:
            color = "red"
            label = "Needs Improvement"
        
        return f"![Score](https://img.shields.io/badge/score-{score:.0f}%25-{color})"
    
    def _get_severity_badge_md(self, severity: str) -> str:
        """Retorna badge Markdown para severidade"""
        colors = {
            "high": "red",
            "medium": "yellow",
            "low": "green",
        }
        color = colors.get(severity.lower(), "lightgrey")
        return f"![{severity}](https://img.shields.io/badge/severity-{severity}-{color})"


# Função helper para uso simples
def generate_validation_report(
    analysis_result,
    project_context,
    git_summary: Dict,
    output_dir: str = "reports",
    formats: List[str] = ["json", "markdown", "html"]
) -> Dict[str, Path]:
    """
    Função helper para gerar relatório rapidamente
    
    Args:
        analysis_result: Resultado da análise
        project_context: Contexto do projeto
        git_summary: Resumo do Git
        output_dir: Diretório de saída
        formats: Formatos desejados
    
    Returns:
        Dict com formato -> caminho do arquivo
    """
    reporter = Reporter(output_dir)
    return reporter.generate_report(
        analysis_result,
        project_context,
        git_summary,
        formats
    )
