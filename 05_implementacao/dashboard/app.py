"""
TechFlow BI — DORA Metrics Dashboard (Streamlit).

Layout:
- Sidebar: filtros globais (squad, repositório, período, adoção IA)
- 3 abas (cenário A / B / C) × 3 níveis (Macro / Filtros / Drill-down)

Executar:
    streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from config import AI_ADOPTION_DATE, DATE_END, DATE_START, DORA_BENCHMARKS, SCENARIOS

DB_PATH = ROOT / "warehouse" / "techflow.duckdb"


# ─────────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_scenario(scenario_key: str) -> pd.DataFrame:
    """Carrega fato_deploys joined com dimensões para um cenário."""
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        df = conn.execute(
            f"""
            SELECT
                f.deploy_id,
                f.timestamp_deploy,
                CAST(f.timestamp_deploy AS DATE) AS date_full,
                f.lead_time_minutes,
                f.recovery_time_minutes,
                f.is_rollback,
                f.is_hotfix,
                f.ai_generated_pct,
                f.pr_review_time_minutes,
                f.num_comments_review,
                f.num_approvals,
                f.num_revisions_requested,
                f.deploy_status,
                f.deploy_trigger,
                f.environment,
                f.lines_added,
                f.lines_removed,
                f.pr_number,
                f.pr_title,
                dr.repo_name,
                dr.squad,
                dr.criticality_level,
                dr.ai_adoption_level,
                dr.ai_tool_used,
                de.full_name AS engineer_name,
                de.github_username,
                de.seniority_level,
                de.uses_ai_tools
            FROM {scenario_key}.fato_deploys f
            JOIN {scenario_key}.dim_repository dr ON f.repository_id = dr.repository_id
            JOIN {scenario_key}.dim_engineer de ON f.engineer_id = de.engineer_id
            WHERE f.environment = 'production'
            """
        ).fetch_df()
    finally:
        conn.close()
    df["date_full"] = pd.to_datetime(df["date_full"])
    df["timestamp_deploy"] = pd.to_datetime(df["timestamp_deploy"])
    df["is_failure"] = df["is_rollback"] | (df["deploy_status"] == "failure")
    df["is_after_ai"] = df["date_full"] >= pd.Timestamp(AI_ADOPTION_DATE)
    df["ai_band"] = pd.cut(
        df["ai_generated_pct"],
        bins=[-0.01, 0.3, 0.7, 1.01],
        labels=["Baixa IA (<30%)", "Média IA (30-70%)", "Alta IA (>=70%)"],
    )
    return df


@st.cache_data(show_spinner=False)
def all_squads_and_repos(scenario_key: str) -> tuple[list[str], list[str]]:
    df = load_scenario(scenario_key)
    return sorted(df["squad"].unique().tolist()), sorted(df["repo_name"].unique().tolist())


# ─────────────────────────────────────────────────────────────
# DORA classification
# ─────────────────────────────────────────────────────────────
DORA_COLORS = {
    "Elite": "#238636",
    "High": "#1f6feb",
    "Medium": "#d29922",
    "Low": "#da3633",
}


def classify(metric: str, value: float) -> str:
    if value is None or pd.isna(value):
        return "—"
    b = DORA_BENCHMARKS[metric]
    if metric == "deployment_frequency":
        if value >= b["elite"]:
            return "Elite"
        if value >= b["high"]:
            return "High"
        if value >= b["medium"]:
            return "Medium"
        return "Low"
    # lead_time_hours, mttr_hours, change_failure_rate → menor é melhor
    if value < b["elite"]:
        return "Elite"
    if value < b["high"]:
        return "High"
    if value < b["medium"]:
        return "Medium"
    return "Low"


def badge(label: str) -> str:
    emoji = {"Elite": "🟢", "High": "🔵", "Medium": "🟡", "Low": "🔴", "—": "⚪"}[label]
    return f"{emoji} {label}"


# ─────────────────────────────────────────────────────────────
# Metric calculators
# ─────────────────────────────────────────────────────────────
def business_days_in_range(start: pd.Timestamp, end: pd.Timestamp) -> int:
    rng = pd.bdate_range(start, end)
    return max(1, len(rng))


def compute_kpis(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> dict:
    if df.empty:
        return {
            "deploy_freq": 0.0, "lead_time_h": 0.0, "cfr_pct": 0.0, "mttr_h": 0.0,
            "ai_pct": 0.0, "n_deploys": 0,
        }
    bdays = business_days_in_range(start, end)
    success = df[df["deploy_status"] == "success"]
    mttr = df.loc[df["is_failure"] & df["recovery_time_minutes"].notna(), "recovery_time_minutes"]
    return {
        "deploy_freq": len(success) / bdays,
        "lead_time_h": df["lead_time_minutes"].mean() / 60.0,
        "cfr_pct": df["is_failure"].mean() * 100.0,
        "mttr_h": (mttr.mean() / 60.0) if len(mttr) else 0.0,
        "ai_pct": df["ai_generated_pct"].mean() * 100.0,
        "n_deploys": len(df),
    }


def kpi_delta(current: float, previous: float, lower_is_better: bool) -> tuple[str, str]:
    """Retorna (delta_str, delta_color) para st.metric."""
    if previous == 0 or pd.isna(previous):
        return ("—", "off")
    pct = (current - previous) / previous * 100
    arrow = "▲" if pct >= 0 else "▼"
    if lower_is_better:
        color = "inverse"  # seta pra baixo = verde
    else:
        color = "normal"
    return (f"{arrow} {pct:+.1f}% vs pré-IA", color)


# ─────────────────────────────────────────────────────────────
# Sidebar filters
# ─────────────────────────────────────────────────────────────
def sidebar_filters() -> dict:
    st.sidebar.title("🎛️ Filtros globais")

    all_squads = sorted({sq for sc in SCENARIOS for sq in all_squads_and_repos(sc)[0]})
    all_repos = sorted({r for sc in SCENARIOS for r in all_squads_and_repos(sc)[1]})

    squads = st.sidebar.multiselect("Squad", all_squads, default=all_squads)
    repos = st.sidebar.multiselect("Repositório", all_repos, default=all_repos)

    preset = st.sidebar.radio(
        "Período",
        ["Tudo", "Últimos 90 dias", "Últimos 180 dias", "Pós-adoção IA", "Custom"],
        index=0,
    )
    if preset == "Tudo":
        date_range = (DATE_START, DATE_END)
    elif preset == "Últimos 90 dias":
        date_range = (DATE_END - pd.Timedelta(days=90), DATE_END)
    elif preset == "Últimos 180 dias":
        date_range = (DATE_END - pd.Timedelta(days=180), DATE_END)
    elif preset == "Pós-adoção IA":
        date_range = (AI_ADOPTION_DATE, DATE_END)
    else:
        date_range = st.sidebar.date_input(
            "Intervalo", value=(DATE_START, DATE_END),
            min_value=DATE_START, max_value=DATE_END,
        )

    ai_filter = st.sidebar.radio(
        "Adoção de IA",
        ["Todos", "Com IA (repos)", "Sem IA (repos)"],
        index=0,
    )

    st.sidebar.divider()
    st.sidebar.caption(f"Adoção IA: **{AI_ADOPTION_DATE}**")
    st.sidebar.caption(f"Range total: {DATE_START} → {DATE_END}")

    return {
        "squads": squads,
        "repos": repos,
        "date_start": pd.Timestamp(date_range[0]),
        "date_end": pd.Timestamp(date_range[1]),
        "ai_filter": ai_filter,
    }


def apply_filters(df: pd.DataFrame, f: dict) -> pd.DataFrame:
    out = df[
        (df["squad"].isin(f["squads"]))
        & (df["repo_name"].isin(f["repos"]))
        & (df["date_full"] >= f["date_start"])
        & (df["date_full"] <= f["date_end"])
    ]
    if f["ai_filter"] == "Com IA (repos)":
        out = out[out["ai_adoption_level"] != "none"]
    elif f["ai_filter"] == "Sem IA (repos)":
        out = out[out["ai_adoption_level"] == "none"]
    return out


# ─────────────────────────────────────────────────────────────
# Rendering — Nível 1 (Macro)
# ─────────────────────────────────────────────────────────────
def render_level1(df: pd.DataFrame, f: dict) -> None:
    st.subheader("Nível 1 — Visão Macro")

    kpi_now = compute_kpis(df, f["date_start"], f["date_end"])
    pre = df[~df["is_after_ai"]]
    post = df[df["is_after_ai"]]
    pre_end = pd.Timestamp(AI_ADOPTION_DATE) - pd.Timedelta(days=1)
    post_end = f["date_end"]
    kpi_pre = compute_kpis(pre, f["date_start"], pre_end)
    kpi_post = compute_kpis(post, pd.Timestamp(AI_ADOPTION_DATE), post_end)

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        cls = classify("deployment_frequency", kpi_now["deploy_freq"])
        d, color = kpi_delta(kpi_post["deploy_freq"], kpi_pre["deploy_freq"], lower_is_better=False)
        st.metric("📈 Deployment Freq.", f"{kpi_now['deploy_freq']:.2f} /dia", delta=d, delta_color=color)
        st.caption(badge(cls))

    with c2:
        cls = classify("lead_time_hours", kpi_now["lead_time_h"])
        d, color = kpi_delta(kpi_post["lead_time_h"], kpi_pre["lead_time_h"], lower_is_better=True)
        st.metric("⏱️ Lead Time", f"{kpi_now['lead_time_h']:.1f} h", delta=d, delta_color=color)
        st.caption(badge(cls))

    with c3:
        cls = classify("change_failure_rate", kpi_now["cfr_pct"] / 100.0)
        d, color = kpi_delta(kpi_post["cfr_pct"], kpi_pre["cfr_pct"], lower_is_better=True)
        st.metric("🚨 Change Failure Rate", f"{kpi_now['cfr_pct']:.2f}%", delta=d, delta_color=color)
        st.caption(badge(cls))

    with c4:
        cls = classify("mttr_hours", kpi_now["mttr_h"])
        d, color = kpi_delta(kpi_post["mttr_h"], kpi_pre["mttr_h"], lower_is_better=True)
        st.metric("🔄 MTTR", f"{kpi_now['mttr_h']:.2f} h", delta=d, delta_color=color)
        st.caption(badge(cls))

    with c5:
        st.metric("🤖 Código IA", f"{kpi_now['ai_pct']:.1f}%")
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=kpi_now["ai_pct"],
            number={"suffix": "%"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#1f6feb"},
                "steps": [
                    {"range": [0, 30], "color": "#eef"},
                    {"range": [30, 70], "color": "#cde"},
                    {"range": [70, 100], "color": "#9bd"},
                ],
            },
        ))
        fig.update_layout(height=140, margin=dict(l=5, r=5, t=5, b=5))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("**📊 Tendência DORA ao longo do tempo**")
    trend = _build_trend_series(df)
    if not trend.empty:
        fig = px.line(
            trend, x="month", y="value", color="metric",
            labels={"value": "valor", "month": "mês", "metric": "métrica"},
            color_discrete_map={
                "deploy_freq (dia)": "#1f6feb",
                "lead_time (h)": "#8b5cf6",
                "CFR (%)": "#da3633",
                "MTTR (h)": "#d29922",
            },
        )
        fig.add_vline(
            x=AI_ADOPTION_DATE.isoformat(),
            line_dash="dash", line_color="red",
        )
        fig.add_annotation(
            x=AI_ADOPTION_DATE.isoformat(),
            y=1.0, yref="paper",
            text="Adoção IA", showarrow=False,
            yshift=10, font=dict(color="red"),
        )
        fig.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)


def _build_trend_series(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    dd = df.copy()
    dd["month"] = dd["date_full"].dt.to_period("M").dt.to_timestamp()
    g = dd.groupby("month")
    rows = []
    for m, sub in g:
        success = sub[sub["deploy_status"] == "success"]
        mttr = sub.loc[sub["is_failure"] & sub["recovery_time_minutes"].notna(), "recovery_time_minutes"]
        bdays = business_days_in_range(m, m + pd.offsets.MonthEnd(0))
        rows.append({"month": m, "metric": "deploy_freq (dia)", "value": len(success) / bdays})
        rows.append({"month": m, "metric": "lead_time (h)", "value": sub["lead_time_minutes"].mean() / 60.0})
        rows.append({"month": m, "metric": "CFR (%)", "value": sub["is_failure"].mean() * 100.0})
        rows.append({"month": m, "metric": "MTTR (h)", "value": (mttr.mean() / 60.0) if len(mttr) else 0.0})
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────
# Rendering — Nível 2 (Filtros / comparações)
# ─────────────────────────────────────────────────────────────
def render_level2(df: pd.DataFrame) -> None:
    st.subheader("Nível 2 — Análises cruzadas")

    if df.empty:
        st.info("Sem dados para os filtros atuais.")
        return

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Deploys por squad (success vs failure)**")
        g = df.groupby(["squad", "deploy_status"]).size().reset_index(name="n")
        fig = px.bar(
            g, x="squad", y="n", color="deploy_status", barmode="stack",
            color_discrete_map={"success": "#238636", "failure": "#da3633", "rolled_back": "#d29922"},
        )
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("**Lead time (h) × % código IA**")
        sample = df.sample(min(800, len(df)), random_state=0)
        fig = px.scatter(
            sample,
            x="ai_generated_pct", y=sample["lead_time_minutes"] / 60.0,
            color="is_failure",
            color_discrete_map={True: "#da3633", False: "#238636"},
            labels={"ai_generated_pct": "% IA", "y": "lead time (h)", "is_failure": "falhou"},
            opacity=0.55,
        )
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Antes vs depois da adoção de IA (por métrica)**")
    pre = df[~df["is_after_ai"]]
    post = df[df["is_after_ai"]]

    def _summary(sub: pd.DataFrame) -> dict:
        mttr = sub.loc[sub["is_failure"] & sub["recovery_time_minutes"].notna(), "recovery_time_minutes"]
        return {
            "Lead time (h)": sub["lead_time_minutes"].mean() / 60.0 if len(sub) else 0,
            "Review time (h)": sub["pr_review_time_minutes"].mean() / 60.0 if len(sub) else 0,
            "CFR (%)": sub["is_failure"].mean() * 100.0 if len(sub) else 0,
            "MTTR (h)": mttr.mean() / 60.0 if len(mttr) else 0,
        }

    summary = pd.DataFrame({"Pré-IA": _summary(pre), "Pós-IA": _summary(post)}).reset_index(names="métrica")
    summary_long = summary.melt(id_vars="métrica", var_name="período", value_name="valor")
    fig = px.bar(
        summary_long, x="métrica", y="valor", color="período", barmode="group",
        color_discrete_map={"Pré-IA": "#6b7280", "Pós-IA": "#1f6feb"},
    )
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────
# Rendering — Nível 3 (Drill-down)
# ─────────────────────────────────────────────────────────────
def render_level3(df: pd.DataFrame) -> None:
    st.subheader("Nível 3 — Drill-down")

    if df.empty:
        st.info("Sem dados para os filtros atuais.")
        return

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Heatmap de falhas (dia da semana × hora)**")
        fails = df[df["is_failure"]].copy()
        if fails.empty:
            st.info("Nenhuma falha no recorte atual.")
        else:
            fails["dow"] = fails["timestamp_deploy"].dt.day_name()
            fails["hour"] = fails["timestamp_deploy"].dt.hour
            dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            heat = fails.groupby(["dow", "hour"]).size().reset_index(name="n")
            pivot = heat.pivot(index="hour", columns="dow", values="n").reindex(columns=dow_order).fillna(0)
            fig = px.imshow(
                pivot, aspect="auto", color_continuous_scale="Reds",
                labels=dict(x="dia", y="hora", color="falhas"),
            )
            fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("**Taxa de falhas por repositório**")
        by_repo = df.groupby("repo_name").agg(
            total=("deploy_id", "count"),
            failures=("is_failure", "sum"),
        ).reset_index()
        by_repo["cfr_pct"] = by_repo["failures"] / by_repo["total"] * 100
        by_repo = by_repo.sort_values("cfr_pct", ascending=True)
        fig = px.bar(
            by_repo, x="cfr_pct", y="repo_name", orientation="h",
            color="cfr_pct", color_continuous_scale=["#238636", "#d29922", "#da3633"],
            labels={"cfr_pct": "CFR (%)", "repo_name": "repositório"},
        )
        fig.add_vline(x=5.0, line_dash="dash", line_color="#1f6feb",
                      annotation_text="Elite (5%)", annotation_position="top")
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Tabela de Pull Requests (ordenável / filtrável)**")
    cols = [
        "pr_number", "pr_title", "github_username", "squad", "repo_name",
        "ai_generated_pct", "pr_review_time_minutes", "num_comments_review",
        "num_revisions_requested", "lines_added", "lines_removed", "deploy_status",
        "timestamp_deploy",
    ]
    table = df[cols].copy()
    table["ai_generated_pct"] = (table["ai_generated_pct"] * 100).round(1)
    table["pr_review_time_h"] = (table["pr_review_time_minutes"] / 60.0).round(2)
    table = table.drop(columns=["pr_review_time_minutes"])
    table = table.rename(columns={
        "pr_number": "PR #", "pr_title": "Título", "github_username": "Autor",
        "squad": "Squad", "repo_name": "Repo", "ai_generated_pct": "IA %",
        "pr_review_time_h": "Review (h)", "num_comments_review": "Comments",
        "num_revisions_requested": "Revisões", "lines_added": "+lines",
        "lines_removed": "-lines", "deploy_status": "Status", "timestamp_deploy": "Quando",
    })
    table = table.sort_values("Quando", ascending=False).head(200)
    st.dataframe(table, use_container_width=True, height=380)


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────
def render_scenario(scenario_key: str, cfg: dict, f: dict) -> None:
    df = load_scenario(scenario_key)
    df = apply_filters(df, f)

    st.markdown(f"### {cfg['label']}")
    st.caption(cfg["description"])
    st.caption(f"N = **{len(df):,}** deploys após filtros")

    render_level1(df, f)
    st.markdown("---")
    render_level2(df)
    st.markdown("---")
    render_level3(df)


def main() -> None:
    st.set_page_config(
        page_title="TechFlow — DORA Dashboard",
        page_icon="📊",
        layout="wide",
    )

    if not DB_PATH.exists():
        st.error(f"Banco DuckDB não encontrado em {DB_PATH}.")
        st.code("python warehouse/load.py")
        st.stop()

    st.title("🏢 TechFlow — DORA Metrics Dashboard")
    st.caption("Comparação de 3 cenários sintéticos sobre o impacto da IA Generativa em engenharia.")

    f = sidebar_filters()

    tab_a, tab_b, tab_c = st.tabs([
        "🟢 Cenário A — IA Saudável",
        "🔴 Cenário B — IA Tóxica",
        "🟡 Cenário C — IA Neutra",
    ])
    with tab_a:
        render_scenario("cenario_a", SCENARIOS["cenario_a"], f)
    with tab_b:
        render_scenario("cenario_b", SCENARIOS["cenario_b"], f)
    with tab_c:
        render_scenario("cenario_c", SCENARIOS["cenario_c"], f)


if __name__ == "__main__":
    main()
