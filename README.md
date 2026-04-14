# 📊 TechFlow — Estratégia de Business Intelligence com DORA (2025)

> **Projeto Acadêmico | Engenharia de Software + Business Intelligence**

---

## 🎯 Contexto do Projeto

A **TechFlow** é uma empresa de tecnologia que adotou **IA Generativa** para acelerar a escrita de código. Embora o volume de código tenha aumentado significativamente, dois problemas críticos surgiram:

1. **Instabilidade crescente do sistema** — mais deploys resultaram em mais falhas em produção
2. **Gargalo no Code Review** — o volume de PRs gerados por IA sobrecarregou os revisores humanos

Como **Lead de Engenharia**, a missão é estruturar uma estratégia de BI baseada no framework **DORA (2025)** para responder ao CTO:

> *"A IA está acelerando as entregas ou apenas criando caos mais rápido?"*

---

## 📂 Estrutura do Projeto

| # | Módulo | Arquivo | Conteúdo |
|---|--------|---------|----------|
| 1 | **Modelagem Dimensional** | [`modelagem_dimensional.md`](./01_modelagem_dimensional/modelagem_dimensional.md) | Star Schema: Tabela Fato + 3 Dimensões + Métricas DORA |
| 2 | **Arquitetura de Dados** | [`arquitetura_dados.md`](./02_arquitetura_dados/arquitetura_dados.md) | Pipeline ELT + Diagramas Mermaid + Justificativa Técnica |
| 3 | **Dashboard Executivo** | [`dashboard_executivo.md`](./03_dashboard_executivo/dashboard_executivo.md) | Wireframe 3 Níveis: Macro → Filtros → Drill-down |
| 4 | **Análise Estratégica** | [`analise_estrategica.md`](./04_analise_estrategica/analise_estrategica.md) | Diagnóstico IA + Conexão Técnica↔Negócio |
| 5 | **Implementação Prática** | [`05_implementacao/`](./05_implementacao/README.md) | MVP executável: DuckDB + Streamlit + dados sintéticos dos 3 cenários |

---

## 🚀 MVP Executável

O módulo [05_implementacao](./05_implementacao/README.md) materializa toda a documentação em código rodável:

```bash
cd 05_implementacao
pip install -r requirements.txt
python data/generate_synthetic_data.py   # dados sintéticos dos 3 cenários
python warehouse/load.py                 # popula DuckDB
python run_queries.py                    # imprime métricas DORA
streamlit run dashboard/app.py           # dashboard interativo
```

Stack local: **DuckDB** (substitui BigQuery) + **Streamlit + Plotly** (substitui Power BI) + **Faker** (gera dados que reproduzem os 3 cenários narrativos IA Saudável / IA Tóxica / IA Neutra).

---

## 🏗️ Framework DORA — As 4 Métricas-Chave

| Métrica | O que mede | Benchmark Elite (2025) |
|---------|-----------|----------------------|
| **Deployment Frequency** | Frequência com que código chega em produção | Múltiplos deploys por dia |
| **Lead Time for Changes** | Tempo entre commit e deploy em produção | Menos de 1 hora |
| **Change Failure Rate** | % de deploys que causam falha em produção | < 5% |
| **Mean Time to Recovery** | Tempo para restaurar serviço após falha | Menos de 1 hora |

---

## 🛠️ Stack Tecnológica Proposta

| Camada | Tecnologia | Função |
|--------|-----------|--------|
| **Extração** | GitHub REST API + Jira REST API | Coleta de dados brutos |
| **Armazenamento** | BigQuery (Google Cloud) | Data Warehouse Cloud |
| **Transformação** | dbt (data build tool) + SQL | Modelagem dimensional |
| **Visualização** | Power BI / Looker Studio | Dashboard executivo |
| **Orquestração** | Apache Airflow / Cloud Scheduler | Agendamento de pipelines |

---

## 👤 Autor

Projeto acadêmico de Business Intelligence aplicado à Engenharia de Software.

---

> *"Medir é o primeiro passo para melhorar. Sem dados, você está apenas adivinhando."*  
> — W. Edwards Deming
