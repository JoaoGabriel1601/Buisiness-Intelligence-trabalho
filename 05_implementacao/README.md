# 05 — Implementação Prática (MVP)

MVP executável do projeto TechFlow BI. Materializa em código o Star Schema, os SQLs DORA e o dashboard executivo projetados nos módulos [01](../01_modelagem_dimensional/modelagem_dimensional.md), [02](../02_arquitetura_dados/arquitetura_dados.md), [03](../03_dashboard_executivo/dashboard_executivo.md) e [04](../04_analise_estrategica/analise_estrategica.md).

---

## Stack

| Camada | Ferramenta | Papel |
|---|---|---|
| Geração de dados | Python + Faker | Dados sintéticos dos 3 cenários DORA × IA |
| Data Warehouse | DuckDB | SQL analítico embarcado (substitui BigQuery localmente) |
| Queries DORA | SQL puro (`queries/*.sql`) | 4 métricas DORA + análise IA + Balance Score |
| Dashboard | Streamlit + Plotly | 3 níveis × 3 cenários (abas) |

---

## Estrutura

```
05_implementacao/
├── requirements.txt
├── config.py                        # Parâmetros dos 3 cenários (seeds, multipliers)
├── run_queries.py                   # Executa e imprime todas as queries DORA
│
├── data/
│   ├── generate_synthetic_data.py   # Faker → CSVs (3 cenários)
│   └── seed/{cenario_a,b,c}/        # CSVs gerados
│
├── warehouse/
│   ├── schema.sql                   # DDL Star Schema
│   ├── load.py                      # CSV → DuckDB (schema por cenário)
│   └── techflow.duckdb              # Banco gerado
│
├── queries/
│   ├── 01_deployment_frequency.sql
│   ├── 02_lead_time.sql
│   ├── 03_change_failure_rate.sql
│   ├── 04_mttr.sql
│   ├── 05_ai_impact_analysis.sql
│   └── 06_dora_balance_score.sql
│
└── dashboard/
    └── app.py                       # Streamlit — 3 abas × 3 níveis
```

---

## Como rodar

### 1. Instalar dependências

```bash
cd 05_implementacao
pip install -r requirements.txt
```

### 2. Gerar os dados sintéticos

```bash
python data/generate_synthetic_data.py
```

Cria CSVs em `data/seed/cenario_{a,b,c}/` — ~1500 deploys por cenário + dimensões.

> **Windows**: se aparecer `UnicodeEncodeError` por causa de caracteres UTF-8 no console, rode com `PYTHONIOENCODING=utf-8 python data/generate_synthetic_data.py`.

### 3. Popular o DuckDB

```bash
python warehouse/load.py
```

Gera `warehouse/techflow.duckdb` com 3 schemas (`cenario_a`, `cenario_b`, `cenario_c`), cada um com 1 fato + 3 dimensões.

### 4. Validar via queries

```bash
python run_queries.py                      # roda todas as queries nos 3 cenários
python run_queries.py --query 03           # só a CFR
python run_queries.py --scenario cenario_b # só o cenário B
```

Saída esperada: tabelas formatadas mostrando as 4 métricas DORA + análise IA + Balance Score lado a lado por cenário.

### 5. Abrir o dashboard

```bash
streamlit run dashboard/app.py
```

Abre em `http://localhost:8501`.

---

## Os 3 Cenários

Os parâmetros em [config.py](config.py) geram distribuições que reproduzem as narrativas de [04_analise_estrategica.md](../04_analise_estrategica/analise_estrategica.md):

| Cenário | Narrativa | Lead Time | CFR | MTTR | Review Time |
|---|---|---|---|---|---|
| **A — IA Saudável** | Aceleração Real | ↓↓ | estável | estável | estável |
| **B — IA Tóxica** | Caos Mais Rápido | ↓↓ | ↑↑ | ↑↑↑ | ↑↑ |
| **C — IA Neutra** | Transferência de Gargalo | estável | estável | estável | ↑↑ |

A data de corte "adoção IA" é `2025-03-01` ([config.py](config.py)), marcada por linha tracejada vermelha no dashboard.

---

## Dashboard — 3 Níveis

Seguindo o wireframe do [módulo 3](../03_dashboard_executivo/dashboard_executivo.md):

- **Nível 1 — Macro**: 4 KPI cards (DF, LT, CFR, MTTR) com semáforo DORA + trend line mensal + gauge % IA
- **Nível 2 — Filtros**: stacked bar por squad + scatter `lead_time × ai_pct`
- **Nível 3 — Drill-down**: tabela de PRs filtrável + heatmap falhas × dia-da-semana + barra CFR por repositório

Filtros laterais (sidebar): squad, repositório, janela de datas, % IA.

---

## Regenerar do zero

```bash
rm -rf data/seed warehouse/techflow.duckdb
python data/generate_synthetic_data.py
python warehouse/load.py
```

---

## Critérios de validação

- [x] 3 schemas DuckDB populados (`cenario_a`, `cenario_b`, `cenario_c`)
- [x] Cenário B mostra Lead Time ↓ + CFR > 10% (caos acelerado)
- [x] Cenário A mostra Lead Time ↓ + CFR < 5% (aceleração real)
- [x] DORA Balance Score diferencia os 3 cenários numericamente
- [x] Dashboard alterna entre cenários via abas e aplica filtros
