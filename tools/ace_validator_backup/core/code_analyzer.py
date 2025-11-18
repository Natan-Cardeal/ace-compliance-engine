"""
Code Analyzer - Extrai contexto e metadados do cÃ³digo
"""

import os
import ast
from pathlib import Path
from typing import List, Dict, Set
from dataclasses import dataclass


@dataclass
class FileInfo:
    """InformaÃ§Ãµes de um arquivo"""
    path: str
    size_bytes: int
    lines_count: int
    functions: List[str]
    classes: List[str]
    imports: List[str]
    complexity_score: int


@dataclass
class ProjectContext:
    """Contexto completo do projeto"""
    root_path: str
    total_files: int
    total_lines: int
    modules: List[str]
    main_files: Dict[str, FileInfo]
    dependencies: Set[str]


class CodeAnalyzer:
    """Analisa estrutura e contexto de cÃ³digo Python"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
    
    def analyze_project(self, include_patterns: List[str] = None) -> ProjectContext:
        """
        Analisa projeto completo
        
        Args:
            include_patterns: PadrÃµes de arquivos (ex: ["ace/**/*.py"])
        
        Returns:
            Contexto do projeto
        """
        if include_patterns is None:
            include_patterns = ["**/*.py"]
        
        all_files = []
        for pattern in include_patterns:
            all_files.extend(self.project_root.glob(pattern))
        
        # Filtra arquivos Python vÃ¡lidos
        py_files = [f for f in all_files if f.suffix == '.py' and self._is_valid_file(f)]
        
        total_lines = 0
        main_files = {}
        all_imports = set()
        modules = set()
        
        for file_path in py_files:
            info = self.analyze_file(str(file_path))
            if info:
                total_lines += info.lines_count
                all_imports.update(info.imports)
                
                # Identifica mÃ³dulos principais
                rel_path = file_path.relative_to(self.project_root)
                if len(rel_path.parts) >= 2:
                    modules.add(rel_path.parts[0])
                
                # Guarda arquivos principais
                if self._is_main_file(file_path):
                    main_files[str(rel_path)] = info
        
        return ProjectContext(
            root_path=str(self.project_root),
            total_files=len(py_files),
            total_lines=total_lines,
            modules=sorted(list(modules)),
            main_files=main_files,
            dependencies=all_imports
        )
    
    def analyze_file(self, file_path: str) -> FileInfo:
        """
        Analisa arquivo Python individual
        
        Args:
            file_path: Caminho do arquivo
        
        Returns:
            InformaÃ§Ãµes do arquivo
        """
        path = Path(file_path)
        
        if not path.exists():
            return None
        
        try:
            content = path.read_text(encoding='utf-8-sig')
            tree = ast.parse(content)
            
            functions = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        imports.extend([alias.name for alias in node.names])
                    else:
                        imports.append(node.module if node.module else "")
            
            lines = content.split('\n')
            
            return FileInfo(
                path=str(path),
                size_bytes=path.stat().st_size,
                lines_count=len(lines),
                functions=functions,
                classes=classes,
                imports=list(set(imports)),
                complexity_score=len(functions) + len(classes) * 2
            )
        
        except Exception as e:
            print(f"âš ï¸  Erro ao analisar {file_path}: {e}")
            return None
    
    def extract_key_files(self, focus_on: List[str] = None) -> Dict[str, str]:
        """
        Extrai conteÃºdo dos arquivos principais
        
        Args:
            focus_on: Lista de padrÃµes (ex: ["parser_*.py", "runner.py"])
        
        Returns:
            Dict com filename -> conteÃºdo
        """
        if focus_on is None:
            focus_on = [
                "ace/extraction/*.py",
                "scripts/process_*.py",
                "ace/data_model/db.py"
            ]
        
        files_content = {}
        
        for pattern in focus_on:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file() and file_path.suffix == '.py':
                    rel_path = file_path.relative_to(self.project_root)
                    try:
                        content = file_path.read_text(encoding='utf-8-sig')
                        files_content[str(rel_path)] = content
                    except Exception as e:
                        print(f"âš ï¸  Erro ao ler {rel_path}: {e}")
        
        return files_content
    
    def get_module_summary(self, module_name: str) -> Dict:
        """
        Resumo de um mÃ³dulo especÃ­fico
        
        Args:
            module_name: Nome do mÃ³dulo (ex: "ace/extraction")
        
        Returns:
            Resumo do mÃ³dulo
        """
        module_path = self.project_root / module_name
        
        if not module_path.exists():
            return {}
        
        files = list(module_path.glob("*.py"))
        total_functions = 0
        total_classes = 0
        all_imports = set()
        
        for file_path in files:
            info = self.analyze_file(str(file_path))
            if info:
                total_functions += len(info.functions)
                total_classes += len(info.classes)
                all_imports.update(info.imports)
        
        return {
            "module": module_name,
            "files_count": len(files),
            "total_functions": total_functions,
            "total_classes": total_classes,
            "dependencies": sorted(list(all_imports))
        }
    
    def _is_valid_file(self, path: Path) -> bool:
        """Verifica se arquivo Ã© vÃ¡lido para anÃ¡lise"""
        # Ignora __pycache__, .venv, etc
        exclude_dirs = {'.venv', '__pycache__', '.git', 'venv', 'env'}
        return not any(part in exclude_dirs for part in path.parts)
    
    def _is_main_file(self, path: Path) -> bool:
        """Identifica se Ã© arquivo principal/importante"""
        important_names = {
            'runner', 'parser', 'engine', 'main', 
            'pipeline', 'extractor', 'processor'
        }
        stem = path.stem.lower()
        return any(name in stem for name in important_names)

