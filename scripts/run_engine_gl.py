import sys

from ace.data_model.db import DB_PATH
from ace.engine.gl_evaluator import evaluate_gl_for_certificate


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: py scripts\\run_engine_gl.py <certificate_id>")
        raise SystemExit(1)

    certificate_id = int(sys.argv[1])
    print(f"Usando banco em: {DB_PATH}")
    evaluate_gl_for_certificate(certificate_id)


if __name__ == "__main__":
    main()
