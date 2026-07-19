# Endpoint security validation bot

## Structure
```
config.py                # all tunables: DATABASE_URL, models, thresholds
models.py                # pydantic contracts (Asset, ControlRecord, Finding, etc.)
sql/sqlite-schema.sql    # DDL: assets / av_controls / edr_controls tables + drift view
scripts/import_data.py     # ETL: reads our 3 xlsx exports, loads them into the DB 
                            (should only run once)
db/database.py              # data access via SQLAlchemy (SQL Server / Postgres / SQLite, same code)
db/blueprint.py              # compliance blueprint as structured rules
compliance/comparator.py     # deterministic field diff — NO LLM here
llm/ollama_client.py          # generic Ollama REST wrapper
llm/extraction.py              # LLM call 1: free text -> {ip, intent}
llm/recommendation.py          # LLM call 2: findings + RAG context -> recommendations
rag/retriever.py               # Chroma store, embeddings via Ollama (nomic-embed-text)
policies/                        # drop your policy/standard docs here (.txt/.md)
orchestrator.py                   # routes each request through the right path
main.py                            # interactive CLI
```

## Setup — you're using SQLite (current)

```bash
pip install requests pydantic chromadb sqlalchemy
ollama pull llama3.1:8b        # used for both extraction and recommendations
ollama pull nomic-embed-text   # embedding model for RAG

python scripts/init_sqlite_db.py    # creates endpoint_security.db from sql/schema_sqlite.sql
python scripts/import_data.py \
  --folder . \
  --db-url "sqlite:///endpoint_security.db"

python rag/retriever.py         # ingests policies/ into the vector store
python main.py                  # interactive CLI
```

Re-run `import_data.py` any time you get fresh evidence exports — it replaces table
contents and prints any inventory/evidence drift it finds.

## Moving to SQL Server later

1. Create the database and run the schema:
   ```bash
   sqlcmd -S <server> -d master -Q "CREATE DATABASE EndpointSecurity"
   sqlcmd -S <server> -d EndpointSecurity -i sql/schema.sql
   ```
2. Install the ODBC driver + `pyodbc` on the machine running this code (Linux example):
   ```bash
   curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
   curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
   sudo apt-get update && sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
   pip install pyodbc
   ```
3. Point `config.py`'s `DATABASE_URL` at it and re-run `import_data.py` with `--db-url` set
   to the same connection string.

## Things to change before production
- `db/blueprint.py`: replace with your actual signed-off blueprint thresholds.
- `llm/extraction.py`: add a few real few-shot examples from your own users' phrasing.
- Add logging across `orchestrator.py` for extracted intent + confidence per request —
  your main lever for catching misroutes.
- Consider rejecting `confidence: "low"` extractions and asking the user to confirm
  before running a DB lookup, rather than proceeding silently.
- Schedule `scripts/import_data.py` to run on whatever cadence your AV/EDR exports refresh.

