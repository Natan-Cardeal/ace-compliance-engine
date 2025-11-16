import csv
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent  # .../ACE/scripts -> /ACE
DB_DIR = ROOT / "db"
GL_EXPORT_PATH = DB_DIR / "gl_export.csv"
GL_REQUIREMENTS_PATH = DB_DIR / "requirements_gl.csv"
GL_COMPLIANCE_EXPORT_PATH = DB_DIR / "gl_compliance.csv"


def _to_float(value: str) -> Optional[float]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def load_requirements() -> dict:
    if not GL_REQUIREMENTS_PATH.exists():
        raise SystemExit(
            f"Arquivo de requisitos não encontrado: {GL_REQUIREMENTS_PATH}\n"
            f"Crie um CSV com colunas: profile,min_each_occ,min_agg."
        )
    with GL_REQUIREMENTS_PATH.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        raise SystemExit(f"Arquivo de requisitos {GL_REQUIREMENTS_PATH} está vazio.")
    # por enquanto usamos sempre a primeira linha (profile default)
    row = rows[0]
    req = {
        "profile": row.get("profile") or "default",
        "min_each_occ": _to_float(row.get("min_each_occ") or ""),
        "min_agg": _to_float(row.get("min_agg") or ""),
    }
    if req["min_each_occ"] is None or req["min_agg"] is None:
        raise SystemExit(
            f"Requisitos inválidos em {GL_REQUIREMENTS_PATH}: "
            f"min_each_occ e min_agg são obrigatórios."
        )
    return req


def run():
    if not GL_EXPORT_PATH.exists():
        raise SystemExit(
            f"Arquivo de export GL não encontrado: {GL_EXPORT_PATH}\n"
            f"Rode primeiro o script que gera gl_export.csv."
        )

    req = load_requirements()
    print("=== GL Compliance Check (ACORD 25 / GL) ===")
    print(
        f"Usando requisitos profile='{req['profile']}', "
        f"min_each_occ={req['min_each_occ']:.0f}, "
        f"min_agg={req['min_agg']:.0f}\n"
    )

    with GL_EXPORT_PATH.open(newline="", encoding="utf-8-sig") as f_in, \
            GL_COMPLIANCE_EXPORT_PATH.open("w", newline="", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in)
        fieldnames = reader.fieldnames + ["gl_compliance_status", "gl_compliance_reason"]
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        total = 0
        ok = 0
        fail = 0

        for row in reader:
            total += 1
            status = (row.get("extraction_status") or "").upper()
            cert_id = row.get("certificate_id")

            if status != "SUCCESS":
                comp_status = "NOT_EVALUATED"
                reason = f"extraction_status={status}"
            else:
                each_occ = _to_float(row.get("GL_EACH_OCC") or "")
                agg = _to_float(row.get("GL_AGGREGATE") or "")

                missing = []
                if each_occ is None:
                    missing.append("GL_EACH_OCC")
                if agg is None:
                    missing.append("GL_AGGREGATE")

                if missing:
                    comp_status = "NON_COMPLIANT"
                    reason = "missing limits: " + ", ".join(missing)
                    fail += 1
                else:
                    breaches = []
                    if each_occ < req["min_each_occ"]:
                        breaches.append(f"EACH_OCC<{req['min_each_occ']:.0f}")
                    if agg < req["min_agg"]:
                        breaches.append(f"AGG<{req['min_agg']:.0f}")

                    if breaches:
                        comp_status = "NON_COMPLIANT"
                        reason = "; ".join(breaches)
                        fail += 1
                    else:
                        comp_status = "COMPLIANT"
                        reason = ""
                        ok += 1

            row["gl_compliance_status"] = comp_status
            row["gl_compliance_reason"] = reason
            writer.writerow(row)

            print(f"Certificate {cert_id}: {comp_status} {('- ' + reason) if reason else ''}")

    print("\nResumo:")
    print(f"  Total analisados: {total}")
    print(f"  COMPLIANT: {ok}")
    print(f"  NON_COMPLIANT: {fail}")
    print(f"  Resultado salvo em: {GL_COMPLIANCE_EXPORT_PATH}")


if __name__ == "__main__":
    run()
