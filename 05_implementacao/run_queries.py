"""
Executa os 6 SQLs DORA contra cada schema do DuckDB e imprime os resultados.

Uso:
    python run_queries.py
    python run_queries.py --query 03            # roda apenas um SQL
    python run_queries.py --scenario cenario_b  # apenas um cenário

Pré-requisitos: warehouse/techflow.duckdb populado (rode warehouse/load.py).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import SCENARIOS

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "warehouse" / "techflow.duckdb"
QUERIES_DIR = ROOT / "queries"


def list_queries() -> list[Path]:
    return sorted(QUERIES_DIR.glob("*.sql"))


def run_query(conn: duckdb.DuckDBPyConnection, sql_path: Path, scenario_key: str) -> pd.DataFrame:
    sql = sql_path.read_text(encoding="utf-8").replace("{{SCHEMA}}", scenario_key)
    return conn.execute(sql).fetch_df()


def print_df(df: pd.DataFrame) -> None:
    if df.empty:
        print("  (vazio)")
        return
    with pd.option_context(
        "display.max_rows", 60,
        "display.max_columns", None,
        "display.width", 200,
        "display.float_format", lambda v: f"{v:.2f}",
    ):
        print(df.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", help="prefixo do arquivo SQL (ex.: 03)", default=None)
    parser.add_argument("--scenario", help="cenario_a | cenario_b | cenario_c", default=None)
    args = parser.parse_args()

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Banco DuckDB nao encontrado em {DB_PATH}. Rode antes: python warehouse/load.py"
        )

    queries = list_queries()
    if args.query:
        queries = [q for q in queries if q.name.startswith(args.query)]
        if not queries:
            raise SystemExit(f"Nenhuma query com prefixo '{args.query}'")

    scenarios = list(SCENARIOS.keys())
    if args.scenario:
        if args.scenario not in scenarios:
            raise SystemExit(f"Cenario invalido: {args.scenario}. Use um de {scenarios}")
        scenarios = [args.scenario]

    conn = duckdb.connect(str(DB_PATH), read_only=True)

    for sql_path in queries:
        header = f" {sql_path.stem} "
        print("\n" + "=" * 80)
        print(header.center(80, "="))
        print("=" * 80)

        for scenario_key in scenarios:
            label = SCENARIOS[scenario_key]["label"]
            print(f"\n--- {scenario_key} | {label} ---")
            try:
                df = run_query(conn, sql_path, scenario_key)
                print_df(df)
            except Exception as exc:
                print(f"  ERRO: {exc}")

    conn.close()
    print("\nConcluido.")


if __name__ == "__main__":
    main()
