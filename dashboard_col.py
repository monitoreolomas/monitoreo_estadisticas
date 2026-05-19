import streamlit as st
st.cache_data.clear()
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import io
import os

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Centro de Operaciones Lomas",
    page_icon="🚔",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── SESSION STATE ────────────────────────────────────────────────────────────
if "pagina"           not in st.session_state: st.session_state.pagina           = "resumen"
if "pie_mode_resumen" not in st.session_state: st.session_state.pie_mode_resumen = "turno"
if "pie_mode_detalle" not in st.session_state: st.session_state.pie_mode_detalle = "turno"

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
    .block-container { padding: 1rem 1.5rem 1.5rem; max-width: 100%; background: #060b17; }

    /* Header */
    .main-header {
        background: linear-gradient(135deg, #0b1630 0%, #092040 45%, #0d3260 100%);
        padding: 20px 30px;
        border-radius: 25px;
        text-align: center;
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
        font-size: 1.9rem;
        font-weight: 800;
        font-style: italic;
        text-shadow: 0 4px 18px rgba(0,0,0,0.35);
        letter-spacing: 0.4px;
        margin: 0;
    }

    /* Cards */
    .section-card {
        background: rgba(15,23,42,0.85);
        border: 1px solid rgba(56,189,248,0.15);
        border-radius: 25px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.35);
        padding: 20px 22px 22px;
        margin-bottom: 18px;
        overflow: hidden;
    }

    /* KPI */
    .kpi-card {
        background: rgba(15,23,42,0.92);
        border: 1px solid rgba(56,189,248,0.22);
        border-radius: 25px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.40);
        padding: 20px 26px;
        margin-bottom: 4px;
        border-left: 5px solid #38bdf8;
    }
    .kpi-label  { font-size:.88rem; color:#94a3b8; font-weight:600; letter-spacing:.03em; margin-bottom:4px; }
    .kpi-value  { font-size:2.4rem; color:#f8fafc; font-weight:800; line-height:1.1; }
    .kpi-delta-pos { font-size:.85rem; color:#4ade80; font-weight:600; margin-top:4px; }
    .kpi-delta-neg { font-size:.85rem; color:#f87171; font-weight:600; margin-top:4px; }
    .kpi-delta-neu { font-size:.85rem; color:#94a3b8; font-weight:600; margin-top:4px; }

    /* Section title */
    .section-title {
        font-size:1.05rem; font-weight:700; color:#e2e8f0;
        margin-bottom:14px; padding-bottom:7px;
        border-bottom:2px solid rgba(56,189,248,0.18);
    }

    /* Buttons */
    .stButton > button {
        border-radius:18px !important; font-weight:700 !important;
        font-size:.9rem !important; padding:8px 18px !important;
        transition:all .2s ease !important;
    }
    .stDownloadButton button {
        background:#38bdf8 !important; color:#0f172a !important;
        border:none !important; border-radius:18px !important;
        font-weight:700 !important; font-size:.9rem !important; padding:9px 18px !important;
    }
    .stDownloadButton button:hover { background:#22c55e !important; color:#020617 !important; }

    /* Ocultar toolbar de Plotly */
    .js-plotly-plot .plotly .modebar { display: none !important; }

    hr { border-color:rgba(56,189,248,0.15); margin:14px 0; }
    label { font-size:.92rem !important; color:#cbd5e1 !important; font-weight:600 !important; }
</style>
""", unsafe_allow_html=True)

# ─── PALETA ───────────────────────────────────────────────────────────────────
TEAL_DARK   = "#0ea5e9"
TEAL_MED    = "#38bdf8"
TEAL_LIGHT  = "#7dd3fc"
COLOR_SEQ   = ["#22d3ee","#38bdf8","#0ea5e9","#0284c7","#0369a1"]
COLOR_TURNO = {"Turno Mañana":"#22d3ee","Turno Tarde":"#f59e0b","Turno Noche":"#0284c7"}

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Barlow, sans-serif", size=12, color="#e2e8f0"),
    margin=dict(l=12, r=12, t=44, b=12),
)

# ─── DATA ─────────────────────────────────────────────────────────────────────
CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vRBFU12b6jgWRdNJbj5yKqKJ0iucps7HFJlkmKyjNi2DeccbtnnBM4aQEEbxKOAgKL78DUZJwFIJauX"
    "/pub?gid=2079582736&single=true&output=csv"
)

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={"Categoria":"Categoría","Comisaria":"Comisaría","Camara del Evento":"Cámara del Evento"})
    df["Marca temporal"] = pd.to_datetime(df["Marca temporal"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    df = df.dropna(subset=["Marca temporal"])
    df["Hour"]    = df["Marca temporal"].dt.hour
    df["Weekday"] = df["Marca temporal"].dt.dayofweek

    def get_turno(h, wd):
        if wd < 5:
            if 6 <= h < 14:    return "Turno Mañana"
            elif 14 <= h < 22: return "Turno Tarde"
            else:               return "Turno Noche"
        else:
            return "Turno Mañana" if 6 <= h < 18 else "Turno Noche"

    df["Turno"]    = df.apply(lambda r: get_turno(r["Hour"], r["Weekday"]), axis=1)
    dia_map = {0:"1-Lunes",1:"2-Martes",2:"3-Miércoles",3:"4-Jueves",4:"5-Viernes",5:"6-Sábado",6:"7-Domingo"}
    df["Dia Semana"] = df["Weekday"].map(dia_map)
    df["Tipo Dia"]   = df["Weekday"].apply(lambda x: "Lu - Vie" if x < 5 else "Fin de Semana")

    def get_franja(h):
        franjas = ["1-00:00-03:00","2-03:00-06:00","3-06:00-09:00","4-09:00-12:00",
                   "5-12:00-15:00","6-15:00-18:00","7-18:00-21:00","8-21:00-00:00"]
        return franjas[min(h//3,7)]
    df["Franja"] = df["Hour"].apply(get_franja)

    if "Subcategoria" not in df.columns:
        subcats = [c for c in df.columns if c.startswith("Subcategoria ")]
        df["Subcategoria"] = df[subcats].replace("", pd.NA).bfill(axis=1).iloc[:,0].fillna("")
    df["Subcategoria"] = df["Subcategoria"].fillna("").str.strip()
    df["Con Cámara"]   = df["¿Se ve por cámara?"].str.upper().str.strip() == "SI"
    return df

with st.spinner("Cargando datos..."):
    try:
        df = load_data()
    except Exception as e:
        st.error(f"❌ Error al cargar datos: {e}")
        st.stop()

min_date = df["Marca temporal"].min().date()
max_date = df["Marca temporal"].max().date()

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def render_kpi(label, value_str, delta_val, delta_str):
    cls   = "kpi-delta-pos" if delta_val > 0 else ("kpi-delta-neg" if delta_val < 0 else "kpi-delta-neu")
    arrow = "▲" if delta_val > 0 else ("▼" if delta_val < 0 else "●")
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value_str}</div>
        <div class="{cls}">{arrow} {delta_str}</div>
    </div>""", unsafe_allow_html=True)

def render_header(titulo):
    c_left, c_mid, c_right = st.columns([1, 6, 1])
    with c_left:
        st.markdown("<div style='display:flex;align-items:center;justify-content:center;height:100%;padding-top:6px;'>", unsafe_allow_html=True)
        if os.path.exists("logo_izquierda.png"):
            st.image("logo_izquierda.png", width=72)
        st.markdown("</div>", unsafe_allow_html=True)
    with c_mid:
        st.markdown(f'<div class="main-header"><div class="header-title">{titulo}</div></div>', unsafe_allow_html=True)
    with c_right:
        st.markdown("<div style='display:flex;align-items:center;justify-content:center;height:100%;padding-top:6px;'>", unsafe_allow_html=True)
        if os.path.exists("logo_derecha.png"):
            st.image("logo_derecha.png", width=72)
        st.markdown("</div>", unsafe_allow_html=True)

# ─── GRÁFICOS ─────────────────────────────────────────────────────────────────
def top5_bar(data_series, title):
    top = data_series.value_counts().head(5).reset_index()
    top.columns = ["label","n"]
    top = top.sort_values("n")
    fig = go.Figure(go.Bar(
        x=top["n"], y=top["label"], orientation="h",
        marker=dict(color=top["n"], colorscale=[[0,TEAL_LIGHT],[1,TEAL_DARK]],
                    showscale=False, line=dict(color="rgba(255,255,255,0.08)",width=1)),
        text=top["n"], textposition="outside",
        textfont=dict(size=12,color="#e2e8f0"),
        hovertemplate="%{y}: <b>%{x}</b><extra></extra>"
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text=title, font=dict(size=13,color="#e2e8f0",weight=700)),
        height=310,
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=12,color="#e2e8f0")),
        bargap=0.3,
    )
    return fig

def render_heatmap(df_filt):
    hm    = df_filt.groupby(["Dia Semana","Franja"]).size().reset_index(name="n")
    pivot = hm.pivot(index="Dia Semana", columns="Franja", values="n").fillna(0)
    pivot = pivot.reindex(sorted(pivot.index))
    all_f = [f"{i+1}-"+s for i,s in enumerate(
        ["00:00-03:00","03:00-06:00","06:00-09:00","09:00-12:00",
         "12:00-15:00","15:00-18:00","18:00-21:00","21:00-00:00"])]
    for f in all_f:
        if f not in pivot.columns: pivot[f] = 0
    pivot     = pivot[sorted(pivot.columns)]
    dias_y    = [d.split("-",1)[1] for d in pivot.index]
    franjas_x = [f.split("-",1)[1] for f in pivot.columns]
    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=franjas_x, y=dias_y,
        colorscale=[[0,"#0d1f3c"],[0.5,"#0a4a99"],[1,"#1f7ec9"]],
        showscale=False,
        hovertemplate="<b>%{y}</b> · %{x}<br>Novedades: <b>%{z}</b><extra></extra>"
    ))
    fig.update_layout(
        **CHART_LAYOUT, height=250,
        xaxis=dict(side="top", showgrid=False, tickfont=dict(size=10,color="#e2e8f0")),
        yaxis=dict(showgrid=False, tickfont=dict(size=10,color="#e2e8f0")),
    )
    return fig

def render_linea(df_cur, df_prev):
    daily_cur  = df_cur.groupby(df_cur["Marca temporal"].dt.date).size().reset_index(name="n")
    daily_prev = df_prev.groupby(df_prev["Marca temporal"].dt.date).size().reset_index(name="n")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_cur["Marca temporal"].astype(str), y=daily_cur["n"],
        name="Novedades", line=dict(color=TEAL_MED,width=2.5,shape="spline"),
        mode="lines+markers", marker=dict(size=5,color=TEAL_MED),
        hovertemplate="%{x}<br>Novedades: <b>%{y}</b><extra></extra>"
    ))
    if len(daily_prev) > 0:
        x_prev = daily_cur["Marca temporal"].astype(str).values[:len(daily_prev)]
        fig.add_trace(go.Scatter(
            x=x_prev, y=daily_prev["n"].values[:len(x_prev)],
            name="Período anterior",
            line=dict(color=TEAL_LIGHT,width=1.5,dash="dot",shape="spline"),
            mode="lines+markers", marker=dict(size=4,color=TEAL_LIGHT),
            hovertemplate="Anterior: <b>%{y}</b><extra></extra>"
        ))
    fig.update_layout(
        **CHART_LAYOUT, height=320,
        legend=dict(orientation="h", y=1.12, x=0, font=dict(size=11,color="#e2e8f0")),
        xaxis=dict(showgrid=False, tickangle=-30, tickfont=dict(size=10,color="#e2e8f0")),
        yaxis=dict(showgrid=True, gridcolor="rgba(226,232,240,0.08)", zeroline=False,
                   tickfont=dict(color="#e2e8f0")),
    )
    return fig

