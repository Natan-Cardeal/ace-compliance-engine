from ace.data_model.db import get_connection, DB_PATH

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_hash       TEXT NOT NULL,
    storage_path    TEXT NOT NULL,
    doc_type        TEXT NOT NULL,
    source_system   TEXT,
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_hash)
);

CREATE TABLE IF NOT EXISTS certificates (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id         INTEGER NOT NULL,
    client_id           INTEGER,
    project_id          INTEGER,
    vendor_id           INTEGER,
    certificate_date    TEXT,
    certificate_status  TEXT NOT NULL DEFAULT 'NEW',
    extraction_status   TEXT NOT NULL DEFAULT 'PENDING',
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TEXT,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

CREATE TABLE IF NOT EXISTS extraction_runs (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id      INTEGER NOT NULL,
    run_type         TEXT NOT NULL,
    ocr_provider     TEXT,
    parser_version   TEXT,
    ml_model_version TEXT,
    started_at       TEXT NOT NULL,
    finished_at      TEXT,
    status           TEXT NOT NULL,
    error_message    TEXT,
    created_at       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

CREATE TABLE IF NOT EXISTS policies (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    certificate_id            INTEGER NOT NULL,
    lob_code                  TEXT NOT NULL,
    carrier_name              TEXT,
    policy_number             TEXT,
    effective_date            TEXT,
    expiration_date           TEXT,
    cancellation_notice_days  INTEGER,

    source_method        TEXT NOT NULL DEFAULT 'PARSER',
    source_detail        TEXT,
    confidence_score     REAL,
    extraction_run_id    INTEGER,
    is_reviewed          INTEGER NOT NULL DEFAULT 0,
    reviewed_by          TEXT,
    reviewed_at          TEXT,
    created_at           TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           TEXT,

    CHECK (confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)),
    FOREIGN KEY (certificate_id) REFERENCES certificates(id),
    FOREIGN KEY (extraction_run_id) REFERENCES extraction_runs(id)
);

CREATE TABLE IF NOT EXISTS coverages (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_id               INTEGER NOT NULL,
    coverage_code           TEXT NOT NULL,
    limit_amount            REAL,
    limit_currency          TEXT,
    deductible_amount       REAL,
    deductible_currency     TEXT,
    occurrence_or_aggregate TEXT,

    source_method        TEXT NOT NULL DEFAULT 'PARSER',
    source_detail        TEXT,
    confidence_score     REAL,
    extraction_run_id    INTEGER,
    is_reviewed          INTEGER NOT NULL DEFAULT 0,
    reviewed_by          TEXT,
    reviewed_at          TEXT,
    created_at           TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           TEXT,

    CHECK (confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)),
    FOREIGN KEY (policy_id) REFERENCES policies(id),
    FOREIGN KEY (extraction_run_id) REFERENCES extraction_runs(id)
);

CREATE TABLE IF NOT EXISTS policy_clauses (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_id           INTEGER NOT NULL,
    clause_code         TEXT NOT NULL,
    clause_description  TEXT,
    applies_to_lob      TEXT,

    source_method        TEXT NOT NULL DEFAULT 'PARSER',
    source_detail        TEXT,
    confidence_score     REAL,
    extraction_run_id    INTEGER,
    is_reviewed          INTEGER NOT NULL DEFAULT 0,
    reviewed_by          TEXT,
    reviewed_at          TEXT,
    created_at           TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           TEXT,

    CHECK (confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)),
    FOREIGN KEY (policy_id) REFERENCES policies(id),
    FOREIGN KEY (extraction_run_id) REFERENCES extraction_runs(id)
);

CREATE TABLE IF NOT EXISTS coverage_requirements (
    id                                   INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id                            INTEGER,
    project_id                           INTEGER,
    property_id                          INTEGER,
    lob_code                             TEXT NOT NULL,
    requirement_scope                    TEXT NOT NULL,
    requirement_name                     TEXT,
    effective_from                       TEXT NOT NULL,
    effective_to                         TEXT,
    is_active                            INTEGER NOT NULL DEFAULT 1,
    gl_each_occurrence_min               REAL,
    gl_general_aggregate_min             REAL,
    auto_csl_min                         REAL,
    requires_wc_coverage                 INTEGER NOT NULL DEFAULT 0,
    employers_liability_each_acc_min     REAL,
    requires_additional_insured          INTEGER NOT NULL DEFAULT 0,
    requires_waiver_subrogation          INTEGER NOT NULL DEFAULT 0,
    requires_primary_non_contributory    INTEGER NOT NULL DEFAULT 0,
    requirement_notes                    TEXT,
    created_at                           TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by                           TEXT,
    updated_at                           TEXT,
    updated_by                           TEXT
);

CREATE TABLE IF NOT EXISTS compliance_evaluation (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    certificate_id      INTEGER NOT NULL,
    lob_code            TEXT NOT NULL,
    evaluation_run_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    engine_version      TEXT,
    requirement_id      INTEGER,
    requirement_version TEXT,
    status              TEXT NOT NULL,
    gap_count           INTEGER NOT NULL DEFAULT 0,
    gap_summary         TEXT,
    expiration_risk     TEXT,
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (certificate_id) REFERENCES certificates(id),
    FOREIGN KEY (requirement_id) REFERENCES coverage_requirements(id)
);
"""


def init_db() -> None:
    print(f"Usando banco em: {DB_PATH}")
    conn = get_connection()
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        print("Schema criado/atualizado com sucesso.")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
