# README.md

# wap-mha-yea-matt-repo

Modular egg collection system with multiple collectors and a unified aggregator. Supports JSON output and SQLite database storage.

## Components

- `collector_a.py` — simulates egg collection from source A
- `collector_b.py` — simulates egg collection from source B
- `aggregator.py` — normalizes, deduplicates, and stores results in SQLite
- `run_collectors.py` — entrypoint script
- `config.ini` — runtime configuration (database path, batch sizes)

## Quick start

1. Clone the repository.
2. cd to the repo root.
3. Ensure Python 3.8+ is installed.
4. Run:
```bash
cd src
python run_collectors.py
