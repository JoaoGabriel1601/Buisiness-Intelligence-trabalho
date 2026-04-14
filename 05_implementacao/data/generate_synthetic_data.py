"""
Gerador de dados sintéticos para o Star Schema TechFlow.

Para cada cenário (A/B/C) gera 4 CSVs em data/seed/<cenario>/:
  - dim_time.csv
  - dim_repository.csv
  - dim_engineer.csv
  - fato_deploys.csv

As distribuições são controladas por config.py e refletem as narrativas:
  A → IA saudável (aceleração real, qualidade mantida)
  B → IA tóxica (caos acelerado, CFR e MTTR sobem)
  C → IA neutra (gargalo só mudou de lugar)
"""

from __future__ import annotations

import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

from faker import Faker

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    AI_ADOPTION_DATE,
    AI_TOOLS,
    CRITICALITY,
    DATE_END,
    DATE_START,
    N_DEPLOYS_PER_SCENARIO,
    N_ENGINEERS,
    N_REPOSITORIES,
    ROLES,
    SCENARIOS,
    SENIORITY_LEVELS,
    SERVICE_TYPES,
    SQUADS,
    TECH_STACKS,
)

SEED_DIR = Path(__file__).resolve().parent / "seed"

MONTH_NAMES_PT = [
    "",
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]
DAY_NAMES_PT = [
    "Segunda-feira", "Terça-feira", "Quarta-feira",
    "Quinta-feira", "Sexta-feira", "Sábado", "Domingo",
]


