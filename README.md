# Lichess to PostgreSQL

This Python-based service automates the enrichment of chess datasets stored in PostgreSQL. It identifies records missing metadata (where `url IS NULL`), fetches the corresponding game details via the Lichess API, and updates the database with high-granularity information.

## Key Features

* **Batch Processing:** Efficiently queries records in blocks of 1,000 to manage memory and DB load.
* **Lichess API Integration:** Connects to `https://lichess.org/api/game/{id}` to extract nested JSON data including ratings, variants, and clock settings.
* **Error & Rate Handling:**
    * **HTTP 429 (Rate Limit):** Automatically detects limits and pauses for 60 seconds.
    * **HTTP 404 (Not Found):** Marks non-existent games in the DB as `404_NOT_FOUND` to prevent redundant API calls.
* **SI-Compliant Timestamps:** Automatically converts Lichess millisecond timestamps to PostgreSQL `TIMESTAMPTZ` using `to_timestamp(%s / 1000.0)`.



## Technical Prerequisites

* **Runtime:** Python 3.11+
* **Database:** PostgreSQL 15+
* **Driver:** `psycopg` (Version 3)
* **Dependencies:** `requests`

## Configuration

The script uses a centralized configuration for database access and API authentication:

| Variable | Description | Default Service |
| :--- | :--- | :--- |
| `DB_CONFIG` | PostgreSQL Connection String | `host=postgres_db` |
| `LICHESS_TOKEN` | Bearer Token for API access | `lip_...` |

## Deployment

1.  **Install dependencies:**
    ```bash
    pip install requests "psycopg[binary]"
    ```
2.  **Run the service:**
    ```bash
    python lichess_game_to_db.py
    ```

## Database Mapping

The service updates the following columns in the `metrics` table:

* **Game Info:** `rated`, `game_variant`, `speed`, `perf`, `turns`, `winner`, `url`
* **Time Control:** `clock_initial`, `clock_increment`, `clock_total_time`
* **Player Metadata:** User IDs, Ratings, and Rating Diffs for both White and Black.
* **Timestamps:** `game_created_at`, `last_move_at` (stored as SI-compliant timestamps).



## DevOps Notes (Docker)

When running within the provided Docker stack, the `DB_CONFIG` utilizes the internal Docker DNS name `postgres_db`. Ensure the container is part of the `sql_fishnet_net` network to resolve the host correctly.
