import streamlit as st
st.cache_data.clear()
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import io
import numpy as np

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Centro de Operaciones Lomas",
    page_icon="🚔",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Barlow:ital,wght@0,400;0,500;0,600;0,700;1,700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Barlow', sans-serif;
        font-size: 14px;
        color: #e2e8f0;
        background: #060b17;
    }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container {
        padding: 1rem 1.5rem 1.5rem;
        max-width: 100%;
        background: #060b17;
    }

    /* Header */
    .main-header {
        background: linear-gradient(135deg, #0b1630 0%, #092040 45%, #0d3260 100%);
        padding: 24px 30px;
        border-radius: 24px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 20px 60px rgba(0,0,0,0.45);
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: '';
        position: absolute;
        bottom: -14px; left: -14px; right: -14px;
        height: 52px;
        background: rgba(255,255,255,0.06);
        border-radius: 50%;
        transform: scaleX(2);
    }
    .header-title {
        color: #e2e8f0;
        font-size: 2rem;
        font-weight: 800;
        text-shadow: 0 4px 18px rgba(0,0,0,0.35);
        letter-spacing: 0.4px;
        text-align: center;
        flex: 1;
    }
    .header-badge {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(226,232,240,0.12);
        border-radius: 18px;
        padding: 8px 16px;
        color: #cbd5e1;
        font-size: 0.95rem;
        font-weight: 700;
        backdrop-filter: blur(8px);
    }

    /* Cards */
    .section-card,
    [data-testid="metric-container"] {
        background: #0f172a;
        border: 1px solid rgba(96,165,250,0.18);
        border-radius: 20px;
        box-shadow: 0 22px 55px rgba(0,0,0,0.45);
    }
    .section-card { padding: 24px 26px 26px; margin-bottom: 20px; }
    [data-testid="metric-container"] {
        border-left: 6px solid #38bdf8;
        padding: 18px 22px;
        background: rgba(15,23,42,0.95);
    }
    [data-testid="stMetricLabel"] { font-size: 0.95rem; color: #94a3b8; font-weight: 600; letter-spacing: 0.01em; }
    [data-testid="stMetricValue"] { font-size: 2.6rem; color: #f8fafc; font-weight: 800; }
    [data-testid="stMetricDelta"] { font-size: 0.95rem; color: #a5b4fc; }
    [data-testid="stMetricDelta"] svg { display: none; }

    /* Section title */
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #e2e8f0;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 2px solid rgba(56,189,248,0.18);
    }

    /* Filter row */
    .filter-row {
        background: #0b1220;
        border-radius: 22px;
        padding: 18px 20px;
        margin-bottom: 18px;
        border: 1px solid rgba(56,189,248,0.16);
        box-shadow: 0 18px 40px rgba(0,0,0,0.35);
    }

    /* Download button */
    .stDownloadButton button {
        background: #38bdf8;
        color: #0f172a;
        border: none;
        border-radius: 16px;
        font-weight: 700;
        font-size: 0.95rem;
        padding: 10px 18px;
        cursor: pointer;
        transition: background 0.2s ease;
    }
    .stDownloadButton button:hover { background: #22c55e; color: #020617; }

    /* Divider */
    hr { border-color: rgba(56,189,248,0.15); margin: 18px 0; }

    /* Selectbox & date input labels */
    label { font-size: 0.95rem !important; color: #cbd5e1 !important; font-weight: 600 !important; }
    .css-1emrehy { font-size: 0.95rem; color: #cbd5e1; }
</style>
""", unsafe_allow_html=True)

# ─── PALETA ───────────────────────────────────────────────────────────────────
TEAL_DARK   = "#0ea5e9"
TEAL_MED    = "#38bdf8"
TEAL_LIGHT  = "#7dd3fc"
TEAL_PALE   = "#cffafe"
COLOR_SEQ   = ["#22d3ee", "#38bdf8", "#0ea5e9", "#0284c7", "#0369a1"]

CHART_LAYOUT = dict(
    paper_bgcolor="#07111f",
    plot t_bgcolor="#07111f",
    font=dict(family="Barlow, sans-serif", size=12, color="#e2e8f0"),
    margin=dict(l=12, r=12, t=38, b=12),
)

# ─── DATA LOADING ─────────────────────────────────────────────────────────────
CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vRBFU12b6jgWRdNJbj5yKqKJ0iucps7HFJlkmKyjNi2DeccbtnnBM4aQEEbxKOAgKL78DUZJwFIJauX"
    "/pub?gid=2079582736&single=true&output=csv"
)

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(CSV_URL)

    # Limpiar nombres de columnas (quitar espacios y saltos de línea)
    df.columns = df.columns.str.strip()

    # Normalizar nombres clave para usar en el script
    df = df.rename(columns={
        "Categoria":        "Categoría",
        "Comisaria":        "Comisaría",
        "Camara del Evento": "Cámara del Evento",
    })

    # Parse fechas
    df["Marca temporal"] = pd.to_datetime(
        df["Marca temporal"], format="%d/%m/%Y %H:%M:%S", errors="coerce"
    )
    df = df.dropna(subset=["Marca temporal"])

    # Extraer campos de tiempo
    df["Hour"]    = df["Marca temporal"].dt.hour
    df["Weekday"] = df["Marca temporal"].dt.dayofweek   # 0=Lun … 6=Dom

    # Turno
    def get_turno(h, wd):
        if wd < 5:
            if 6 <= h < 14:    return "Turno Mañana"
            elif 14 <= h < 22: return "Turno Tarde"
            else:               return "Turno Noche"
        else:
            if 6 <= h < 18:  return "Turno Mañana"
            else:              return "Turno Noche"

    df["Turno"] = df.apply(lambda r: get_turno(r["Hour"], r["Weekday"]), axis=1)

    # Día semana (ordenado)
    dia_map = {0:"1-Lunes",1:"2-Martes",2:"3-Miércoles",
               3:"4-Jueves",4:"5-Viernes",5:"6-Sábado",6:"7-Domingo"}
    df["Dia Semana"] = df["Weekday"].map(dia_map)

    # Franja horaria (ordenada)
    def get_franja(h):
        franjas = ["1-00:00-03:00","2-03:00-06:00","3-06:00-09:00","4-09:00-12:00",
                   "5-12:00-15:00","6-15:00-18:00","7-18:00-21:00","8-21:00-00:00"]
        return franjas[min(h // 3, 7)]

    df["Franja"] = df["Hour"].apply(get_franja)

    # Subcategoria ya viene consolidada en la columna "Subcategoria"
    if "Subcategoria" not in df.columns:
        subcats = [c for c in df.columns if c.startswith("Subcategoria ")]
        df_sub = df[subcats].replace("", pd.NA)
        df["Subcategoria"] = df_sub.bfill(axis=1).iloc[:, 0].fillna("")
    df["Subcategoria"] = df["Subcategoria"].fillna("").str.strip()

    # Cámara normalizada
    df["Con Cámara"] = df["¿Se ve por cámara?"].str.upper().str.strip() == "SI"

    return df

# ─── CARGA ────────────────────────────────────────────────────────────────────
with st.spinner("Cargando datos..."):
    try:
        df = load_data()
    except Exception as e:
        st.error(f"❌ Error al cargar datos desde Google Sheets: {e}")
        st.stop()

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <span class="header-badge">🚔 COL</span>
    <div class="header-title">Resumen de Novedades</div>
    <span class="header-badge">Centro de Operaciones Lomas</span>
</div>
""", unsafe_allow_html=True)

# ─── FILTROS ──────────────────────────────────────────────────────────────────
min_date = df["Marca temporal"].min().date()
max_date = df["Marca temporal"].max().date()

with st.container():
    fc1, fc2, fc3, fc4, fc5 = st.columns([3, 1.2, 1.5, 1.5, 1])

    with fc1:
        date_range = st.date_input(
            "Período",
            value=(max_date.replace(day=1), max_date),
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY"
        )
    with fc2:
        turnos = ["Todos"] + sorted(df["Turno"].dropna().unique().tolist())
        turno_sel = st.selectbox("Turno", turnos)
    with fc3:
        cats = ["Todas"] + sorted(df["Categoría"].dropna().unique().tolist())
        cat_sel = st.selectbox("Categoría", cats)
    with fc4:
        comisarias = ["Todas"] + sorted(df["Comisaría"].dropna().unique().tolist())
        com_sel = st.selectbox("Comisaría", comisarias)
    with fc5:
        st.markdown("<br>", unsafe_allow_html=True)

# ─── PERÍODOS ─────────────────────────────────────────────────────────────────
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
elif isinstance(date_range, tuple) and len(date_range) == 1:
    start_date = end_date = date_range[0]
else:
    start_date = end_date = date_range

period_days  = (end_date - start_date).days + 1
prev_end     = start_date - timedelta(days=1)
prev_start   = prev_end   - timedelta(days=period_days - 1)

def apply_filters(frame, sd, ed):
    m = (frame["Marca temporal"].dt.date >= sd) & (frame["Marca temporal"].dt.date <= ed)
    if turno_sel != "Todos":
        m &= frame["Turno"] == turno_sel
    if cat_sel != "Todas":
        m &= frame["Categoría"] == cat_sel
    if com_sel != "Todas":
        m &= frame["Comisaría"] == com_sel
    return frame[m].copy()

df_cur  = apply_filters(df, start_date, end_date)
df_prev = apply_filters(df, prev_start, prev_end)

# ─── MÉTRICAS ─────────────────────────────────────────────────────────────────
total_cur  = len(df_cur)
total_prev = len(df_prev)
d_total    = ((total_cur - total_prev) / total_prev * 100) if total_prev else 0

cam_cur  = df_cur["Con Cámara"].mean()  * 100 if total_cur  else 0
cam_prev = df_prev["Con Cámara"].mean() * 100 if total_prev else 0
d_cam    = cam_cur - cam_prev

m1, m2, m3 = st.columns([1, 1, 3])
with m1:
    st.metric("% Novedades con Cámara", f"{cam_cur:.1f}%",
              f"{d_cam:+.1f}% vs Período anterior")
with m2:
    st.metric("Total Novedades", f"{total_cur:,}",
              f"{d_total:+.1f}% vs Período anterior")
with m3:
    buf = io.BytesIO()
    df_cur.drop(columns=["Hour","Weekday","Con Cámara"], errors="ignore").to_excel(
        buf, index=False, engine="openpyxl"
    )
    st.markdown("<div style='display:flex; justify-content:flex-end; margin-top:10px;'>", unsafe_allow_html=True)
    st.download_button(
        "⬇ Descargar datos filtrados",
        data=buf.getvalue(),
        file_name=f"novedades_{start_date}_{end_date}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ─── HEATMAP DÍA / FRANJA ─────────────────────────────────────────────────────
st.markdown('<div class="section-title">Distribución por Día y Franja Horaria</div>', unsafe_allow_html=True)
st.markdown('<div class="section-card">', unsafe_allow_html=True)

hm = (
    df_cur.groupby(["Dia Semana", "Franja"])
    .size().reset_index(name="n")
)
pivot = hm.pivot(index="Dia Semana", columns="Franja", values="n").fillna(0)
pivot = pivot.reindex(sorted(pivot.index))

# Asegurarse de que todas las franjas estén presentes
all_franjas = [f"{i+1}-" + s for i, s in enumerate(
    ["00:00-03:00","03:00-06:00","06:00-09:00","09:00-12:00",
     "12:00-15:00","15:00-18:00","18:00-21:00","21:00-00:00"]
)]
for f in all_franjas:
    if f not in pivot.columns:
        pivot[f] = 0
pivot = pivot[sorted(pivot.columns)]

dias_y   = [d.split("-", 1)[1] for d in pivot.index]
franjas_x = [f.split("-", 1)[1] for f in pivot.columns]

fig_hm = go.Figure(go.Heatmap(
    z=pivot.values,
    x=franjas_x,
    y=dias_y,
    colorscale=[[0, "#0d1f3c"], [0.5, "#0a4a99"], [1, "#1f7ec9"]],
    showscale=False,
    texttemplate="",
    hovertemplate="<b>%{y}</b> · %{x}<br>Novedades: <b>%{z}</b><extra></extra>"
))
fig_hm.update_layout(
    **CHART_LAYOUT,
    height=210,
    xaxis=dict(side="top", showgrid=False, tickfont=dict(size=10, color="#e2e8f0"), linecolor="#334155", tickcolor="#e2e8f0"),
    yaxis=dict(showgrid=False, tickfont=dict(size=10, color="#e2e8f0"), linecolor="#334155", tickcolor="#e2e8f0"),
)
st.plotly_chart(fig_hm, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ─── LÍNEA + TORTA ────────────────────────────────────────────────────────────
col_line, col_pie = st.columns([3, 2])

with col_line:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Evolución de Novedades</div>', unsafe_allow_html=True)

    daily_cur  = df_cur.groupby(df_cur["Marca temporal"].dt.date).size().reset_index(name="n")
    daily_prev = df_prev.groupby(df_prev["Marca temporal"].dt.date).size().reset_index(name="n")

    # Usar fechas reales del período actual en eje X; período anterior como overlay por posición
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=daily_cur["Marca temporal"].astype(str),
        y=daily_cur["n"],
        name="Novedades",
        line=dict(color=TEAL_MED, width=2.5, shape="spline"),
        mode="lines+markers",
        marker=dict(size=5, color=TEAL_MED),
        hovertemplate="%{x}<br>Novedades: <b>%{y}</b><extra></extra>"
    ))
    # Período anterior: alinear por posición sobre el eje del período actual
    if len(daily_prev) > 0:
        x_prev = daily_cur["Marca temporal"].astype(str).values[:len(daily_prev)]
        fig_line.add_trace(go.Scatter(
            x=x_prev,
            y=daily_prev["n"].values[:len(x_prev)],
            name="Período anterior",
            line=dict(color=TEAL_LIGHT, width=1.5, dash="dot", shape="spline"),
            mode="lines+markers",
            marker=dict(size=4, color=TEAL_LIGHT),
            hovertemplate="Anterior: <b>%{y}</b><extra></extra>"
        ))
    fig_line.update_layout(
        **CHART_LAYOUT,
        height=270,
        legend=dict(orientation="h", y=1.12, x=0, font=dict(size=10, color="#e2e8f0")),
        xaxis=dict(showgrid=False, showticklabels=True, tickangle=-30, tickfont=dict(size=10, color="#e2e8f0"), linecolor="#334155", tickcolor="#e2e8f0"),
        yaxis=dict(showgrid=True, gridcolor="rgba(226,232,240,0.08)", zeroline=False, tickfont=dict(color="#e2e8f0"), linecolor="#334155", tickcolor="#e2e8f0"),
    )
    st.plotly_chart(fig_line, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_pie:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">% Participación por Turno</div>', unsafe_allow_html=True)
    turno_data = df_cur["Turno"].value_counts().reset_index()
    turno_data.columns = ["Turno", "n"]
    fig_pie = px.pie(
        turno_data, values="n", names="Turno",
        color_discrete_sequence=COLOR_SEQ,
        hole=0.3
    )
    fig_pie.update_traces(
        textposition="inside",
        textinfo="percent+label",
        textfont=dict(size=11, color="#e2e8f0"),
        hovertemplate="%{label}<br><b>%{value}</b> (%{percent})<extra></extra>"
    )
    fig_pie.update_layout(**CHART_LAYOUT, height=270, showlegend=False)
    st.plotly_chart(fig_pie, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ─── TOP 5 ────────────────────────────────────────────────────────────────────
def top5_bar(data_series, title):
    top = data_series.value_counts().head(5).reset_index()
    top.columns = ["label", "n"]
    top = top.sort_values("n")
    fig = go.Figure(go.Bar(
        x=top["n"], y=top["label"],
        orientation="h",
        marker=dict(
            color=top["n"],
            colorscale=[[0, TEAL_LIGHT], [1, TEAL_DARK]],
            showscale=False,
            line=dict(color="rgba(255,255,255,0.12)", width=1)
        ),
        text=top["n"],
        textposition="outside",
        textfont=dict(size=11, color="#e2e8f0"),
        hovertemplate="%{y}: <b>%{x}</b><extra></extra>"
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text=title, font=dict(size=13, color="#e2e8f0", weight=700)),
        height=260,
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=11, color="#e2e8f0"), linecolor="#334155", tickcolor="#e2e8f0"),
        bargap=0.33,
    )
    return fig

st.markdown('<div class="section-card">', unsafe_allow_html=True)
b1, b2, b3 = st.columns(3)
with b1:
    st.plotly_chart(top5_bar(df_cur["Categoría"], "Top 5 por Categoría"),
                    use_container_width=True)
with b2:
    sub_nonempty = df_cur[df_cur["Subcategoria"].str.strip() != ""]["Subcategoria"]
    st.plotly_chart(top5_bar(sub_nonempty, "Top 5 por Subcategoría"),
                    use_container_width=True)
with b3:
    st.plotly_chart(top5_bar(df_cur["Comisaría"], "Top 5 por Comisaría"),
                    use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center; color:#90a4ae; font-size:0.75rem; margin-top:10px;">
    Centro de Operaciones Lomas · Datos actualizados cada 5 min ·
    Período seleccionado: {start_date.strftime('%d/%m/%Y')} al {end_date.strftime('%d/%m/%Y')}
    ({period_days} días) · Período anterior: {prev_start.strftime('%d/%m/%Y')} al {prev_end.strftime('%d/%m/%Y')}
</div>
""", unsafe_allow_html=True)
