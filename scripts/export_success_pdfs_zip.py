import sys
import shutil
import zipfile
from pathlib import Path

from ace.data_model.db import get_connection, DB_PATH


OUTPUT_DIR = Path("db") / "success_pdfs"
ZIP_PATH = Path("db") / "success_pdfs_gl_sample.zip"


def export_success_pdfs(limit: int = 50) -> None:
    """
    Copia PDFs dos certificates com extraction_status = 'SUCCESS'
    (limitados a N registros) para uma pasta local e gera um ZIP.

    - OUTPUT_DIR: db/success_pdfs
    - ZIP_PATH:   db/success_pdfs_gl_sample.zip
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        rows = cur.execute(
            """
            SELECT c.id AS certificate_id,
                   d.storage_path
              FROM certificates c
              JOIN documents d ON d.id = c.document_id
             WHERE c.extraction_status = 'SUCCESS'
             ORDER BY c.id
             LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        print("Nenhum certificate com status SUCCESS encontrado.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Usando banco em: {DB_PATH}")
    print(f"Copiando PDFs para: {OUTPUT_DIR.resolve()}")
    print(f"Total previsto (limit): {len(rows)}\n")

    copied = 0
    for row in rows:
        cid = row["certificate_id"]
        src = Path(row["storage_path"])

        if not src.exists():
            print(f"[WARN] Arquivo não encontrado para cert {cid}: {src}")
            continue

        dst_name = f"cert_{cid:04d}__{src.name}"
        dst = OUTPUT_DIR / dst_name

        try:
            shutil.copy2(src, dst)
            print(f"[OK] Cert {cid} -> {dst.name}")
            copied += 1
        except Exception as e:
            print(f"[ERRO] Ao copiar cert {cid} ({src}): {e}")

    if copied == 0:
        print("\nNenhum arquivo copiado, ZIP não será criado.")
        return

    # Gera o ZIP
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in OUTPUT_DIR.iterdir():
            if path.is_file():
                zf.write(path, arcname=path.name)

    print("\nResumo:")
    print(f"  Arquivos copiados: {copied}")
    print(f"  ZIP criado em:     {ZIP_PATH.resolve()}")


def main() -> None:
    limit = 50
    if len(sys.argv) >= 2:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            print(f"Limite inválido: {sys.argv[1]!r}, usando padrão 50.")
    export_success_pdfs(limit=limit)


if __name__ == "__main__":
    main()
