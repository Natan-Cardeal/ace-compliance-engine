"""
Git Handler - Gerencia operações com repositórios Git
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CommitInfo:
    hash: str
    author: str
    date: datetime
    message: str
    files_changed: List[str]


class GitHandler:
    def __init__(self, repo_path: str = None):
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()

    def get_recent_commits(self, n: int = 10) -> List[CommitInfo]:
        """Retorna os N commits mais recentes.

        Se o repositório não for um repositório git válido ou se o comando git
        falhar por qualquer motivo, devolve uma lista vazia ao invés de
        levantar exceção. Isso permite usar o validador mesmo em projetos que
        ainda não estão versionados em git.
        """
        cmd = ["log", f"-{n}", "--pretty=format:%H|%an|%ad|%s", "--date=iso"]
        output = self._run_git_command(cmd)
        if not output:
            return []

        commits: List[CommitInfo] = []

        for line in output.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 3)
            if len(parts) != 4:
                continue
            hash_val, author, date_str, message = parts
            try:
                dt = datetime.fromisoformat(
                    date_str.replace(" ", "T").split("+")[0]
                )
            except ValueError:
                dt = datetime.min

            commits.append(
                CommitInfo(
                    hash=hash_val[:8],
                    author=author,
                    date=dt,
                    message=message,
                    files_changed=[],
                )
            )
        return commits

    def get_file_content(self, file_path: str) -> Optional[str]:
        full_path = self.repo_path / file_path
        if full_path.exists():
            return full_path.read_text(encoding="utf-8")
        return None

    def _run_git_command(self, args: List[str]) -> str:
        """Executa um comando git de forma segura.

        - Se git não estiver instalado, ou
        - Se o diretório não for um repositório git válido, ou
        - Se o comando falhar (exit status diferente de 0),

        retorna string vazia ao invés de levantar exceção.
        """
        cmd = ["git", "-C", str(self.repo_path)] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Sem git ou diretório não é repo: devolve string vazia
            return ""

    def get_repo_summary(self) -> Dict:
        """Resumo simples do repositório.

        Se não for possível usar git, preenche branch/commit como
        "unknown" em vez de quebrar o fluxo.
        """
        branch = (
            self._run_git_command(["branch", "--show-current"]).strip()
            or "unknown"
        )
        last_commit = (
            self._run_git_command(["rev-parse", "HEAD"]).strip()[:8]
            or "unknown"
        )

        return {
            "repo_path": str(self.repo_path),
            "current_branch": branch,
            "last_commit": last_commit,
        }