def render_pie(df_filt, mode):
    import math
    col    = "Turno" if mode == "turno" else "Tipo Dia"
    data   = df_filt[col].value_counts().reset_index()
    data.columns = [col, "n"]
    colors = list(COLOR_TURNO.values()) if mode == "turno" else ["#22d3ee", "#f59e0b"]
    total  = data["n"].sum()

    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=data[col],
        values=data["n"],
        hole=0.38,
        marker=dict(colors=colors, line=dict(color="#060b17", width=2)),
        textinfo="none",
        hovertemplate="%{label}<br><b>%{value}</b> (%{percent})<extra></extra>",
        sort=False,
        direction="clockwise",
    ))

    # Calcular annotations dentro del slice con fondo gris
    annotations = []
    angle = 90.0
    for _, row in data.iterrows():
        pct       = row["n"] / total
        sweep     = pct * 360
        mid_angle = math.radians(angle - sweep / 2)
        r = 0.62   # radio al centro del anillo (ajustado al hole=0.38)
        x = 0.5 + r * 0.5 * math.cos(mid_angle)
        y = 0.5 + r * 0.5 * math.sin(mid_angle)
        annotations.append(dict(
            text=f"<b>{row[col]}</b><br>{pct*100:.1f}%",
            x=x, y=y,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=11, color="#ffffff", family="Barlow, sans-serif"),
            bgcolor="rgba(30,30,30,0.78)",
            bordercolor="rgba(255,255,255,0.12)",
            borderpad=6,
            borderwidth=1,
            align="center",
        ))
        angle -= sweep

    layout = {**CHART_LAYOUT}
    layout["margin"] = dict(l=20, r=20, t=10, b=48)
    fig.update_layout(
        **layout,
        height=340,
        annotations=annotations,
        showlegend=True,
        legend=dict(
            orientation="h",
            x=0.5, y=-0.04,
            xanchor="center",
            yanchor="top",
            font=dict(size=12, color="#e2e8f0"),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            title_text="",
        ),
    )
    return fig

