# wap-mha-yea-matt-repo

A modular egg collection system with multiple collectors and a unified aggregator. This project supports JSON output and persistent storage in an SQLite database.

### Components

-   **`collector_a.py`** — Simulates egg collection from source A.
-   **`collector_b.py`** — Simulates egg collection from source B.
-   **`aggregator.py`** — Normalizes, deduplicates, and stores results in an SQLite database.
-   **`run_collectors.py`** — The main entrypoint script to execute the collection and aggregation process.
-   **`config.ini`** — Runtime configuration for database path and collector batch sizes.

### Quick Start

1.  Clone the repository.
2.  Navigate to the repository's root directory.
3.  Ensure you have Python 3.8+ installed.
4.  Run the collection process:
    ```bash
    cd src
    python run_collectors.py
    ```

### Configuration

You can edit `src/config.ini` to adjust the following parameters:
-   `db_path` — The file name for the SQLite database.
-   `batch_a` and `batch_b` — The number of records each collector produces per run.

### Database

-   The SQLite database file location defaults to `src/egg_records.db`.
-   The data is stored in a table named `eggs` with the following columns:
    -   `id` (TEXT, PRIMARY KEY)
    -   `source` (TEXT)
    -   `collected_at` (TEXT)
    -   `size` (TEXT)
    -   `weight_g` (REAL)
    -   `diameter_mm` (REAL)
    -   `quality` (TEXT)

### Developer Notes

-   Collectors can be run individually for testing purposes.
-   The aggregator uses an `INSERT OR IGNORE` SQL command to handle deduplication based on the `id` primary key.
-   To switch to a different database system like PostgreSQL, you would need to replace the database connection and query functions in `aggregator.py` with a suitable implementation (e.g., using `psycopg2` or an ORM like SQLAlchemy).

### License

This project is licensed under the MIT License. See the `LICENSE` file for details.

