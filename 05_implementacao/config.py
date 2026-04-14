"""
Parâmetros de geração dos 3 cenários DORA × IA.

Cada cenário modela uma hipótese narrativa do documento 04_analise_estrategica.md:

- Cenário A — IA Saudável  ....... "Aceleração Real"
- Cenário B — IA Tóxica ........... "Caos Mais Rápido"
- Cenário C — IA Neutra ........... "Transferência de Gargalo"

Os parâmetros controlam as distribuições dos campos da tabela fato_deploys
de modo que as queries DORA retornem valores coerentes com cada narrativa.
"""

from datetime import date

# ─────────────────────────────────────────────────────────────
# Parâmetros globais (comuns aos 3 cenários)
# ─────────────────────────────────────────────────────────────
DATE_START = date(2024, 1, 1)
DATE_END = date(2025, 12, 31)

N_REPOSITORIES = 10
N_ENGINEERS = 40
N_DEPLOYS_PER_SCENARIO = 1500

AI_ADOPTION_DATE = date(2025, 3, 1)  # marco de adoção de IA

SQUADS = ["Payments", "Platform", "Growth", "Mobile", "Data"]
TECH_STACKS = ["Python", "Node.js", "Go", "Java", "TypeScript"]
SERVICE_TYPES = ["backend", "frontend", "infra", "data", "mobile"]
CRITICALITY = ["critical", "high", "medium", "low"]
AI_TOOLS = ["Copilot", "Cursor", "Cody", "none"]
ROLES = [
    "Junior Engineer",
    "Pleno Engineer",
    "Senior Engineer",
    "Staff Engineer",
    "Tech Lead",
]
SENIORITY_LEVELS = ["L1", "L2", "L3", "L4", "L5", "L6"]


# ─────────────────────────────────────────────────────────────
# Perfis por cenário (controlam distribuições dos deploys)
# ─────────────────────────────────────────────────────────────
# Campos:
#   lead_time_base_min       → média do lead_time ANTES da adoção de IA
#   lead_time_ai_factor      → multiplicador aplicado DEPOIS da adoção (< 1 = reduz)
#   review_time_base_min     → média do tempo de review ANTES
#   review_time_ai_factor    → multiplicador DEPOIS
#   cfr_base                 → change failure rate ANTES (0.0–1.0)
#   cfr_ai_delta             → soma aplicada ao CFR DEPOIS (pode ser +/-)
#   mttr_base_min            → MTTR ANTES (em minutos)
#   mttr_ai_factor           → multiplicador DEPOIS
#   ai_pct_mean_after        → % médio de código gerado por IA depois da adoção
#   comments_ai_extra        → comentários adicionais em PRs com IA

SCENARIOS = {
    "cenario_a": {
        "label": "Cenário A — IA Saudável",
        "description": "Aceleração Real: lead time cai, qualidade mantida",
        "seed": 42,
        "lead_time_base_min": 720,       # 12h
        "lead_time_ai_factor": 0.35,     # cai p/ ~4.2h
        "review_time_base_min": 240,     # 4h
        "review_time_ai_factor": 1.05,   # quase estável
        "cfr_base": 0.045,               # 4.5%
        "cfr_ai_delta": -0.005,          # leve melhora
        "mttr_base_min": 55,             # < 1h
        "mttr_ai_factor": 0.95,
        "ai_pct_mean_after": 0.55,
        "comments_ai_extra": 0.5,
    },
    "cenario_b": {
        "label": "Cenário B — IA Tóxica",
        "description": "Caos Mais Rápido: lead time cai, mas CFR e MTTR explodem",
        "seed": 1337,
        "lead_time_base_min": 750,
        "lead_time_ai_factor": 0.25,     # cai p/ ~3h
        "review_time_base_min": 250,
        "review_time_ai_factor": 2.5,    # review explode
        "cfr_base": 0.05,
        "cfr_ai_delta": 0.12,            # vai p/ ~17%
        "mttr_base_min": 70,
        "mttr_ai_factor": 3.5,           # MTTR triplica
        "ai_pct_mean_after": 0.70,
        "comments_ai_extra": 6.0,
    },
    "cenario_c": {
        "label": "Cenário C — IA Neutra",
        "description": "Transferência de Gargalo: dev ↓, review ↑, efeito líquido zero",
        "seed": 2025,
        "lead_time_base_min": 700,
        "lead_time_ai_factor": 0.98,     # praticamente estável
        "review_time_base_min": 230,
        "review_time_ai_factor": 2.0,    # review dobra
        "cfr_base": 0.055,
        "cfr_ai_delta": 0.01,            # quase estável
        "mttr_base_min": 60,
        "mttr_ai_factor": 1.1,
        "ai_pct_mean_after": 0.60,
        "comments_ai_extra": 3.0,
    },
}


# ─────────────────────────────────────────────────────────────
# Benchmarks DORA 2025 (utilizados para classificação no dashboard)
# ─────────────────────────────────────────────────────────────
DORA_BENCHMARKS = {
    "deployment_frequency": {   # deploys por dia
        "elite": 1.0,            # > 1/dia
        "high": 1 / 7,           # 1/dia a 1/semana
        "medium": 1 / 30,        # 1/semana a 1/mês
    },
    "lead_time_hours": {         # lead time médio em horas
        "elite": 1.0,            # < 1h
        "high": 24.0,            # < 1 dia
        "medium": 168.0,         # < 1 semana
    },
    "change_failure_rate": {     # percentual 0-1
        "elite": 0.05,
        "high": 0.10,
        "medium": 0.15,
    },
    "mttr_hours": {              # minutos para horas
        "elite": 1.0,
        "high": 24.0,
        "medium": 168.0,
    },
}