def render_top_horario(df_filt):
    top = df_filt["Franja"].value_counts().head(5).reset_index()
    top.columns = ["label","n"]
    top["label"] = top["label"].str.split("-", n=1).str[1]
    top = top.sort_values("n")
    fig = go.Figure(go.Bar(
        x=top["n"], y=top["label"], orientation="h",
        marker=dict(color=top["n"], colorscale=[[0,TEAL_LIGHT],[1,TEAL_DARK]], showscale=False),
        text=top["n"], textposition="outside",
        textfont=dict(size=12,color="#e2e8f0"),
        hovertemplate="%{y}: <b>%{x}</b><extra></extra>"
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        height=320,
        # sin título interno — viene del section-title del card
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, title=None),
        yaxis=dict(showgrid=False, tickfont=dict(size=12,color="#e2e8f0"), title=None),
        bargap=0.3,
    )
    return fig

def render_comisaria_turno(df_filt):
    ct = df_filt.groupby(["Comisaría","Turno"]).size().reset_index(name="n")
    turno_order = ["Turno Mañana","Turno Tarde","Turno Noche"]
    ct["Turno"] = pd.Categorical(ct["Turno"], categories=turno_order, ordered=True)
    ct = ct.sort_values("Turno")
    fig = px.bar(ct, x="Comisaría", y="n", color="Turno",
                 color_discrete_map=COLOR_TURNO, barmode="stack")
    fig.update_layout(
        **CHART_LAYOUT,
        height=320,
        xaxis=dict(showgrid=False, tickangle=-35,
                   tickfont=dict(size=9,color="#e2e8f0"),
                   title=None, showticklabels=True),
        yaxis=dict(showgrid=True, gridcolor="rgba(226,232,240,0.08)",
                   zeroline=False, tickfont=dict(color="#e2e8f0"), title=None),
        legend=dict(
            orientation="h", y=1.08, x=0,
            font=dict(size=12, color="#ffffff"),
            bgcolor="rgba(90,90,90,0.55)",
            bordercolor="rgba(255,255,255,0.1)", borderwidth=1,
            title_text=""
        ),
        bargap=0.2,
    )
    return fig

