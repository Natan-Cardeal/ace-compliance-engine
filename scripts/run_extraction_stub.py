import sys

from ace.data_model.db import DB_PATH
from ace.extraction.runner import run_extraction_for_certificate


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: py scripts\\run_extraction_stub.py <certificate_id>")
        sys.exit(1)

    certificate_id = int(sys.argv[1])
    print(f"Usando banco em: {DB_PATH}")
    run_extraction_for_certificate(certificate_id)


if __name__ == "__main__":
    main()
