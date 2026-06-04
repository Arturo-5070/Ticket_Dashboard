from google.cloud import firestore
from google.oauth2 import service_account
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timezone
import json
import streamlit as st

key_dict = json.loads((st.secrets["textkey"]))

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACION DE LA PAGINA
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ticket Status & Metrics Dashboard",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="collapsed",
    #st.session_state.sidebar_state = 'collapsed'
)

# ─────────────────────────────────────────────────────────────────────────────
# THEME / CSS  —  Tema obscuro, ignora las preferencia/configuración del Sistema Operativo / Navegador.
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');
/* ── Hay que tener cuidado con los siguientes colores y donde se estan aplicando ── */
:root, html[data-theme], html[data-theme="light"], html[data-theme="dark"] {
    color-scheme: dark !important;
    --bg:        #0d0f14;
    --surface:   #161922;
    --border:    #252a36;
    --accent:    #f97316;
    --accent2:   #6366f1;
    --danger:    #ef4444;
    --warn:      #facc15;
    --ok:        #22c55e;
    --txt:       #e2e8f0;
    --txt-muted: #64748b;
}

html, body,
.stApp, .stApp > div,
.main, .main > div,
[class*="css"],
.block-container,
div[data-testid="stAppViewContainer"],
div[data-testid="stAppViewBlockContainer"],
div[data-testid="stVerticalBlock"],
div[data-testid="stHorizontalBlock"] {
    background-color: var(--bg) !important;
    color: var(--txt) !important;
    font-family: 'DM Sans', sans-serif !important;
}

header[data-testid="stHeader"],
div[data-testid="stToolbar"] {
    background-color: #0d0f14 !important;
}

/* ── Inputs, selects, multiselects — backgrounds ── */
div[data-testid="stMultiSelect"] > div,
div[data-testid="stSelectbox"] > div,
.stTextInput > div > div,
div[role="listbox"],
div[data-baseweb="select"] {
    background-color: #1c2030 !important;
    border-color: var(--border) !important;
}

/* ── Dropdown selected value & placeholder text ── */
div[data-baseweb="select"] span,
div[data-baseweb="select"] div[class*="ValueContainer"] span,
div[data-baseweb="select"] div[class*="singleValue"],
div[data-baseweb="select"] div[class*="placeholder"],
div[data-baseweb="select"] [data-testid="stWidgetLabel"] ~ div {
    color: #2D4256 !important;
}

/* ── Open dropdown list — background ── */
div[data-baseweb="popover"] {
    background-color: #1c2030 !important;
    border-color: var(--border) !important;
}

/* ── Open dropdown list — option text ── */
div[data-baseweb="popover"] li,
div[data-baseweb="popover"] li span,
div[data-baseweb="popover"] [role="option"],
div[data-baseweb="popover"] [role="option"] span,
div[data-baseweb="menu"] li,
div[data-baseweb="menu"] li span {
    color: #2D4256 !important;
}

/* ── Multiselect chips ── */
div[data-baseweb="tag"] {
    background-color: #252a36 !important;
}
div[data-baseweb="tag"] span {
    color: #2D4256 !important;
}

/* ── Checkboxes / Labels — Aqui hay que delimitar bien los estilo para que NO se apliquen de forma global div/span ── */
label[data-testid="stCheckbox"] span { color: var(--txt) !important; }
p, label { color: var(--txt) !important; }

hr { border-color: var(--border) !important; }

div[data-testid="stPlotlyChart"] > div {
    background-color: transparent !important;
}

div[data-testid="stDataFrame"] iframe,
div[data-testid="stDataFrame"] > div {
    background-color: var(--surface) !important;
    color: var(--txt) !important;
}

section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div {
    background-color: #10131a !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span {
    color: var(--txt) !important;
}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stMultiSelect label,
section[data-testid="stSidebar"] .stTextInput label {
    font-size: .8rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: .06em !important;
    color: var(--txt-muted) !important;
}

.stCaption, small, [data-testid="stCaptionContainer"] {
    color: var(--txt-muted) !important;
}