# ─── TOGGLE TORTA ─────────────────────────────────────────────────────────────
def pie_toggle_row(key):
    """Botones Turno/Día alineados a la derecha dentro del card."""
    mode = st.session_state[f"pie_mode_{key}"]
    _, col_t, col_d = st.columns([6, 1, 1])
    with col_t:
        if st.button("Turno", key=f"btn_turno_{key}",
                     type="primary" if mode=="turno" else "secondary"):
            st.session_state[f"pie_mode_{key}"] = "turno"
            st.rerun()
    with col_d:
        if st.button("Día", key=f"btn_dia_{key}",
                     type="primary" if mode=="dia" else "secondary"):
            st.session_state[f"pie_mode_{key}"] = "dia"
            st.rerun()
    return mode

# ══════════════════════════════════════════════════════════════════════════════
#  PÁGINA 1 – RESUMEN
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.pagina == "resumen":

    render_header("Resumen mensual novedades")

    # Filtros (primero capturamos fecha y turno para filtrar antes de dibujar botones)
    fc1, fc2, fc_dl, fc_nav = st.columns([3, 1.5, 1.6, 1.4])
    with fc1:
        date_range = st.date_input(
            "Período",
            value=(max_date.replace(day=1), max_date),
            min_value=min_date, max_value=max_date, format="DD/MM/YYYY"
        )
    with fc2:
        turnos    = ["Todos"] + sorted(df["Turno"].dropna().unique().tolist())
        turno_sel = st.selectbox("Turno", turnos)

    # Períodos (calculados antes de renderizar los botones)
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    elif isinstance(date_range, tuple) and len(date_range) == 1:
        start_date = end_date = date_range[0]
    else:
        start_date = end_date = date_range

    period_days = (end_date - start_date).days + 1
    prev_end    = start_date - timedelta(days=1)
    prev_start  = prev_end - timedelta(days=period_days - 1)

    def filt_resumen(frame, sd, ed):
        m = (frame["Marca temporal"].dt.date >= sd) & (frame["Marca temporal"].dt.date <= ed)
        if turno_sel != "Todos": m &= frame["Turno"] == turno_sel
        return frame[m].copy()

    df_cur  = filt_resumen(df, start_date, end_date)
    df_prev = filt_resumen(df, prev_start, prev_end)

    # Botones en la misma fila que los filtros, alineados
    buf = io.BytesIO()
    df_cur.drop(columns=["Hour","Weekday","Con Cámara"], errors="ignore").to_excel(buf, index=False, engine="openpyxl")
    with fc_dl:
        st.markdown("<label style='visibility:hidden;font-size:.92rem;font-weight:600;'>.</label>", unsafe_allow_html=True)
        st.download_button(
            "⬇ Descargar Excel", data=buf.getvalue(),
            file_name=f"novedades_{start_date}_{end_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    with fc_nav:
        st.markdown("<label style='visibility:hidden;font-size:.92rem;font-weight:600;'>.</label>", unsafe_allow_html=True)
        if st.button("🔍 Ver Detalle →", type="primary", use_container_width=True):
            st.session_state.pagina = "detalle"
            st.rerun()

    # KPIs
    total_cur  = len(df_cur)
    total_prev = len(df_prev)
    d_total    = ((total_cur - total_prev) / total_prev * 100) if total_prev else 0
    cam_cur    = df_cur["Con Cámara"].mean() * 100 if total_cur else 0
    cam_prev   = df_prev["Con Cámara"].mean() * 100 if total_prev else 0
    d_cam      = cam_cur - cam_prev

    k1, k2, _ = st.columns([1.3, 1.3, 5])
    with k1: render_kpi("% Cámara",        f"{cam_cur:.1f}%", d_cam,   f"{d_cam:+.1f}% vs Período anterior")
    with k2: render_kpi("Total Novedades", f"{total_cur:,}",  d_total, f"{d_total:+.1f}% vs Período anterior")

    st.markdown("<hr>", unsafe_allow_html=True)

    # Heatmap
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Distribución por Día y Franja Horaria</div>', unsafe_allow_html=True)
    st.plotly_chart(render_heatmap(df_cur), use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

    # Línea + Torta
    col_line, col_pie = st.columns([3, 2])
    with col_line:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Evolución de Novedades</div>', unsafe_allow_html=True)
        st.plotly_chart(render_linea(df_cur, df_prev), use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_pie:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">% Participación por Turno y Día</div>', unsafe_allow_html=True)
        pie_mode = pie_toggle_row("resumen")
        st.plotly_chart(render_pie(df_cur, pie_mode), use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Top 5
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    b1, b2, b3 = st.columns(3)
    with b1:
        st.plotly_chart(top5_bar(df_cur["Categoría"],  "Top 5 por Categoría"),
                        use_container_width=True, config={"displayModeBar":False})
    with b2:
        sub_ne = df_cur[df_cur["Subcategoria"].str.strip() != ""]["Subcategoria"]
        st.plotly_chart(top5_bar(sub_ne, "Top 5 por Subcategoría"),
                        use_container_width=True, config={"displayModeBar":False})
    with b3:
        st.plotly_chart(top5_bar(df_cur["Comisaría"], "Top 5 por Comisaría"),
                        use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div style="text-align:center;color:#64748b;font-size:.75rem;margin-top:8px;">
        Centro de Operaciones Lomas · Datos actualizados cada 5 min ·
        Período: {start_date.strftime('%d/%m/%Y')} al {end_date.strftime('%d/%m/%Y')}
        ({period_days} días) · Período anterior: {prev_start.strftime('%d/%m/%Y')} al {prev_end.strftime('%d/%m/%Y')}
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PÁGINA 2 – DETALLE
# ══════════════════════════════════════════════════════════════════════════════
else:

    render_header("Detalle mensual novedades")

    # Filtros
    fc1, fc2, fc3, fc4, fc5 = st.columns([2.5, 1.3, 1.5, 1.3, 1.3])
    with fc1:
        date_range2 = st.date_input(
            "Período",
            value=(max_date.replace(day=1), max_date),
            min_value=min_date, max_value=max_date, format="DD/MM/YYYY", key="dr2"
        )
    with fc2:
        cats2    = ["Todas"] + sorted(df["Categoría"].dropna().unique().tolist())
        cat_sel2 = st.selectbox("Categoría", cats2, key="cat2")
    with fc3:
        if cat_sel2 != "Todas":
            subs_d = df[df["Categoría"]==cat_sel2]["Subcategoria"]
            subs_d = subs_d[subs_d.str.strip()!=""].dropna().unique().tolist()
        else:
            subs_d = df["Subcategoria"][df["Subcategoria"].str.strip()!=""].dropna().unique().tolist()
        sub_sel2 = st.selectbox("Subcategoría", ["Todas"]+sorted(subs_d), key="sub2")
    with fc4:
        turno_sel2 = st.selectbox("Turno", ["Todos"]+sorted(df["Turno"].dropna().unique().tolist()), key="turno2")
    with fc5:
        com_sel2   = st.selectbox("Comisaría", ["Todas"]+sorted(df["Comisaría"].dropna().unique().tolist()), key="com2")

    # Períodos
    if isinstance(date_range2, tuple) and len(date_range2) == 2:
        start_date2, end_date2 = date_range2
    elif isinstance(date_range2, tuple) and len(date_range2) == 1:
        start_date2 = end_date2 = date_range2[0]
    else:
        start_date2 = end_date2 = date_range2

    period_days2 = (end_date2 - start_date2).days + 1
    prev_end2    = start_date2 - timedelta(days=1)
    prev_start2  = prev_end2 - timedelta(days=period_days2 - 1)

    def filt_detalle(frame, sd, ed):
        m = (frame["Marca temporal"].dt.date >= sd) & (frame["Marca temporal"].dt.date <= ed)
        if turno_sel2 != "Todos":  m &= frame["Turno"]        == turno_sel2
        if cat_sel2   != "Todas":  m &= frame["Categoría"]    == cat_sel2
        if sub_sel2   != "Todas":  m &= frame["Subcategoria"] == sub_sel2
        if com_sel2   != "Todas":  m &= frame["Comisaría"]    == com_sel2
        return frame[m].copy()

    df_cur2  = filt_detalle(df, start_date2, end_date2)
    df_prev2 = filt_detalle(df, prev_start2, prev_end2)

    # KPI + botones a la derecha
    total_cur2  = len(df_cur2)
    total_prev2 = len(df_prev2)
    d_total2    = ((total_cur2 - total_prev2) / total_prev2 * 100) if total_prev2 else 0

    kd1, kd_sp, kd_back, kd_dl = st.columns([1.4, 3.5, 1.1, 1.5])
    with kd1:
        render_kpi("Total Novedades", f"{total_cur2:,}", d_total2,
                   f"{d_total2:+.1f}% vs Período anterior")
    with kd_sp:
        pass
    with kd_back:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("← Volver", type="secondary", use_container_width=True):
            st.session_state.pagina = "resumen"
            st.rerun()
    with kd_dl:
        buf2 = io.BytesIO()
        df_cur2.drop(columns=["Hour","Weekday","Con Cámara"], errors="ignore").to_excel(buf2, index=False, engine="openpyxl")
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        st.download_button(
            "⬇ Descargar Excel", data=buf2.getvalue(),
            file_name=f"novedades_detalle_{start_date2}_{end_date2}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl2", use_container_width=True
        )

    st.markdown("<hr>", unsafe_allow_html=True)

    # Heatmap
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Distribución por Día y Franja Horaria</div>', unsafe_allow_html=True)
    st.plotly_chart(render_heatmap(df_cur2), use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

    # Línea + Top Horario
    col_l2, col_t2 = st.columns([3, 2])
    with col_l2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Evolución de Novedades</div>', unsafe_allow_html=True)
        st.plotly_chart(render_linea(df_cur2, df_prev2), use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_t2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Top 5 por Rango Horario</div>', unsafe_allow_html=True)
        st.plotly_chart(render_top_horario(df_cur2), use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    # Torta + Comisaría x Turno
    col_p2, col_b2 = st.columns([2, 3])
    with col_p2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">% Participación por Turno y Día</div>', unsafe_allow_html=True)
        pie_mode2 = pie_toggle_row("detalle")
        st.plotly_chart(render_pie(df_cur2, pie_mode2), use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Novedades por Comisaría y Turno</div>', unsafe_allow_html=True)
        st.plotly_chart(render_comisaria_turno(df_cur2), use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div style="text-align:center;color:#64748b;font-size:.75rem;margin-top:8px;">
        Centro de Operaciones Lomas · Datos actualizados cada 5 min ·
        Período: {start_date2.strftime('%d/%m/%Y')} al {end_date2.strftime('%d/%m/%Y')}
        ({period_days2} días) · Período anterior: {prev_start2.strftime('%d/%m/%Y')} al {prev_end2.strftime('%d/%m/%Y')}
    </div>""", unsafe_allow_html=True)
