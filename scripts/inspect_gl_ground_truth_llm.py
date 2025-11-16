import csv
import os

GROUND_TRUTH_PATH = os.path.join("db", "gl_ground_truth.csv")

MAIN_FIELDS = [
    "policy_number",
    "effective_date",
    "expiration_date",
    "gl_aggregate",
    "gl_each_occurrence",
    "notes",
]

ERROR_FIELDS = ["_llm_error", "_parse_error"]


def is_filled(v: str) -> bool:
    if v is None:
        return False
    v = str(v).strip()
    if v == "" or v.lower() == "null" or v.lower() == "none":
        return False
    return True


def main() -> None:
    if not os.path.exists(GROUND_TRUTH_PATH):
        raise FileNotFoundError(f"Arquivo não encontrado: {GROUND_TRUTH_PATH}")

    with open(GROUND_TRUTH_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    total = len(rows)
    print(f"Arquivo: {GROUND_TRUTH_PATH}")
    print(f"Total de linhas (certificados): {total}")
    print()

    # Contar erros
    for ef in ERROR_FIELDS:
        if ef in rows[0].keys():
            count_err = sum(1 for r in rows if is_filled(r.get(ef)))
            print(f"{ef}: {count_err} linhas com valor")
    print()

    # Cobertura por campo principal
    print("=== Cobertura por campo (não-nulos) ===")
    for field in MAIN_FIELDS:
        if field not in rows[0].keys():
            print(f"{field}: NÃO ENCONTRADO NO CSV")
            continue
        count_nonnull = sum(1 for r in rows if is_filled(r.get(field)))
        print(f"{field:18s}: {count_nonnull:4d} / {total}")

    print("\n=== Amostras de linhas sem erro de LLM/parse ===")
    clean_rows = [
        r for r in rows
        if not any(is_filled(r.get(e)) for e in ERROR_FIELDS if e in r)
    ]
    print(f"Linhas consideradas 'OK' (sem _llm_error/_parse_error): {len(clean_rows)}\n")

    # Mostrar até 3 exemplos
    for sample in clean_rows[:3]:
        cid = sample.get("certificate_id") or sample.get("id") or "N/A"
        print(f"certificate_id: {cid}")
        for field in MAIN_FIELDS:
            if field in sample:
                print(f"  {field}: {sample[field]}")
        print("-" * 40)


if __name__ == "__main__":
    main()