button[kind="primary"]   { background-color: var(--accent)  !important; border: none !important; }
button[kind="secondary"] { background-color: var(--surface) !important; border: 1px solid var(--border) !important; color: var(--txt) !important; }

.dash-header {
    background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%);
    border-bottom: 2px solid var(--accent);
    padding: 1.4rem 2rem 1.2rem;
    margin: -1rem -1rem 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}
.dash-header h1 {
    font-family: 'Space Mono', monospace;
    font-size: 1.6rem;
    color: #fff !important;
    margin: 0;
    letter-spacing: -0.02em;
}
.dash-header .badge {
    background: var(--accent);
    color: #fff !important;
    font-size: .7rem;
    font-weight: 700;
    padding: .2rem .6rem;
    border-radius: 999px;
    text-transform: uppercase;
    letter-spacing: .08em;
    align-self: flex-start;
    margin-top: .2rem;
}

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: .75rem;
    margin-bottom: 1.5rem;
}
.kpi-card {
    background: var(--surface) !important;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.1rem 1.3rem;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
}
.kpi-card.accent::before  { background: var(--accent); }
.kpi-card.accent2::before { background: var(--accent2); }
.kpi-card.danger::before  { background: var(--danger); }
.kpi-card.ok::before      { background: var(--ok); }
.kpi-label {
    font-size: .72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .08em;
    color: var(--txt-muted) !important;
    margin-bottom: .4rem;
}
.kpi-value {
    font-family: 'Space Mono', monospace;
    font-size: clamp(1rem, 3.5vw, 2rem);
    font-weight: 700;
    color: var(--txt) !important;
    line-height: 1;
}
.kpi-sub {
    font-size: .73rem;
    color: var(--txt-muted) !important;
    margin-top: .35rem;
}

.section-title {
    font-family: 'Space Mono', monospace;
    font-size: .85rem;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: var(--accent) !important;
    margin: 1.5rem 0 .75rem;
    padding-left: .75rem;
    border-left: 3px solid var(--accent);
}

