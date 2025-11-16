import csv
import os
from typing import Dict, Any, Optional


GL_EXPORT_PATH = os.path.join("db", "gl_export.csv")
GROUND_TRUTH_PATH = os.path.join("db", "gl_ground_truth.csv")
DISAGREEMENTS_PATH = os.path.join("db", "gl_oracle_disagreements.csv")


FIELDS_TO_COMPARE = [
    # campos de metadados de apólice
    "policy_number",
    "effective_date",
    "expiration_date",
    # campos de limites GL
    "gl_aggregate",
    "gl_each_occurrence",
]


def normalize_text(value: str) -> Optional[str]:
    if value is None:
        return None
    v = str(value).strip()
    if not v:
        return None
    return v.upper()


def normalize_numeric(value: str) -> Optional[float]:
    if value is None:
        return None
    v = str(value).strip()
    if not v:
        return None

    # remove símbolos comuns de dinheiro e separadores
    for ch in ["$", ","]:
        v = v.replace(ch, "")
    v = v.strip()

    if not v:
        return None

    try:
        return float(v)
    except ValueError:
        return None


def normalize_value(field: str, value: str) -> Optional[Any]:
    if field in ("gl_aggregate", "gl_each_occurrence"):
        return normalize_numeric(value)
    # para datas e policy_number, tratamos como texto
    return normalize_text(value)


def load_csv_by_cert_id(path: str) -> Dict[str, Dict[str, str]]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    data: Dict[str, Dict[str, str]] = {}
    for row in rows:
        cid = str(row.get("certificate_id") or "").strip()
        if not cid:
            # ignora linhas sem ID
            continue
        if cid in data:
            # se tiver duplicado, mantém o primeiro (pode ajustar depois)
            continue
        data[cid] = row
    return data


def main() -> None:
    print(f"Lendo extrações do ACE em: {GL_EXPORT_PATH}")
    ace_data = load_csv_by_cert_id(GL_EXPORT_PATH)

    print(f"Lendo ground truth do LLM em: {GROUND_TRUTH_PATH}")
    oracle_data = load_csv_by_cert_id(GROUND_TRUTH_PATH)

    # estrutura de métricas por campo
    metrics: Dict[str, Dict[str, int]] = {
        f: {"evaluated": 0, "matches": 0, "mismatches": 0, "only_truth": 0, "only_pred": 0}
        for f in FIELDS_TO_COMPARE
    }

    disagreements = []

    common_ids = sorted(set(ace_data.keys()) & set(oracle_data.keys()))
    print(f"Total de certificados com ACE + Oráculo: {len(common_ids)}")

    for cid in common_ids:
        ace_row = ace_data[cid]
        truth_row = oracle_data[cid]

        row_has_disagreement = False
        row_diff: Dict[str, Any] = {"certificate_id": cid}

        for field in FIELDS_TO_COMPARE:
            pred_raw = ace_row.get(field)
            truth_raw = truth_row.get(field)

            pred = normalize_value(field, pred_raw)
            truth = normalize_value(field, truth_raw)

            m = metrics[field]

            if truth is None and pred is None:
                # nada para avaliar
                continue
            if truth is not None and pred is None:
                m["only_truth"] += 1
                row_has_disagreement = True
            elif truth is None and pred is not None:
                m["only_pred"] += 1
                row_has_disagreement = True
            else:
                # ambos não nulos, podemos avaliar
                m["evaluated"] += 1
                if pred == truth:
                    m["matches"] += 1
                else:
                    m["mismatches"] += 1
                    row_has_disagreement = True

            # sempre guardamos os valores brutos para inspeção
            row_diff[f"{field}_ace"] = pred_raw
            row_diff[f"{field}_truth"] = truth_raw

        if row_has_disagreement:
            disagreements.append(row_diff)

    # salvar CSV de divergências
    if disagreements:
        fieldnames = sorted({k for row in disagreements for k in row.keys()})
        with open(DISAGREEMENTS_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(disagreements)
        print(f"Divergências salvas em: {DISAGREEMENTS_PATH}")
    else:
        print("Nenhuma divergência encontrada para os campos analisados.")

    print("\n=== Métricas por campo ===")
    for field, m in metrics.items():
        evaluated = m["evaluated"]
        matches = m["matches"]
        mismatches = m["mismatches"]
        only_truth = m["only_truth"]
        only_pred = m["only_pred"]

        acc = (matches / evaluated * 100.0) if evaluated > 0 else 0.0

        print(f"\nCampo: {field}")
        print(f"  avaliados  : {evaluated}")
        print(f"  matches    : {matches}")
        print(f"  mismatches : {mismatches}")
        print(f"  only_truth : {only_truth}  (oráculo tem valor, ACE não)")
        print(f"  only_pred  : {only_pred}   (ACE tem valor, oráculo não)")
        print(f"  acurácia   : {acc:5.1f}%")

    print("\nResumo concluído.")


if __name__ == "__main__":
    main()
