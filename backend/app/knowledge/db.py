"""Embedded SQLite Relational Knowledge & Evidence Graph Engine for TrustLens"""
import os
import sqlite3
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("trustlens.knowledge.db")

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "trustlens_knowledge.db"


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Returns a thread-safe connection to the embedded SQLite database
    with foreign keys and dict-like row factories enabled.
    """
    path = db_path or os.getenv("TRUSTLENS_DB_PATH", str(DEFAULT_DB_PATH))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")  # High-concurrency WAL mode
    return conn


def ensure_schema(db_path: Optional[str] = None) -> None:
    """
    Initializes the relational schema for Workspaces, Knowledge Graph,
    Claim Graph, Evidence Graph, Semantic Rules, Chunk Embeddings, and
    Data Analyst Profiles.

    Must be called explicitly at the application lifecycle point (not imported):
    - ``app.main`` lifespan startup for the default database.
    - ``UserKnowledgeContext`` construction for per-user databases.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # 1. Workspaces
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workspaces (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Documents (User-uploaded files, notes, reports, CSVs)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        title TEXT NOT NULL,
        filename TEXT NOT NULL,
        file_type TEXT NOT NULL,
        raw_content TEXT,
        authority_level TEXT DEFAULT 'MEDIUM',
        metadata_json TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
    );
    """)

    # 3. Document Chunks (Precise passage coordinates)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        document_id TEXT NOT NULL,
        chunk_index INTEGER NOT NULL,
        text TEXT NOT NULL,
        location_info TEXT, -- e.g. "Section 2.1", "Row 42", "Page 5"
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    );
    """)

    # 4. Knowledge Graph: Entities
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS entities (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        name TEXT NOT NULL,
        normalized_name TEXT NOT NULL,
        entity_type TEXT NOT NULL, -- Person, Org, Product, Project, Metric, Concept, Event
        aliases_json TEXT DEFAULT '[]',
        metadata_json TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
    );
    """)

    # 5. Knowledge Graph: Relationships
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS relationships (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        source_entity_id TEXT NOT NULL,
        target_entity_id TEXT NOT NULL,
        relation_type TEXT NOT NULL, -- founded, mentions, depends_on, contradicts, supports, part_of
        evidence_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
        FOREIGN KEY (source_entity_id) REFERENCES entities(id) ON DELETE CASCADE,
        FOREIGN KEY (target_entity_id) REFERENCES entities(id) ON DELETE CASCADE
    );
    """)

    # 6. Claim Graph: Atomic Factual Claims
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS claims (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        document_id TEXT,
        statement TEXT NOT NULL,
        normalized_statement TEXT,
        claim_type TEXT DEFAULT 'FACTUAL',
        status TEXT DEFAULT 'UNRESOLVED', -- SUPPORTED, PARTIALLY_SUPPORTED, CONTRADICTED, UNSUPPORTED, UNRESOLVED
        confidence REAL DEFAULT 0.5,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    );
    """)

    # 7. Evidence Graph: First-class Evidentiary Links
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evidence (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        claim_id TEXT NOT NULL,
        document_id TEXT NOT NULL,
        chunk_id TEXT,
        exact_passage TEXT NOT NULL,
        location_ref TEXT, -- e.g. "Page 3, Paragraph 2", "Row 15, Column 'Revenue'"
        relationship_type TEXT DEFAULT 'SUPPORTS', -- SUPPORTS, CONTRADICTS, QUALIFIES
        strength REAL DEFAULT 0.8,
        explanation TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
        FOREIGN KEY (claim_id) REFERENCES claims(id) ON DELETE CASCADE,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
        FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE
    );
    """)

    # 8. Chronological Timeline Events
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        document_id TEXT,
        title TEXT NOT NULL,
        date_str TEXT NOT NULL,
        timestamp_val REAL,
        description TEXT,
        location_ref TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    );
    """)

    # 9. User-Controlled Semantic Memory & Rules
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS semantic_rules (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        rule_type TEXT NOT NULL, -- term_definition, entity_alias, authority_override, constraint
        rule_key TEXT NOT NULL,
        rule_value TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
    );
    """)

    # 10. Data Analyst: Structured Dataset Profiles
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dataset_profiles (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        document_id TEXT NOT NULL,
        row_count INTEGER NOT NULL,
        col_count INTEGER NOT NULL,
        columns_json TEXT NOT NULL,
        profile_json TEXT NOT NULL,
        insights_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    );
    """)

    # 11. Chunk Embeddings (lightweight persistent vector store for workspace RAG)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chunk_embeddings (
        chunk_id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        embedding BLOB NOT NULL,
        dim INTEGER NOT NULL,
        model TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
    );
    """)

    # Indexes for lightning fast workspace-scoped lookups
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_docs_workspace ON documents(workspace_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_workspace ON chunks(workspace_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_workspace ON entities(workspace_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_claims_workspace ON claims(workspace_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_claim ON evidence(claim_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_workspace ON events(workspace_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rules_workspace ON semantic_rules(workspace_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunk_embeddings_workspace ON chunk_embeddings(workspace_id);")

    conn.commit()
    conn.close()
    logger.info("TrustLens Knowledge Schema initialized at %s", db_path or DEFAULT_DB_PATH)


# Backward-compatible alias for callers that referenced the old name.
init_knowledge_schema = ensure_schema