.count-chip {
    display: inline-block;
    background: var(--border);
    border-radius: 999px;
    padding: .15rem .65rem;
    font-size: .72rem;
    font-weight: 700;
    font-family: 'Space Mono', monospace;
    color: var(--txt) !important;
    vertical-align: middle;
    margin-left: .4rem;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FIRESTORE — Conexion y carga de los datos (se usa el caché para mayor rápidez)
# RECORDAR---- cambiar el nombre del projecto, puede usarse el project id
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_db():
    """Return a cached Firestore client."""
    creds = service_account.Credentials.from_service_account_info(key_dict)
    return firestore.Client(credentials=creds, project="tickets-dashboard-56dd6")




@st.cache_data
def load_tickets(limit: int = 3000) -> pd.DataFrame:
    try:
        db = get_db()
        docs = db.collection("DB_ticket").limit(limit).stream()
        records = [doc.to_dict() for doc in docs]
    except Exception as e:
        # ── Muestra el error real en la UI en lugar de crashear ───────────────
        st.error(f"❌ Error al conectar con Firestore: {e}")
        st.info("Verifica los roles IAM del service account y las reglas de Firestore.")
        st.stop()

    df = pd.DataFrame(records)

    # ── Lee las fechas correctamente ──────────────────────────────────────────
    date_cols = ["started", "ended", "issue_created",
                 "issue_resolution_date", "last_change_date"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)

    # ── Guarda Numérica (conversion del tipo de dato) ─────────────────────────
    if "resolution_time_seconds" in df.columns:
        df["resolution_time_seconds"] = pd.to_numeric(
            df["resolution_time_seconds"], errors="coerce"
        )

    return df


# ─────────────────────────────────────────────────────────────────────────────
# HELPER — marca los registros que se van a colorear
# ─────────────────────────────────────────────────────────────────────────────
def compute_flags(df: pd.DataFrame) -> pd.DataFrame:
    now = pd.Timestamp.now(tz="UTC")

    q75 = df["resolution_time_seconds"].quantile(0.75) \
          if "resolution_time_seconds" in df.columns else np.inf

    df = df.copy()
    df["_flag_slow"]     = df["resolution_time_seconds"] > q75
    df["_flag_high_pri"] = df.get("issue_priority", pd.Series()).astype(str).str.lower() == "high"

    if "issue_status" in df.columns and "issue_created" in df.columns:
        age_weeks = (now - df["issue_created"]).dt.total_seconds() / (7 * 86400)
        df["_flag_stale"] = (
            df["issue_status"].astype(str).str.lower().isin(["awaiting", "in progress"]) &
            (age_weeks > 2)
        )
    else:
        df["_flag_stale"] = False

    return df, q75

# ─────────────────────────────────────────────────────────────────────────────
# PANDAS STYLER — Coloreado mixto a nivel de celda y fila
#
# Coloreado a nivel de celda (resaltado preciso en la columna que lo activó):
# • issue_priority → celda roja cuando es Alta
# • resolution_time_seconds → celda naranja cuando supera Q75
# • issue_status → celda amarilla cuando está obsoleto (en espera > 2 semanas)
#
# Coloreado a nivel de fila (se colorea la fila completa para que los tickets
# obsoletos llamen la atención del lector):
# • Toda la fila se tiñe de un ligero tono ámbar cuando _flag_stale es Verdadero
# ─────────────────────────────────────────────────────────────────────────────
def style_tickets(df: pd.DataFrame):
    flag_cols  = [c for c in df.columns if c.startswith("_flag_")]
    display_df = df.drop(columns=flag_cols, errors="ignore")

    # ── Banderas para filtrado (todos en Falso si la columna está ausente) ────
    flag_slow  = df.get("_flag_slow",     pd.Series(False, index=df.index))
    flag_high  = df.get("_flag_high_pri", pd.Series(False, index=df.index))
    flag_stale = df.get("_flag_stale",    pd.Series(False, index=df.index))

    # ── 1. Estilos a nivel de celda (axis=None → regresa el mismo shape del DataFrame) ──
    def cell_style(d):
        styles = pd.DataFrame("", index=d.index, columns=d.columns)

        # Columna issue_priority — celda en color ROJO para prioridad "High"
        if "issue_priority" in d.columns:
            styles.loc[flag_high, "issue_priority"] = (
                "background-color: rgba(239,68,68,.45); "
                "color:#c50606; font-weight:700; "
                "border-left: 3px solid #ef4444"
            )

        # Columna resolution_time_seconds — celda NARANJA para tiempo de resolución mayor a Q75
        if "resolution_time_seconds" in d.columns:
            styles.loc[flag_slow, "resolution_time_seconds"] = (
                "background-color: rgba(249,115,22,.40); "
                "color:#cd6b03; font-weight:700; "
                "border-left: 3px solid #f97316"
            )

        # Columna issue_status — celda ÁMBAR para tickets dormidos por mucho tiempo
        if "issue_status" in d.columns:
            styles.loc[flag_stale, "issue_status"] = (
                "background-color: rgba(250,204,21,.35); "
                "color:#a08102; font-weight:700; "
                "border-left: 3px solid #facc15"
            )

        return styles

    # ── 2. Color a nivel de fila: solo para filas obsoletas ───────────────────
    def row_tint(row):
        if flag_stale.get(row.name, False):
            return ["background-color: rgba(250,204,21,.06)"] * len(row)
        return [""] * len(row)

    styler = (
        display_df.style
        .apply(cell_style, axis=None)   # Color de la celda primero
        .apply(row_tint,   axis=1)      # Tinte de fila encima (solo obsoletos)
    )
    return styler

# ─────────────────────────────────────────────────────────────────────────────
# PLOTLY — Ayudante para el tema oscuro
# ─────────────────────────────────────────────────────────────────────────────
PIE_COLORS = [
    "#fb923c", "#818cf8", "#4ade80", "#fde047",
    "#f87171", "#22d3ee", "#c084fc", "#f472b6",
]

def dark_fig(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color="#f2f4f6", size=12),
        legend=dict(
            bgcolor="rgba(22,25,34,.85)",
            bordercolor="#252a36",
            borderwidth=1,
            font_size=11,
            font_color="#e2e8f0",
        ),
        margin=dict(t=30, b=10, l=10, r=10),
    )
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# Carga de DATA
# ─────────────────────────────────────────────────────────────────────────────
df_raw = load_tickets()

