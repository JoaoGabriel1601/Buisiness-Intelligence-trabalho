"""
Carrega os CSVs de cada cenário no DuckDB em schemas isolados.

Uso:
    python warehouse/load.py

Resultado:
    warehouse/techflow.duckdb com os schemas cenario_a, cenario_b, cenario_c.
    Cada schema contém: dim_time, dim_repository, dim_engineer, fato_deploys.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import SCENARIOS

ROOT = Path(__file__).resolve().parent.parent
SEED_DIR = ROOT / "data" / "seed"
SCHEMA_SQL = Path(__file__).resolve().parent / "schema.sql"
DB_PATH = Path(__file__).resolve().parent / "techflow.duckdb"

TABLES = ["dim_time", "dim_repository", "dim_engineer", "fato_deploys"]


def load_scenario(conn: duckdb.DuckDBPyConnection, scenario_key: str) -> dict[str, int]:
    schema_ddl = SCHEMA_SQL.read_text(encoding="utf-8").replace("{{SCHEMA}}", scenario_key)
    conn.execute(schema_ddl)

    counts: dict[str, int] = {}
    scenario_dir = SEED_DIR / scenario_key

    for table in TABLES:
        csv_path = scenario_dir / f"{table}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(
                f"CSV não encontrado: {csv_path}. "
                f"Rode primeiro: python data/generate_synthetic_data.py"
            )

        conn.execute(f"DELETE FROM {scenario_key}.{table}")
        conn.execute(
            f"""
            INSERT INTO {scenario_key}.{table}
            SELECT * FROM read_csv_auto(?, header=True, nullstr=['', 'NULL'])
            """,
            [str(csv_path)],
        )
        count = conn.execute(f"SELECT COUNT(*) FROM {scenario_key}.{table}").fetchone()[0]
        counts[table] = count

    return counts


def main() -> None:
    print(f"→ Abrindo DuckDB em: {DB_PATH}")
    conn = duckdb.connect(str(DB_PATH))

    for scenario_key, cfg in SCENARIOS.items():
        print(f"\n→ Carregando {scenario_key} ({cfg['label']})...")
        counts = load_scenario(conn, scenario_key)
        for table, n in counts.items():
            print(f"  ✓ {scenario_key}.{table:<18} → {n:>5} linhas")

    conn.close()
    print(f"\n✅ Carga concluída. Banco em: {DB_PATH}")


if __name__ == "__main__":
    main()
