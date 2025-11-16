import sys
from pathlib import Path
import hashlib
import sqlite3

from ace.data_model.db import get_connection, DB_PATH


def hash_file(path: Path) -> str:
    """
    Calcula SHA256 de um arquivo em chunks.
    """
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def ingest_folder(root: Path, max_files: int | None = None) -> None:
    """
    Varre a pasta root recursivamente, encontrando PDFs,
    e cria entries em documents + certificates.

    Mais robusto:
      - sempre faz SELECT pra obter document_id
      - não derruba ingestão inteira se um arquivo der erro
    """
    conn = get_connection()
    try:
        print(f"Usando banco em: {DB_PATH}")
        print(f"Iniciando ingestão a partir de: {root}")

        pdf_paths = list(root.rglob("*.pdf"))
        total_found = len(pdf_paths)
        print(f"Encontrados {total_found} PDFs.")

        if max_files is not None:
            pdf_paths = pdf_paths[:max_files]
            print(f"Limitando ingestão aos primeiros {max_files} arquivos.")

        new_documents = 0
        new_certificates = 0
        skipped = 0

        for idx, pdf_path in enumerate(pdf_paths, start=1):
            pdf_path = pdf_path.resolve()
            print(f"[{idx}/{len(pdf_paths)}] Ingerindo: {pdf_path}")

            try:
                file_hash = hash_file(pdf_path)

                # 1) Documents: INSERT OR IGNORE
                before_changes = conn.total_changes
                conn.execute(
                    """
                    INSERT OR IGNORE INTO documents (file_hash, storage_path, doc_type, source_system)
                    VALUES (?, ?, ?, ?)
                    """,
                    (file_hash, str(pdf_path), "COI_ACORD25", "BULK_IMPORT_GRAY"),
                )
                after_changes = conn.total_changes
                if after_changes > before_changes:
                    new_documents += 1

                # 2) Buscar SEMPRE o id pelo hash
                row = conn.execute(
                    "SELECT id FROM documents WHERE file_hash = ?",
                    (file_hash,),
                ).fetchone()

                if not row:
                    print(f"[ERRO] Não foi possível recuperar document_id para {pdf_path} (hash={file_hash}). Pulando.")
                    skipped += 1
                    continue

                document_id = row["id"]

                # 3) Certificates: um por document (por enquanto)
                conn.execute(
                    """
                    INSERT INTO certificates (
                        document_id,
                        client_id,
                        project_id,
                        vendor_id,
                        certificate_date,
                        certificate_status,
                        extraction_status
                    )
                    VALUES (?, ?, ?, ?, NULL, 'NEW', 'PENDING')
                    """,
                    (
                        document_id,
                        1,   # client_id dummy
                        1,   # project_id dummy
                        None # vendor_id
                    ),
                )
                new_certificates += 1

            except sqlite3.IntegrityError as e:
                # Não derruba tudo, só loga e segue
                print(f"[ERRO] IntegrityError ao ingerir {pdf_path}: {e}. Pulando.")
                skipped += 1
            except Exception as e:
                print(f"[ERRO] Falha inesperada ao ingerir {pdf_path}: {e}. Pulando.")
                skipped += 1

        conn.commit()
        print("Ingestão concluída.")
        print(f"Novos documents: {new_documents}")
        print(f"Novos certificates: {new_certificates}")
        print(f"Arquivos pulados por erro: {skipped}")

    finally:
        conn.close()


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: py scripts\\ingest_from_folder.py <caminho_da_pasta> [max_files]")
        raise SystemExit(1)

    root = Path(sys.argv[1]).expanduser().resolve()
    if not root.exists():
        print(f"Pasta não encontrada: {root}")
        raise SystemExit(1)

    max_files = None
    if len(sys.argv) >= 3:
        max_files = int(sys.argv[2])

    ingest_folder(root, max_files=max_files)


if __name__ == "__main__":
    main()