# ─────────────────────────────────────────────────────────────────────────────
# Cabecera
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dash-header">
    <span style="font-size:2rem">🎫</span>
    <div>
        <h1>Ticket Status & Metrics Dashboard</h1>
        <div style="color:#64748b;font-size:.8rem;margin-top:.25rem">
           Google Cloud :: Colab · GitHub · Firestore backend · Streamlite frontend
        </div>
    </div>
    <div class="badge">Test</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR Filtros
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔍 Filters")

    def opts(col, label="All"):
        vals = sorted(df_raw[col].dropna().astype(str).unique().tolist()) if col in df_raw.columns else []
        return [label] + vals

    sel_type = st.multiselect(
        "Issue Type",
        options=sorted(df_raw["issue_type"].dropna().unique().tolist()) if "issue_type" in df_raw.columns else [],
    )
    sel_priority = st.multiselect(
        "Issue Priority",
        options=sorted(df_raw["issue_priority"].dropna().unique().tolist()) if "issue_priority" in df_raw.columns else [],
    )
    sel_resolution = st.multiselect(
        "Issue Resolution",
        options=sorted(df_raw["issue_resolution"].dropna().unique().tolist()) if "issue_resolution" in df_raw.columns else [],
    )
    sel_status = st.multiselect(
        "Issue Status",
        options=sorted(df_raw["issue_status"].dropna().unique().tolist()) if "issue_status" in df_raw.columns else [],
    )

    st.divider()
    st.markdown("## ⚠️ Special flags")
    show_slow  = st.checkbox("Only > Q75 resolution time", value=False)
    show_high  = st.checkbox("Only High priority", value=False)
    show_stale = st.checkbox("Only stale Awaiting (> 2 Weeks)", value=False)
    st.divider()
    st.caption(f"📦 {len(df_raw):,} tickets loaded from Firestore")
    if st.button("🔄 Refresh data (Concept)"):
        load_tickets.clear()
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# Aplicando Filtros
# ─────────────────────────────────────────────────────────────────────────────
df = df_raw.copy()

if sel_type:
    df = df[df["issue_type"].astype(str).isin(sel_type)]
if sel_priority:
    df = df[df["issue_priority"].astype(str).isin(sel_priority)]
if sel_resolution:
    df = df[df["issue_resolution"].astype(str).isin(sel_resolution)]
if sel_status:
    df = df[df["issue_status"].astype(str).isin(sel_status)]

# Cálculo de las banderas ANTES del filtrado de banderas especiales
# (para que el percentil q75 utilice el conjunto filtrado completo).
df, q75_val = compute_flags(df)

if show_slow:
    df = df[df["_flag_slow"]]
if show_high:
    df = df[df["_flag_high_pri"]]
if show_stale:
    df = df[df["_flag_stale"]]

n_flagged_slow  = int(df["_flag_slow"].sum())
n_flagged_high  = int(df["_flag_high_pri"].sum())
n_flagged_stale = int(df["_flag_stale"].sum())

# ─────────────────────────────────────────────────────────────────────────────
# KPI Tarjetas
# ─────────────────────────────────────────────────────────────────────────────
avg_res = df["resolution_time_seconds"].mean() if "resolution_time_seconds" in df.columns else np.nan
avg_res_str = f"{avg_res/86400:.1f}d" if not np.isnan(avg_res) else "—"

pct_done = (
    (df["issue_resolution"].astype(str).str.lower() == "done").sum() / max(len(df), 1) * 100
    if "issue_resolution" in df.columns else 0
)

