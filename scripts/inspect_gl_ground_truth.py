import csv
import os
from collections import Counter

PATH = os.path.join("db", "gl_ground_truth.csv")

def main() -> None:
    if not os.path.exists(PATH):
        print(f"Arquivo não encontrado: {PATH}")
        return

    with open(PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Arquivo: {PATH}")
    print(f"Total de linhas: {len(rows)}")
    print("\nCampos (headers):")
    print(", ".join(reader.fieldnames or []))

    # mostrar primeiras 3 linhas pra entender o formato
    print("\n=== Amostra das 3 primeiras linhas ===")
    for row in rows[:3]:
        print("---")
        for k, v in row.items():
            if v:
                print(f"{k}: {v}")

    # contar quantas linhas têm cada campo não vazio
    fields_to_check = [
        "policy_number",
        "effective_date",
        "expiration_date",
        "gl_aggregate",
        "gl_each_occurrence",
        "_parse_error",
        "_llm_error",
    ]

    print("\n=== Presença de campos ===")
    for field in fields_to_check:
        cnt = sum(1 for r in rows if (r.get(field) or "").strip())
        print(f"{field}: {cnt} linhas com valor")

if __name__ == "__main__":
    main()