# ─────────────────────────────────────────────────────────────
# Dimensão: dim_time
# ─────────────────────────────────────────────────────────────
def build_dim_time() -> list[dict]:
    rows = []
    current = DATE_START
    while current <= DATE_END:
        weekday = current.weekday()  # 0 = Monday
        day_of_year = current.timetuple().tm_yday
        sprint_number = ((day_of_year - 1) // 14) + 1

        rows.append({
            "time_id": int(current.strftime("%Y%m%d")),
            "date_full": current.isoformat(),
            "day_of_week": weekday + 1,
            "day_name": DAY_NAMES_PT[weekday],
            "week_number": current.isocalendar()[1],
            "month_number": current.month,
            "month_name": MONTH_NAMES_PT[current.month],
            "quarter": (current.month - 1) // 3 + 1,
            "year": current.year,
            "is_business_day": weekday < 5,
            "sprint_number": sprint_number,
            "sprint_name": f"Sprint {sprint_number} - {current.year}",
        })
        current += timedelta(days=1)
    return rows


# ─────────────────────────────────────────────────────────────
# Dimensão: dim_repository
# ─────────────────────────────────────────────────────────────
REPO_PROFILES = [
    ("payment-service",   "Payments", "Python",     "backend",  "critical", "high",   "Copilot"),
    ("api-gateway",       "Platform", "Go",         "backend",  "critical", "high",   "Copilot"),
    ("user-service",      "Platform", "Node.js",    "backend",  "high",     "high",   "Cursor"),
    ("billing-engine",    "Payments", "Java",       "backend",  "critical", "medium", "Copilot"),
    ("growth-web",        "Growth",   "TypeScript", "frontend", "medium",   "high",   "Cursor"),
    ("mobile-app",        "Mobile",   "TypeScript", "mobile",   "high",     "medium", "Copilot"),
    ("data-pipeline",     "Data",     "Python",     "data",     "medium",   "low",    "none"),
    ("analytics-api",     "Data",     "Python",     "backend",  "low",      "medium", "Copilot"),
    ("infra-config",      "Platform", "Go",         "infra",    "critical", "none",   "none"),
    ("notifications-svc", "Growth",   "Node.js",    "backend",  "medium",   "high",   "Cursor"),
]


def build_dim_repository() -> list[dict]:
    rows = []
    for i, (name, squad, stack, svc, crit, ai_level, ai_tool) in enumerate(REPO_PROFILES, start=1):
        adoption_date = AI_ADOPTION_DATE.isoformat() if ai_level != "none" else ""
        creation_offset = random.randint(400, 1800)
        rows.append({
            "repository_id": i,
            "repo_name": name,
            "repo_full_name": f"techflow/{name}",
            "squad": squad,
            "tech_stack": stack,
            "service_type": svc,
            "criticality_level": crit,
            "ai_adoption_level": ai_level,
            "ai_tool_used": ai_tool,
            "adoption_date": adoption_date,
            "total_contributors": random.randint(4, 25),
            "creation_date": (DATE_START - timedelta(days=creation_offset)).isoformat(),
        })
    return rows


# ─────────────────────────────────────────────────────────────
# Dimensão: dim_engineer
# ─────────────────────────────────────────────────────────────
def build_dim_engineer(faker: Faker) -> list[dict]:
    rows = []
    for i in range(1, N_ENGINEERS + 1):
        seniority = random.choices(
            SENIORITY_LEVELS,
            weights=[3, 4, 5, 4, 2, 1],
        )[0]
        role_idx = min(SENIORITY_LEVELS.index(seniority) // 1, len(ROLES) - 1)
        uses_ai = random.random() < 0.75
        ai_tool = random.choice(AI_TOOLS[:-1]) if uses_ai else "none"
        first = faker.first_name()
        last = faker.last_name()
        username = f"{first[0].lower()}{last.lower()}"[:20]

        rows.append({
            "engineer_id": i,
            "full_name": f"{first} {last}",
            "github_username": username,
            "role": ROLES[min(role_idx, len(ROLES) - 1)],
            "seniority_level": seniority,
            "squad": random.choice(SQUADS),
            "uses_ai_tools": uses_ai,
            "ai_tool_name": ai_tool,
            "ai_adoption_date": AI_ADOPTION_DATE.isoformat() if uses_ai else "",
            "experience_years": 1 + SENIORITY_LEVELS.index(seniority) * 2 + random.randint(0, 3),
            "hire_date": faker.date_between(start_date="-6y", end_date="today").isoformat(),
            "is_reviewer": seniority in ("L3", "L4", "L5", "L6") and random.random() < 0.8,
        })
    return rows


# ─────────────────────────────────────────────────────────────
# Fato: fato_deploys
# ─────────────────────────────────────────────────────────────
def _lognormal(mean_min: int) -> int:
    """Lognormal distribution com média aproximada em minutos."""
    import math
    sigma = 0.55
    mu = math.log(max(mean_min, 1)) - (sigma ** 2) / 2
    return max(1, int(random.lognormvariate(mu, sigma)))


def build_fato_deploys(
    cfg: dict,
    dim_time_rows: list[dict],
    dim_repo_rows: list[dict],
    dim_eng_rows: list[dict],
    faker: Faker,
) -> list[dict]:
    rows = []

    repos_ids = [r["repository_id"] for r in dim_repo_rows]
    repos_by_id = {r["repository_id"]: r for r in dim_repo_rows}
    engs_by_id = {e["engineer_id"]: e for e in dim_eng_rows}
    eng_ids = [e["engineer_id"] for e in dim_eng_rows]

    pr_counter = 1000
    deploy_id = 1

    commit_prefixes = [
        "feat:", "fix:", "chore:", "refactor:", "perf:", "docs:", "test:",
    ]
    pr_subjects = [
        "new payment flow", "auth token refresh", "user service refactor",
        "deps update", "dashboard query optimization", "bug in checkout",
        "ai prompt library", "latency fix in gateway", "feature flag rollout",
        "migration to new schema", "performance improvements", "error handling",
        "retry logic in payments", "add new webhook", "update logging",
    ]

    for _ in range(N_DEPLOYS_PER_SCENARIO):
        # timestamp uniforme no intervalo
        offset_days = random.randint(0, (DATE_END - DATE_START).days)
        ts_date = DATE_START + timedelta(days=offset_days)
        hour = random.choices(
            range(24),
            weights=[1, 1, 1, 1, 1, 1,  2, 3, 5, 8, 10, 10,
                     8, 9, 10, 11, 12, 10,  7, 5, 3, 2, 1, 1],
        )[0]
        minute = random.randint(0, 59)
        ts = datetime.combine(ts_date, datetime.min.time()) + timedelta(hours=hour, minutes=minute)

        time_id = int(ts_date.strftime("%Y%m%d"))
        repo_id = random.choice(repos_ids)
        repo = repos_by_id[repo_id]
        eng_id = random.choice(eng_ids)
        eng = engs_by_id[eng_id]

        is_after_ai = ts_date >= AI_ADOPTION_DATE and repo["ai_adoption_level"] != "none"

        # ── Lead time
        lt_mean = cfg["lead_time_base_min"]
        if is_after_ai:
            lt_mean *= cfg["lead_time_ai_factor"]
        lead_time = _lognormal(int(lt_mean))

        # ── Review time
        rv_mean = cfg["review_time_base_min"]
        if is_after_ai:
            rv_mean *= cfg["review_time_ai_factor"]
        review_time = _lognormal(int(rv_mean))

        # ── AI %
        if is_after_ai:
            ai_pct = max(0.0, min(1.0, random.gauss(cfg["ai_pct_mean_after"], 0.18)))
        else:
            ai_pct = max(0.0, min(1.0, random.gauss(0.05, 0.08)))

        # ── Change failure rate (probabilidade deste deploy falhar)
        cfr_prob = cfg["cfr_base"]
        if is_after_ai:
            cfr_prob += cfg["cfr_ai_delta"]
        # deploys em sexta à noite têm risco extra
        if ts.weekday() == 4 and ts.hour >= 17:
            cfr_prob += 0.05
        cfr_prob = max(0.0, min(0.95, cfr_prob))

        failed = random.random() < cfr_prob
        is_rollback = failed and random.random() < 0.85
        is_hotfix = (not failed) and random.random() < 0.08

        # ── MTTR (só preenche se falhou)
        if failed:
            mttr_mean = cfg["mttr_base_min"]
            if is_after_ai:
                mttr_mean *= cfg["mttr_ai_factor"]
            recovery_time = _lognormal(int(mttr_mean))
        else:
            recovery_time = None

        # ── Comentários e revisões (inflacionam com IA em B e C)
        base_comments = max(0, int(random.gauss(3, 1.5)))
        if is_after_ai and ai_pct > 0.3:
            base_comments += int(random.gauss(cfg["comments_ai_extra"], 1.5))
        num_comments = max(0, base_comments)
        num_approvals = random.choices([1, 2, 3], weights=[6, 3, 1])[0]
        num_revisions = 0
        if ai_pct > 0.3:
            num_revisions = max(0, int(random.gauss(1.2 + cfg["comments_ai_extra"] * 0.2, 1.0)))

        # ── Volume de código
        lines_added = max(1, int(random.lognormvariate(5.0, 1.1)))
        lines_removed = max(0, int(random.lognormvariate(4.2, 1.1)))

        # ── Status
        if is_rollback:
            status = "rolled_back"
        elif failed:
            status = "failure"
        else:
            status = "success"

        trigger = random.choices(
            ["ci_cd", "manual", "scheduled", "hotfix"],
            weights=[70, 15, 10, 5],
        )[0]
        environment = random.choices(
            ["production", "staging", "canary"],
            weights=[75, 15, 10],
        )[0]

        pr_title = f"{random.choice(commit_prefixes)} {random.choice(pr_subjects)}"

        rows.append({
            "deploy_id": deploy_id,
            "time_id": time_id,
            "repository_id": repo_id,
            "engineer_id": eng_id,
            "timestamp_deploy": ts.isoformat(sep=" "),
            "lead_time_minutes": lead_time,
            "change_fail_rate": round(cfr_prob, 4),
            "recovery_time_minutes": recovery_time if recovery_time is not None else "",
            "is_rollback": is_rollback,
            "is_hotfix": is_hotfix,
            "lines_added": lines_added,
            "lines_removed": lines_removed,
            "ai_generated_pct": round(ai_pct, 4),
            "pr_review_time_minutes": review_time,
            "num_comments_review": num_comments,
            "num_approvals": num_approvals,
            "num_revisions_requested": num_revisions,
            "deploy_status": status,
            "deploy_trigger": trigger,
            "environment": environment,
            "pr_number": pr_counter,
            "pr_title": pr_title,
        })
        deploy_id += 1
        pr_counter += 1

    return rows


# ─────────────────────────────────────────────────────────────
# CSV writer helper
# ─────────────────────────────────────────────────────────────
def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────
def main() -> None:
    for scenario_key, cfg in SCENARIOS.items():
        print(f"→ Gerando {scenario_key} ({cfg['label']})...")
        random.seed(cfg["seed"])
        faker = Faker("pt_BR")
        faker.seed_instance(cfg["seed"])

        dim_time_rows = build_dim_time()
        dim_repo_rows = build_dim_repository()
        dim_eng_rows = build_dim_engineer(faker)
        fato_rows = build_fato_deploys(cfg, dim_time_rows, dim_repo_rows, dim_eng_rows, faker)

        out_dir = SEED_DIR / scenario_key
        write_csv(out_dir / "dim_time.csv", dim_time_rows)
        write_csv(out_dir / "dim_repository.csv", dim_repo_rows)
        write_csv(out_dir / "dim_engineer.csv", dim_eng_rows)
        write_csv(out_dir / "fato_deploys.csv", fato_rows)

        print(
            f"  ✓ dim_time: {len(dim_time_rows):>5} | "
            f"dim_repository: {len(dim_repo_rows):>3} | "
            f"dim_engineer: {len(dim_eng_rows):>3} | "
            f"fato_deploys: {len(fato_rows):>5}"
        )

    print(f"\nCSVs gerados em: {SEED_DIR}")


if __name__ == "__main__":
    main()