st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi-card accent">
        <div class="kpi-label">Total Tickets</div>
        <div class="kpi-value">{len(df):,}</div>
        <div class="kpi-sub">matching current filters</div>
    </div>
    <div class="kpi-card danger">
        <div class="kpi-label">Slow (> Q75)</div>
        <div class="kpi-value">{n_flagged_slow:,}</div>
        <div class="kpi-sub">Q75 threshold: {q75_val/86400:.1f} days</div>
    </div>
    <div class="kpi-card accent2">
        <div class="kpi-label">Avg Resolution</div>
        <div class="kpi-value">{avg_res_str}</div>
        <div class="kpi-sub">across filtered tickets</div>
    </div>
    <div class="kpi-card ok">
        <div class="kpi-label">Done Rate</div>
        <div class="kpi-value">{pct_done:.0f}%</div>
        <div class="kpi-sub">resolved as Done</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PIE CHARTS — (gráficos de pay) Prioridad, Status y Tipo del Issue
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Distribution Overview</div>', unsafe_allow_html=True)

col_p1, col_p2, col_p3 = st.columns(3)

# ── Estilo compartido para las etiquetas de los gráficos de pay ───────────────
PIE_LABEL_STYLE = dict(
    #textfont_size=13,
    textfont_color="#ffffff",       # letras blancas, siempre legibles sobre fondo oscuro
    textinfo="percent+label",       # muestra tanto el % como el nombre del segmento
    #insidetextorientation="auto",   # plotly elige el mejor ángulo automáticamente
    textposition='inside',
)

# ── Configuración compartida de leyenda: horizontal al pie de la gráfica ──────
LEGEND_BOTTOM = dict(
    orientation="h",            # leyenda horizontal
    yanchor="top",              # ancla desde arriba del bloque de leyenda
    y=-0.20,                    # se posiciona debajo del gráfico
    xanchor="center",           # centrada horizontalmente
    x=0.5,
    font=dict(color="#e2e8f0", size=11),
)

# ── Helper: recorta al top N y agrupa el resto en "Other" ─────────────────────
def top_n_other(df_counts, col_name, top_n=6):
    """Conserva los top_n valores más frecuentes y agrupa el resto en 'Other'."""
    if len(df_counts) > top_n:
        top   = df_counts.head(top_n)
        other = pd.DataFrame([{
            col_name: "Other",
            "Count":  df_counts.tail(-top_n)["Count"].sum()
        }])
        return pd.concat([top, other], ignore_index=True)
    return df_counts

TOP_SLICES = 4

with col_p1:
    if "issue_priority" in df.columns and len(df) > 0:
        pri_counts = df["issue_priority"].astype(str).value_counts().reset_index()
        pri_counts.columns = ["Priority", "Count"]

        # ── Se conservan solo los 5 con más tickets; el resto se agrupa en "Other" ──
        pri_counts = top_n_other(pri_counts, "Priority", TOP_SLICES)

        fig_pri = px.pie(
            pri_counts, names="Priority", values="Count",
            title="Issue Priority",
            color_discrete_sequence=PIE_COLORS,
            hole=0.45,
        )
        fig_pri.update_traces(**PIE_LABEL_STYLE)
        fig_pri.update_layout(
            legend=LEGEND_BOTTOM,
            uniformtext_minsize=12,
            uniformtext_mode='hide',
            title=dict(font=dict(color="#e2e8f0", size=14)),
            margin=dict(t=40, b=80, l=10, r=10),   # espacio extra abajo para la leyenda

        )
        st.plotly_chart(dark_fig(fig_pri), use_container_width=True)

