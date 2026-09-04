"""Generate 450 short, original text documents about Databases
and save them as txt files in backend/data/raw_docs/.

Run: python backend/scripts/generate_database_docs.py
"""
from pathlib import Path
import random

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "raw_docs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Seed for reproducibility
random.seed(42)

# A set of base topics and angles to combine for variety
topics = [
    "Relational model",
    "Normalization",
    "ACID properties",
    "BASE model",
    "Indexing",
    "B-tree indexes",
    "Hash indexes",
    "Transactions",
    "Isolation levels",
    "Concurrency control",
    "MVCC",
    "Query optimization",
    "Joins",
    "Foreign keys",
    "Denormalization",
    "OLTP vs OLAP",
    "NoSQL overview",
    "Document stores",
    "Key-value stores",
    "Column-family stores",
    "Graph databases",
    "CAP theorem",
    "Distributed transactions",
    "Two-phase commit",
    "Consensus (Paxos/Raft)",
    "Sharding",
    "Replication",
    "Eventual consistency",
    "Strong consistency",
    "Materialized views",
    "Stored procedures",
    "Triggers",
    "Constraints",
    "Backup and recovery",
    "Write-ahead log (WAL)",
    "Checkpoints",
    "Point-in-time recovery",
    "Snapshot isolation",
    "Log-structured merge trees (LSM)",
    "RocksDB/LevelDB internals",
    "Full-text search",
    "Inverted indexes",
    "Columnar storage",
    "Compression",
    "Data modeling",
    "ER diagrams",
    "Data warehouses",
    "Star schema",
    "Snowflake schema",
    "ETL pipelines",
    "Change data capture (CDC)",
    "Streaming ingestion",
    "Kafka integration",
    "Query planner",
    "Explain analyze",
    "Statistics and histograms",
    "Cardinality estimation",
    "Cost-based optimization",
    "Query rewriting",
    "Bloom filters",
    "Buffer pool",
    "Caching strategies",
    "LRU and CLOCK algorithms",
    "Page size and layout",
    "Write amplification",
    "Compaction",
    "Durability vs performance",
    "Garbage collection in DBs",
    "Temporal databases",
    "Versioned rows",
    "Time-series databases",
    "Event sourcing",
    "Schema migrations",
    "Online schema change",
    "Foreign data wrappers",
    "Serverless databases",
    "Connection pooling",
    "Prepared statements",
    "Parameterized queries",
    "ORM trade-offs",
    "ACID in distributed systems",
    "Hybrid transactional/analytical processing (HTAP)",
    "Federated queries",
    "Geospatial indexing",
    "Spatial queries",
    "JSON data types",
    "Query caching",
    "Materialized query tables",
    "Adaptive indexing",
    "Columnar compression codecs",
    "Security: authentication and authorization",
    "Encryption at rest",
    "Encryption in transit",
]

angles = [
    "Concept overview",
    "Use case and example",
    "Common pitfalls",
    "Performance tips",
    "Implementation notes",
    "Historical context",
    "Comparison with alternatives",
    "Trade-offs",
    "Best practices",
    "Short tutorial",
]

# Simple sentence templates to produce short documents
templates = [
    "{topic}: {angle}. {sentence1} {sentence2} {sentence3}",
    "{topic} ({angle}). {sentence1} {sentence2}",
    "{topic} — {angle}. {sentence1} {sentence2} {sentence3} {sentence4}",
]

# Phrase fragments to build sentences
starts = [
    "This focuses on",
    "At its core, it means",
    "A typical example is",
    "It helps with",
    "Be careful about",
    "A common optimization is",
    "It contrasts with",
]

middles = [
    "handling concurrent access",
    "reducing disk I/O",
    "simplifying schema evolution",
    "achieving low-latency reads",
    "scaling writes horizontally",
    "preserving transactional guarantees",
    "trading strong consistency for availability",
    "improving throughput in analytics workloads",
]

ends = [
    "using locks or MVCC depending on the engine.",
    "by creating appropriate indexes and statistics.",
    "and is often used in analytics pipelines.",
    "which can complicate migrations over time.",
    "that can be mitigated with sharding or replication.",
    "and requires careful tuning of buffer pools.",
]

# Helper to build a short random sentence
def build_sentence():
    return random.choice(starts) + " " + random.choice(middles) + " " + random.choice(ends)

# Generate 450 document contents
num_docs = 450
manifest_lines = []
for i in range(1, num_docs + 1):
    topic = random.choice(topics)
    angle = random.choice(angles)
    template = random.choice(templates)
    # Vary number of sentences
    s1 = build_sentence()
    s2 = build_sentence()
    s3 = build_sentence()
    s4 = build_sentence()
    content = template.format(topic=topic, angle=angle, sentence1=s1, sentence2=s2, sentence3=s3, sentence4=s4)
    # Ensure short: trim to 3 sentences if too long
    # Save with a title and short body
    title = f"{topic} — {angle}"
    body = content
    doc_text = title + "\n\n" + body + "\n"
    filename = f"doc_{i:03d}.txt"
    with open(OUT_DIR / filename, "w", encoding="utf-8") as f:
        f.write(doc_text)
    manifest_lines.append(f"{filename}\t{topic}\t{angle}")

# Write manifest
with open(OUT_DIR / "manifest.tsv", "w", encoding="utf-8") as f:
    f.write("filename\ttopic\tangle\n")
    f.write("\n".join(manifest_lines))

print(f"Generated {num_docs} documents in: {OUT_DIR}")
print("Sample file: doc_001.txt")

# Print first 3 filenames for quick check
print("Files:")
for p in sorted(OUT_DIR.glob("doc_*.txt"))[:3]:
    print(p.name)
