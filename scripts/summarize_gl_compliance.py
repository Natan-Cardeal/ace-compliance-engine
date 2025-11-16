import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # .../ACE/scripts -> /ACE
DB_DIR = ROOT / "db"
GL_COMPLIANCE_EXPORT_PATH = DB_DIR / "gl_compliance.csv"


def run():
    if not GL_COMPLIANCE_EXPORT_PATH.exists():
        raise SystemExit(
            f"Arquivo de compliance não encontrado: {GL_COMPLIANCE_EXPORT_PATH}\n"
            f"Rode primeiro run_gl_compliance_from_csv.py."
        )

    status_counter = Counter()
    reason_counter = Counter()
    not_evaluated_projects = Counter()

    with GL_COMPLIANCE_EXPORT_PATH.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            status = (row.get("gl_compliance_status") or "").upper()
            reason = (row.get("gl_compliance_reason") or "").strip()
            project = row.get("project_name") or row.get("project") or ""

            status_counter[status] += 1
            if status == "NON_COMPLIANT" and reason:
                reason_counter[reason] += 1
            if status == "NOT_EVALUATED" and project:
                not_evaluated_projects[project] += 1

    print("=== GL Compliance Summary ===\n")
    print("Por status:")
    for k, v in status_counter.items():
        print(f"  {k or '(vazio)'}: {v}")

    print("\nTop motivos NON_COMPLIANT:")
    if not reason_counter:
        print("  (nenhum motivo registrado)")
    else:
        for reason, count in reason_counter.most_common(10):
            print(f"  {count:3d}x  {reason}")

    if not_evaluated_projects:
        print("\nProjetos com mais NOT_EVALUATED (problema de extração):")
        for project, count in not_evaluated_projects.most_common(10):
            print(f"  {count:3d}x  {project}")


if __name__ == "__main__":
    run()