with col_p2:
    if "issue_status" in df.columns and len(df) > 0:
        sta_counts = df["issue_status"].astype(str).value_counts().reset_index()
        sta_counts.columns = ["Status", "Count"]

        # ── Se conservan solo los 5 con más tickets; el resto se agrupa en "Other" ──
        sta_counts = top_n_other(sta_counts, "Status", TOP_SLICES)

        fig_sta = px.pie(
            sta_counts, names="Status", values="Count",
            title="Issue Status",
            color_discrete_sequence=PIE_COLORS[2:],
            hole=0.45,
        )
        fig_sta.update_traces(**PIE_LABEL_STYLE)
        fig_sta.update_layout(
            legend=LEGEND_BOTTOM,
            uniformtext_minsize=12,
            uniformtext_mode='hide',
            title=dict(font=dict(color="#e2e8f0", size=14)),
            margin=dict(t=40, b=80, l=10, r=10),
        )
        st.plotly_chart(dark_fig(fig_sta), use_container_width=True)

with col_p3:
    if "issue_type" in df.columns and len(df) > 0:
        typ_counts = df["issue_type"].astype(str).value_counts().reset_index()
        typ_counts.columns = ["Type", "Count"]

        # ── Se conservan solo los 5 con más tickets; el resto se agrupa en "Other" ──
        typ_counts = top_n_other(typ_counts, "Type", TOP_SLICES)

        fig_typ = px.pie(
            typ_counts, names="Type", values="Count",
            title="Issue Type",
            color_discrete_sequence=PIE_COLORS[4:] + PIE_COLORS,
            hole=0.45,
        )
        fig_typ.update_traces(**PIE_LABEL_STYLE)
        fig_typ.update_layout(
            legend=LEGEND_BOTTOM,
            uniformtext_minsize=12,
            uniformtext_mode='hide',
            title=dict(font=dict(color="#e2e8f0", size=14)),
            margin=dict(t=40, b=80, l=10, r=10),
        )
        st.plotly_chart(dark_fig(fig_typ), use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# BAR CHARTS — (Gráficos de Barra) Cuenta de tickets por reportadores y asignados
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Ticket Counts by Person</div>', unsafe_allow_html=True)

col_r, col_a = st.columns(2)

TOP_N = 15

with col_r:
    if "issue_reporter" in df.columns and len(df) > 0:
        rep_counts = (
            df["issue_reporter"].astype(str)
            .value_counts()
            .head(TOP_N)
            .reset_index()
        )
        rep_counts.columns = ["Reporter", "Tickets"]
        fig_rep = px.bar(
            rep_counts, x="Tickets", y="Reporter", orientation="h",
            title=f"Top {TOP_N} Reporters",
            color="Tickets",
            color_continuous_scale=["#1e2433", "#f97316"],
        )
        fig_rep.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        st.plotly_chart(dark_fig(fig_rep), use_container_width=True)

with col_a:
    if "issue_assignee" in df.columns and len(df) > 0:
        asg_counts = (
            df["issue_assignee"].astype(str)
            .value_counts()
            .head(TOP_N)
            .reset_index()
        )
        asg_counts.columns = ["Assignee", "Tickets"]
        fig_asg = px.bar(
            asg_counts, x="Tickets", y="Assignee", orientation="h",
            title=f"Top {TOP_N} Assignees",
            color="Tickets",
            color_continuous_scale=["#1e2433", "#6366f1"],
        )
        fig_asg.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        st.plotly_chart(dark_fig(fig_asg), use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# TIMELINE — (Línea de Tiempo) Volumen de entradas a lo largo del tiempo
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Ticket Volume Over Time</div>', unsafe_allow_html=True)

if "issue_created" in df.columns and df["issue_created"].notna().any():

    # ── Fila 1: Granularidad + Filtro de periodo por años ────────────────────
    col_tl_gran, col_tl_yr1, col_tl_yr2 = st.columns([2, 1, 1])

    with col_tl_gran:
        granularity = st.selectbox(
            "Granularity",
            ["Daily", "Weekly", "Monthly", "Quarterly"],
            index=2,                          # Por defecto: Mensual
            key="timeline_gran",
        )

    # ── Se detectan las fechas mínima y máxima del conjunto de datos filtrado ─
    fecha_min = df["issue_created"].min()
    fecha_max = df["issue_created"].max()

    # ── Se convierte a año entero para el slider ──────────────────────────────
    anio_min = int(fecha_min.year) if pd.notna(fecha_min) else 2000
    anio_max = int(fecha_max.year) if pd.notna(fecha_max) else datetime.now().year

    with col_tl_yr1:
        anio_desde = st.selectbox(
            "From Year",
            options=list(range(anio_min, anio_max + 1)),
            index=0,                          # Por defecto: el año más antiguo
            key="tl_anio_desde",
        )
    with col_tl_yr2:
        anio_hasta = st.selectbox(
            "To Year",
            options=list(range(anio_min, anio_max + 1)),
            index=len(range(anio_min, anio_max + 1)) - 1,  # Por defecto: el año más reciente
            key="tl_anio_hasta",
        )

    # ── Validación: el año de inicio no puede ser mayor al año final ──────────
    if anio_desde > anio_hasta:
        st.warning("⚠️ 'From Year' can't be 'To Year'. Please, Adjust the time period.")
    else:
        # ── Se filtra el dataframe según el periodo de años seleccionado ──────
        df_tl = df[
            (df["issue_created"].dt.year >= anio_desde) &
            (df["issue_created"].dt.year <= anio_hasta)
        ].copy()

        freq_map  = {"Daily": "D",  "Weekly": "W",  "Monthly": "ME",  "Quarterly": "QE"}
        label_map = {"Daily": "%Y-%m-%d", "Weekly": "%Y-W%W", "Monthly": "%Y-%m", "Quarterly": "%Y-Q%q"}
        freq      = freq_map[granularity]

        # ── Volumen total (línea punteada de referencia) ──────────────────────
        tl_total = (
            df_tl.set_index("issue_created")
            .resample(freq)
            .size()
            .reset_index(name="Tickets")
            .rename(columns={"issue_created": "Date"})
        )

        # ── Desglose por prioridad (área apilada) ─────────────────────────────
        if "issue_priority" in df_tl.columns:
            tl_pri = (
                df_tl.dropna(subset=["issue_created"])
                .set_index("issue_created")
                .groupby([pd.Grouper(freq=freq), "issue_priority"])
                .size()
                .reset_index(name="Tickets")
                .rename(columns={"issue_created": "Date"})
            )
            tl_pri["issue_priority"] = tl_pri["issue_priority"].astype(str)

            # ── Salto de línea entre el encabezado y el título de la gráfica ─
            #st.markdown("<br>", unsafe_allow_html=True)

            fig_tl = px.area(
                tl_pri,
                x="Date", y="Tickets",
                color="issue_priority",
                title=f"Tickets Created per {granularity} · by Priority",
                color_discrete_sequence=PIE_COLORS,
                labels={"issue_priority": "Priority"},
            )
            # ── Superponer el total como una línea discontinua blanca ─────────
            fig_tl.add_scatter(
                x=tl_total["Date"], y=tl_total["Tickets"],
                mode="lines",
                name="Total",
                line=dict(color="#e2e8f0", width=2, dash="dot"),
            )
        else:
            st.markdown("<br>", unsafe_allow_html=True)

            fig_tl = px.area(
                tl_total, x="Date", y="Tickets",
                title=f"Tickets Created per {granularity}",
                color_discrete_sequence=["#6366f1"],
            )

        fig_tl.update_layout(
            hovermode="x unified",
            # ── Dos saltos de línea de margen entre el título y la gráfica───
            margin=dict(t=20, b=10, l=10, r=10),
            title=dict(
                font=dict(color="#e2e8f0", size=15),
                pad=dict(t=10),             # espacio extra debajo del título
            ),
            xaxis=dict(
                showgrid=True,
                gridcolor="#1e2433",
                tickformat=label_map[granularity],
                tickfont=dict(color="#e2e8f0", size=12),
                title_font=dict(color="#e2e8f0"),
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="#1e2433",
                tickfont=dict(color="#e2e8f0", size=12),
                title_font=dict(color="#e2e8f0"),
            ),
            legend=dict(
                orientation="h",
                yanchor="top",
                xanchor="right",  x=1,
                font=dict(color="#e2e8f0", size=12),
            ),
        )

        # ── un saltos de línea antes de renderizar la gráfica ────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.plotly_chart(dark_fig(fig_tl), use_container_width=True)

        # ── Minigráfico: promedio móvil (solo para datos diarios/semanales) ───
        if granularity not in ("Monthly", "Quarterly") and len(tl_total) > 7:
            tl_total["Rolling avg"] = tl_total["Tickets"].rolling(7, min_periods=1).mean()
            fig_spark = px.line(
                tl_total, x="Date", y="Rolling avg",
                title="7-period Rolling Average",
                color_discrete_sequence=["#f97316"],
            )
            fig_spark.update_layout(
                xaxis=dict(showgrid=False, tickfont=dict(color="#e2e8f0")),
                yaxis=dict(showgrid=True, gridcolor="#1e2433", tickfont=dict(color="#e2e8f0")),
                title=dict(font=dict(color="#e2e8f0")),
                showlegend=False,
                height=200,
                margin=dict(t=30, b=10, l=10, r=10),
            )
            st.plotly_chart(dark_fig(fig_spark), use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# HISTOGRAMA DEL TIEMPO DE RESOLUCION
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Resolution Time Distribution</div>', unsafe_allow_html=True)

if "resolution_time_seconds" in df.columns and df["resolution_time_seconds"].notna().any():
    rt_days = df["resolution_time_seconds"].dropna() / 86400
    fig_hist = px.histogram(
        rt_days, nbins=40,
        labels={"value": "Resolution Time (days)", "count": "Tickets"},
        color_discrete_sequence=["#6366f1"],
    )
    fig_hist.add_vline(
        x=q75_val / 86400, line_dash="dash",
        line_color="#f97316", line_width=2,
        annotation_text=f"Q75 ({q75_val/86400:.1f}d)",
        annotation_font_color="#f97316",
    )
    fig_hist.update_layout(showlegend=False, bargap=0.05)
    st.plotly_chart(dark_fig(fig_hist), use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# LEYENDA PARA LAS BANDERAS MARCADAS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Ticket Table</div>', unsafe_allow_html=True)

st.markdown(f"""
<div style="display:flex;gap:1.2rem;margin-bottom:.75rem;font-size:.78rem;font-weight:600">
    <span style="color:#fdba74">🟠 Above Q75 resolution time
        <span class="count-chip">{n_flagged_slow}</span>
    </span>
    <span style="color:#fca5a5">🔴 High priority
        <span class="count-chip">{n_flagged_high}</span>
    </span>
    <span style="color:#fde68a">🟡 Stale awaiting &gt;2 weeks
        <span class="count-chip">{n_flagged_stale}</span>
    </span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TABLA DE DATOS ESTILIZADA — IMPORTANTE
# ─────────────────────────────────────────────────────────────────────────────

# ── Columnas para mostrar (se descartan las columnas internas/de ruido) ───────
DISPLAY_COLS = [
    c for c in [
        "id", "issue_num", "issue_proj", "issue_type", "issue_priority",
        "issue_status", "issue_resolution", "issue_reporter", "issue_assignee",
        "issue_created", "issue_resolution_date", "resolution_time_seconds",
        "issue_comments_count", "escalated_to_mngmnt", "processing_steps",
        "_flag_slow", "_flag_high_pri", "_flag_stale",
    ]
    if c in df.columns
]

table_df = df[DISPLAY_COLS].copy()

# ── Se formatea la columna resolution_time_seconds para mostrarse en días ─────
if "resolution_time_seconds" in table_df.columns:
    table_df["resolution_time_seconds"] = table_df["resolution_time_seconds"].apply(
        lambda x: f"{x/86400:.1f}d" if pd.notna(x) else "—"
    )

st.dataframe(
    style_tickets(table_df),
    use_container_width=True,
    height=520,
)

st.caption(
    f"Showing {len(df):,} tickets · "
    f"🟠 {n_flagged_slow} slow · "
    f"🔴 {n_flagged_high} high priority · "
    f"🟡 {n_flagged_stale} stale awaiting"
)
