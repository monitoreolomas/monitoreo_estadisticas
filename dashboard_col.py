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

# ─── SESSION STATE: navegación y toggle torta ─────────────────────────────────
if "pagina" not in st.session_state:
    st.session_state.pagina = "resumen"
if "pie_mode_resumen" not in st.session_state:
    st.session_state.pie_mode_resumen = "turno"
if "pie_mode_detalle" not in st.session_state:
    st.session_state.pie_mode_detalle = "turno"

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
        padding: 22px 30px;
        border-radius: 25px;
        margin-bottom: 18px;
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
        font-size: 1.9rem;
        font-weight: 800;
        font-style: italic;
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

    /* Cards con bordes redondeados 25px */
    .section-card {
        background: rgba(15,23,42,0.85);
        border: 1px solid rgba(56,189,248,0.15);
        border-radius: 25px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.35);
        padding: 20px 22px 22px;
        margin-bottom: 18px;
    }

    /* KPI cards redondeadas */
    .kpi-card {
        background: rgba(15,23,42,0.92);
        border: 1px solid rgba(56,189,248,0.22);
        border-radius: 25px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.40);
        padding: 20px 26px;
        margin-bottom: 4px;
        border-left: 5px solid #38bdf8;
    }
    .kpi-label {
        font-size: 0.88rem;
        color: #94a3b8;
        font-weight: 600;
        letter-spacing: 0.03em;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 2.4rem;
        color: #f8fafc;
        font-weight: 800;
        line-height: 1.1;
    }
    .kpi-delta-pos {
        font-size: 0.85rem;
        color: #4ade80;
        font-weight: 600;
        margin-top: 4px;
    }
    .kpi-delta-neg {
        font-size: 0.85rem;
        color: #f87171;
        font-weight: 600;
        margin-top: 4px;
    }
    .kpi-delta-neu {
        font-size: 0.85rem;
        color: #94a3b8;
        font-weight: 600;
        margin-top: 4px;
    }

    /* Section title */
    .section-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #e2e8f0;
        margin-bottom: 14px;
        padding-bottom: 7px;
        border-bottom: 2px solid rgba(56,189,248,0.18);
    }

    /* Nav buttons */
    .stButton > button {
        border-radius: 18px !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        padding: 8px 18px !important;
        transition: all 0.2s ease !important;
    }
    
    /* Toggle buttons para torta */
    .toggle-btn-active {
        background: #38bdf8 !important;
        color: #0f172a !important;
        border: none !important;
    }
    .toggle-btn-inactive {
        background: rgba(56,189,248,0.1) !important;
        color: #94a3b8 !important;
        border: 1px solid rgba(56,189,248,0.25) !important;
    }

    /* Download button */
    .stDownloadButton button {
        background: #38bdf8 !important;
        color: #0f172a !important;
        border: none !important;
        border-radius: 18px !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        padding: 9px 18px !important;
    }
    .stDownloadButton button:hover { background: #22c55e !important; color: #020617 !important; }

    /* Divider */
    hr { border-color: rgba(56,189,248,0.15); margin: 14px 0; }

    /* Selectbox & date input labels */
    label { font-size: 0.92rem !important; color: #cbd5e1 !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

# ─── PALETA ───────────────────────────────────────────────────────────────────
TEAL_DARK   = "#0ea5e9"
TEAL_MED    = "#38bdf8"
TEAL_LIGHT  = "#7dd3fc"
COLOR_SEQ   = ["#22d3ee", "#38bdf8", "#0ea5e9", "#0284c7", "#0369a1"]

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
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
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        "Categoria":         "Categoría",
        "Comisaria":         "Comisaría",
        "Camara del Evento": "Cámara del Evento",
    })

    df["Marca temporal"] = pd.to_datetime(
        df["Marca temporal"], format="%d/%m/%Y %H:%M:%S", errors="coerce"
    )
    df = df.dropna(subset=["Marca temporal"])

    df["Hour"]    = df["Marca temporal"].dt.hour
    df["Weekday"] = df["Marca temporal"].dt.dayofweek  # 0=Lun…6=Dom

    def get_turno(h, wd):
        if wd < 5:
            if 6 <= h < 14:    return "Turno Mañana"
            elif 14 <= h < 22: return "Turno Tarde"
            else:               return "Turno Noche"
        else:
            if 6 <= h < 18:  return "Turno Mañana"
            else:              return "Turno Noche"

    df["Turno"] = df.apply(lambda r: get_turno(r["Hour"], r["Weekday"]), axis=1)

    dia_map = {0:"1-Lunes",1:"2-Martes",2:"3-Miércoles",
               3:"4-Jueves",4:"5-Viernes",5:"6-Sábado",6:"7-Domingo"}
    df["Dia Semana"] = df["Weekday"].map(dia_map)

    # Tipo de día: semana / fin de semana
    df["Tipo Dia"] = df["Weekday"].apply(lambda x: "Lu - Vie" if x < 5 else "Fin de Semana")

    def get_franja(h):
        franjas = ["1-00:00-03:00","2-03:00-06:00","3-06:00-09:00","4-09:00-12:00",
                   "5-12:00-15:00","6-15:00-18:00","7-18:00-21:00","8-21:00-00:00"]
        return franjas[min(h // 3, 7)]

    df["Franja"] = df["Hour"].apply(get_franja)

    if "Subcategoria" not in df.columns:
        subcats = [c for c in df.columns if c.startswith("Subcategoria ")]
        df_sub = df[subcats].replace("", pd.NA)
        df["Subcategoria"] = df_sub.bfill(axis=1).iloc[:, 0].fillna("")
    df["Subcategoria"] = df["Subcategoria"].fillna("").str.strip()

    df["Con Cámara"] = df["¿Se ve por cámara?"].str.upper().str.strip() == "SI"

    return df

# ─── CARGA ────────────────────────────────────────────────────────────────────
with st.spinner("Cargando datos..."):
    try:
        df = load_data()
    except Exception as e:
        st.error(f"❌ Error al cargar datos desde Google Sheets: {e}")
        st.stop()

min_date = df["Marca temporal"].min().date()
max_date = df["Marca temporal"].max().date()

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def render_kpi(label, value_str, delta_val, delta_str):
    if delta_val > 0:
        cls = "kpi-delta-pos"
        arrow = "▲"
    elif delta_val < 0:
        cls = "kpi-delta-neg"
        arrow = "▼"
    else:
        cls = "kpi-delta-neu"
        arrow = "●"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value_str}</div>
        <div class="{cls}">{arrow} {delta_str}</div>
    </div>
    """, unsafe_allow_html=True)

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
            line=dict(color="rgba(255,255,255,0.1)", width=1)
        ),
        text=top["n"],
        textposition="outside",
        textfont=dict(size=11, color="#e2e8f0"),
        hovertemplate="%{y}: <b>%{x}</b><extra></extra>"
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text=title, font=dict(size=13, color="#e2e8f0", weight=700)),
        height=250,
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=11, color="#e2e8f0")),
        bargap=0.33,
    )
    return fig

def render_heatmap(df_filt):
    hm = df_filt.groupby(["Dia Semana","Franja"]).size().reset_index(name="n")
    pivot = hm.pivot(index="Dia Semana", columns="Franja", values="n").fillna(0)
    pivot = pivot.reindex(sorted(pivot.index))
    all_franjas = [f"{i+1}-" + s for i, s in enumerate(
        ["00:00-03:00","03:00-06:00","06:00-09:00","09:00-12:00",
         "12:00-15:00","15:00-18:00","18:00-21:00","21:00-00:00"]
    )]
    for f in all_franjas:
        if f not in pivot.columns:
            pivot[f] = 0
    pivot = pivot[sorted(pivot.columns)]
    dias_y    = [d.split("-", 1)[1] for d in pivot.index]
    franjas_x = [f.split("-", 1)[1] for f in pivot.columns]
    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=franjas_x, y=dias_y,
        colorscale=[[0,"#0d1f3c"],[0.5,"#0a4a99"],[1,"#1f7ec9"]],
        showscale=False, texttemplate="",
        hovertemplate="<b>%{y}</b> · %{x}<br>Novedades: <b>%{z}</b><extra></extra>"
    ))
    fig.update_layout(
        **CHART_LAYOUT, height=210,
        xaxis=dict(side="top", showgrid=False, tickfont=dict(size=10, color="#e2e8f0")),
        yaxis=dict(showgrid=False, tickfont=dict(size=10, color="#e2e8f0")),
    )
    return fig

def render_linea(df_cur, df_prev):
    daily_cur  = df_cur.groupby(df_cur["Marca temporal"].dt.date).size().reset_index(name="n")
    daily_prev = df_prev.groupby(df_prev["Marca temporal"].dt.date).size().reset_index(name="n")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_cur["Marca temporal"].astype(str), y=daily_cur["n"],
        name="Novedades",
        line=dict(color=TEAL_MED, width=2.5, shape="spline"),
        mode="lines+markers", marker=dict(size=5, color=TEAL_MED),
        hovertemplate="%{x}<br>Novedades: <b>%{y}</b><extra></extra>"
    ))
    if len(daily_prev) > 0:
        x_prev = daily_cur["Marca temporal"].astype(str).values[:len(daily_prev)]
        fig.add_trace(go.Scatter(
            x=x_prev, y=daily_prev["n"].values[:len(x_prev)],
            name="Período anterior",
            line=dict(color=TEAL_LIGHT, width=1.5, dash="dot", shape="spline"),
            mode="lines+markers", marker=dict(size=4, color=TEAL_LIGHT),
            hovertemplate="Anterior: <b>%{y}</b><extra></extra>"
        ))
    fig.update_layout(
        **CHART_LAYOUT, height=265,
        legend=dict(orientation="h", y=1.12, x=0, font=dict(size=10, color="#e2e8f0")),
        xaxis=dict(showgrid=False, tickangle=-30, tickfont=dict(size=10, color="#e2e8f0")),
        yaxis=dict(showgrid=True, gridcolor="rgba(226,232,240,0.08)", zeroline=False,
                   tickfont=dict(color="#e2e8f0")),
    )
    return fig

def render_pie(df_filt, mode):
    if mode == "turno":
        col  = "Turno"
        ttl  = "% Participación por Turno"
    else:
        col  = "Tipo Dia"
        ttl  = "% Participación por Día"
    data = df_filt[col].value_counts().reset_index()
    data.columns = [col, "n"]
    fig = px.pie(data, values="n", names=col,
                 color_discrete_sequence=COLOR_SEQ, hole=0.3)
    fig.update_traces(
        textposition="inside", textinfo="percent+label",
        textfont=dict(size=11, color="#e2e8f0"),
        hovertemplate="%{label}<br><b>%{value}</b> (%{percent})<extra></extra>"
    )
    fig.update_layout(**CHART_LAYOUT, height=265, showlegend=False,
                      title=dict(text=ttl, font=dict(size=13, color="#e2e8f0")))
    return fig

def render_top_horario(df_filt):
    top = df_filt["Franja"].value_counts().head(5).reset_index()
    top.columns = ["label","n"]
    top["label"] = top["label"].str.split("-", n=1).str[1]
    top = top.sort_values("n")
    fig = go.Figure(go.Bar(
        x=top["n"], y=top["label"], orientation="h",
        marker=dict(color=top["n"], colorscale=[[0, TEAL_LIGHT],[1, TEAL_DARK]],
                    showscale=False),
        text=top["n"], textposition="outside",
        textfont=dict(size=11, color="#e2e8f0"),
        hovertemplate="%{y}: <b>%{x}</b><extra></extra>"
    ))
    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text="Top 5 Novedades por Rango Horario",
                   font=dict(size=13, color="#e2e8f0", weight=700)),
        height=250,
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=11, color="#e2e8f0")),
        bargap=0.33,
    )
    return fig

def render_comisaria_turno(df_filt):
    ct = df_filt.groupby(["Comisaría","Turno"]).size().reset_index(name="n")
    fig = px.bar(ct, x="Comisaría", y="n", color="Turno",
                 color_discrete_sequence=COLOR_SEQ, barmode="stack")
    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(text="Novedades por Comisaría y Turno",
                   font=dict(size=13, color="#e2e8f0", weight=700)),
        height=265,
        xaxis=dict(showgrid=False, tickangle=-35, tickfont=dict(size=9, color="#e2e8f0")),
        yaxis=dict(showgrid=True, gridcolor="rgba(226,232,240,0.08)", zeroline=False,
                   tickfont=dict(color="#e2e8f0")),
        legend=dict(orientation="h", y=1.1, x=0, font=dict(size=10, color="#e2e8f0"),
                    title_text=""),
        bargap=0.2,
    )
    return fig

# ─── TOGGLE PIE COMPONENT ─────────────────────────────────────────────────────
def pie_toggle(key):
    """Renderiza los botones Turno / Día y devuelve el mode actual."""
    mode = st.session_state[f"pie_mode_{key}"]
    col_t, col_d, _ = st.columns([1, 1, 6])
    with col_t:
        if st.button("Turno", key=f"btn_turno_{key}",
                     type="primary" if mode == "turno" else "secondary"):
            st.session_state[f"pie_mode_{key}"] = "turno"
            st.rerun()
    with col_d:
        if st.button("Día", key=f"btn_dia_{key}",
                     type="primary" if mode == "dia" else "secondary"):
            st.session_state[f"pie_mode_{key}"] = "dia"
            st.rerun()
    return st.session_state[f"pie_mode_{key}"]

# ═══════════════════════════════════════════════════════════════════════════════
#  PÁGINA 1 – RESUMEN
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.pagina == "resumen":

    # ── HEADER ────────────────────────────────────────────────────────────────
    hcol1, hcol2, hcol3 = st.columns([2, 7, 2])
    with hcol1:
        try:
            st.image("logo_izquierda.png", width=70)
        except:
            pass
    with hcol2:
        st.markdown("""
        <div class="main-header" style="margin-bottom:0;">
            <div class="header-title">Resumen mensual novedades</div>
        </div>""", unsafe_allow_html=True)
    with hcol3:
        try:
            st.image("logo_derecha.png", width=70)
        except:
            pass

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── FILTROS ───────────────────────────────────────────────────────────────
    with st.container():
        fc1, fc2, fc3 = st.columns([3, 1.5, 2])
        with fc1:
            date_range = st.date_input(
                "Período",
                value=(max_date.replace(day=1), max_date),
                min_value=min_date, max_value=max_date, format="DD/MM/YYYY"
            )
        with fc2:
            turnos = ["Todos"] + sorted(df["Turno"].dropna().unique().tolist())
            turno_sel = st.selectbox("Turno", turnos)
        with fc3:
            buf = io.BytesIO()

    # ── PERÍODOS ──────────────────────────────────────────────────────────────
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    elif isinstance(date_range, tuple) and len(date_range) == 1:
        start_date = end_date = date_range[0]
    else:
        start_date = end_date = date_range

    period_days = (end_date - start_date).days + 1
    prev_end    = start_date - timedelta(days=1)
    prev_start  = prev_end   - timedelta(days=period_days - 1)

    def filt_resumen(frame, sd, ed):
        m = (frame["Marca temporal"].dt.date >= sd) & (frame["Marca temporal"].dt.date <= ed)
        if turno_sel != "Todos":
            m &= frame["Turno"] == turno_sel
        return frame[m].copy()

    df_cur  = filt_resumen(df, start_date, end_date)
    df_prev = filt_resumen(df, prev_start, prev_end)

    # ── KPIs + DESCARGA + NAV ─────────────────────────────────────────────────
    total_cur  = len(df_cur)
    total_prev = len(df_prev)
    d_total    = ((total_cur - total_prev) / total_prev * 100) if total_prev else 0

    cam_cur  = df_cur["Con Cámara"].mean()  * 100 if total_cur  else 0
    cam_prev = df_prev["Con Cámara"].mean() * 100 if total_prev else 0
    d_cam    = cam_cur - cam_prev

    k1, k2, k3 = st.columns([1.3, 1.3, 3])
    with k1:
        render_kpi("% Cámara", f"{cam_cur:.1f}%", d_cam,
                   f"{d_cam:+.1f}% vs Período anterior")
    with k2:
        render_kpi("Total Novedades", f"{total_cur:,}", d_total,
                   f"{d_total:+.1f}% vs Período anterior")
    with k3:
        c_dl, c_nav = st.columns([2, 1])
        with c_dl:
            buf = io.BytesIO()
            df_cur.drop(columns=["Hour","Weekday","Con Cámara"], errors="ignore").to_excel(
                buf, index=False, engine="openpyxl"
            )
            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(
                "⬇ Descargar datos filtrados", data=buf.getvalue(),
                file_name=f"novedades_{start_date}_{end_date}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with c_nav:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔍 Ver Detalle →", type="primary"):
                st.session_state.pagina = "detalle"
                st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── HEATMAP ───────────────────────────────────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Distribución por Día y Franja Horaria</div>', unsafe_allow_html=True)
    st.plotly_chart(render_heatmap(df_cur), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── LÍNEA + TORTA ─────────────────────────────────────────────────────────
    col_line, col_pie = st.columns([3, 2])

    with col_line:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Evolución de Novedades</div>', unsafe_allow_html=True)
        st.plotly_chart(render_linea(df_cur, df_prev), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_pie:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        pie_mode = pie_toggle("resumen")
        st.plotly_chart(render_pie(df_cur, pie_mode), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── TOP 5 ─────────────────────────────────────────────────────────────────
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

    # ── FOOTER ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="text-align:center; color:#64748b; font-size:0.75rem; margin-top:8px;">
        Centro de Operaciones Lomas · Datos actualizados cada 5 min ·
        Período: {start_date.strftime('%d/%m/%Y')} al {end_date.strftime('%d/%m/%Y')}
        ({period_days} días) · Período anterior: {prev_start.strftime('%d/%m/%Y')} al {prev_end.strftime('%d/%m/%Y')}
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  PÁGINA 2 – DETALLE
# ═══════════════════════════════════════════════════════════════════════════════
else:

    # ── HEADER ────────────────────────────────────────────────────────────────
    hcol1, hcol2, hcol3 = st.columns([2, 7, 2])
    with hcol1:
        try:
            st.image("logo_izquierda.png", width=70)
        except:
            pass
    with hcol2:
        st.markdown("""
        <div class="main-header" style="margin-bottom:0;">
            <div class="header-title">Detalle mensual novedades</div>
        </div>""", unsafe_allow_html=True)
    with hcol3:
        try:
            st.image("logo_derecha.png", width=70)
        except:
            pass

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── FILTROS ───────────────────────────────────────────────────────────────
    with st.container():
        fc1, fc2, fc3, fc4, fc5 = st.columns([2.5, 1.3, 1.5, 1.5, 1.3])
        with fc1:
            date_range2 = st.date_input(
                "Período",
                value=(max_date.replace(day=1), max_date),
                min_value=min_date, max_value=max_date, format="DD/MM/YYYY",
                key="dr_detalle"
            )
        with fc2:
            cats2 = ["Todas"] + sorted(df["Categoría"].dropna().unique().tolist())
            cat_sel2 = st.selectbox("Categoría", cats2, key="cat2")
        with fc3:
            if cat_sel2 != "Todas":
                subs_disponibles = df[df["Categoría"] == cat_sel2]["Subcategoria"]
                subs_disponibles = subs_disponibles[subs_disponibles.str.strip() != ""].dropna().unique().tolist()
            else:
                subs_disponibles = df["Subcategoria"][df["Subcategoria"].str.strip() != ""].dropna().unique().tolist()
            subcats2 = ["Todas"] + sorted(subs_disponibles)
            sub_sel2 = st.selectbox("Subcategoría", subcats2, key="sub2")
        with fc4:
            turnos2 = ["Todos"] + sorted(df["Turno"].dropna().unique().tolist())
            turno_sel2 = st.selectbox("Turno", turnos2, key="turno2")
        with fc5:
            comisarias2 = ["Todas"] + sorted(df["Comisaría"].dropna().unique().tolist())
            com_sel2 = st.selectbox("Comisaría", comisarias2, key="com2")

    # ── PERÍODOS ──────────────────────────────────────────────────────────────
    if isinstance(date_range2, tuple) and len(date_range2) == 2:
        start_date2, end_date2 = date_range2
    elif isinstance(date_range2, tuple) and len(date_range2) == 1:
        start_date2 = end_date2 = date_range2[0]
    else:
        start_date2 = end_date2 = date_range2

    period_days2 = (end_date2 - start_date2).days + 1
    prev_end2    = start_date2 - timedelta(days=1)
    prev_start2  = prev_end2   - timedelta(days=period_days2 - 1)

    def filt_detalle(frame, sd, ed):
        m = (frame["Marca temporal"].dt.date >= sd) & (frame["Marca temporal"].dt.date <= ed)
        if turno_sel2 != "Todos":
            m &= frame["Turno"] == turno_sel2
        if cat_sel2 != "Todas":
            m &= frame["Categoría"] == cat_sel2
        if sub_sel2 != "Todas":
            m &= frame["Subcategoria"] == sub_sel2
        if com_sel2 != "Todas":
            m &= frame["Comisaría"] == com_sel2
        return frame[m].copy()

    df_cur2  = filt_detalle(df, start_date2, end_date2)
    df_prev2 = filt_detalle(df, prev_start2, prev_end2)

    # ── KPI + NAV ─────────────────────────────────────────────────────────────
    total_cur2  = len(df_cur2)
    total_prev2 = len(df_prev2)
    d_total2    = ((total_cur2 - total_prev2) / total_prev2 * 100) if total_prev2 else 0

    k1d, k2d = st.columns([1.3, 5])
    with k1d:
        render_kpi("Total Novedades", f"{total_cur2:,}", d_total2,
                   f"{d_total2:+.1f}% vs Período anterior")
    with k2d:
        c_back, c_dl2, _ = st.columns([1, 2, 4])
        with c_back:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("← Volver", type="secondary"):
                st.session_state.pagina = "resumen"
                st.rerun()
        with c_dl2:
            buf2 = io.BytesIO()
            df_cur2.drop(columns=["Hour","Weekday","Con Cámara"], errors="ignore").to_excel(
                buf2, index=False, engine="openpyxl"
            )
            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(
                "⬇ Descargar datos filtrados", data=buf2.getvalue(),
                file_name=f"novedades_detalle_{start_date2}_{end_date2}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_detalle"
            )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── HEATMAP ───────────────────────────────────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Distribución por Día y Franja Horaria</div>', unsafe_allow_html=True)
    st.plotly_chart(render_heatmap(df_cur2), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── LÍNEA + TOP HORARIO ───────────────────────────────────────────────────
    col_line2, col_top2 = st.columns([3, 2])

    with col_line2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Evolución de Novedades</div>', unsafe_allow_html=True)
        st.plotly_chart(render_linea(df_cur2, df_prev2), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_top2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Top 5 por Rango Horario</div>', unsafe_allow_html=True)
        st.plotly_chart(render_top_horario(df_cur2), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── TORTA + COMISARÍA x TURNO ─────────────────────────────────────────────
    col_pie2, col_bar2 = st.columns([2, 3])

    with col_pie2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        pie_mode2 = pie_toggle("detalle")
        st.plotly_chart(render_pie(df_cur2, pie_mode2), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_bar2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.plotly_chart(render_comisaria_turno(df_cur2), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── FOOTER ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="text-align:center; color:#64748b; font-size:0.75rem; margin-top:8px;">
        Centro de Operaciones Lomas · Datos actualizados cada 5 min ·
        Período: {start_date2.strftime('%d/%m/%Y')} al {end_date2.strftime('%d/%m/%Y')}
        ({period_days2} días) · Período anterior: {prev_start2.strftime('%d/%m/%Y')} al {prev_end2.strftime('%d/%m/%Y')}
    </div>
    """, unsafe_allow_html=True)
