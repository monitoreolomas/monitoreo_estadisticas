import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import timedelta, date
import math, io, os

st.set_page_config(
    page_title="COL · Análisis Operativo",
    page_icon="🔵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── SESSION ────────────────────────────────────────────────────────────────────
for k, v in [("vista","ejecutiva"), ("pie_mode","turno")]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── PALETA ─────────────────────────────────────────────────────────────────────
BG      = "#0a0a12"
BG2     = "#111120"
CARD    = "#16162a"
BORDER  = "rgba(139,92,246,0.22)"
ACCENT  = "#8b5cf6"
ACCENT2 = "#6d28d9"
GREEN   = "#10b981"
AMBER   = "#f59e0b"
RED     = "#ef4444"
MUTED   = "#64748b"
TEXT    = "#e2e8f0"
TEXT2   = "#94a3b8"
SEQ_DIV = [GREEN, ACCENT, AMBER, RED, "#38bdf8", "#f472b6", "#a3e635"]

CHART = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=12, color=TEXT),
    margin=dict(l=10, r=10, t=36, b=10),
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{{font-family:'Inter',sans-serif;background:{BG};color:{TEXT};font-size:14px;}}
#MainMenu,footer,header{{visibility:hidden;}}
.block-container{{padding:.8rem 1.4rem 1.4rem;max-width:100%;background:{BG};}}

.topbar{{
    display:flex;align-items:center;gap:18px;
    background:linear-gradient(90deg,{BG2} 0%,#1a1535 50%,{BG2} 100%);
    border:1px solid {BORDER};border-radius:16px;
    padding:14px 24px;margin-bottom:14px;
    box-shadow:0 4px 24px rgba(0,0,0,0.5);
}}
.topbar-title{{font-size:1.3rem;font-weight:800;color:{TEXT};letter-spacing:-.3px;}}
.topbar-sub{{font-size:.8rem;color:{TEXT2};margin-top:2px;}}
.topbar-live{{
    display:inline-flex;align-items:center;gap:6px;margin-left:auto;
    background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3);
    border-radius:100px;padding:4px 12px;
    font-size:.72rem;font-weight:600;color:#6ee7b7;letter-spacing:.06em;
}}
.live-dot{{
    width:6px;height:6px;border-radius:50%;background:{GREEN};
    box-shadow:0 0 6px {GREEN};
    animation:pulse 2s infinite;
}}
@keyframes pulse{{0%,100%{{opacity:1;box-shadow:0 0 6px {GREEN};}}50%{{opacity:.5;box-shadow:0 0 12px {GREEN};}}}}

.kpi{{
    background:{CARD};border:1px solid {BORDER};border-radius:18px;
    padding:16px 18px;position:relative;overflow:hidden;
}}
.kpi::before{{
    content:'';position:absolute;top:0;left:0;right:0;height:3px;
    background:linear-gradient(90deg,{ACCENT},{ACCENT2});border-radius:18px 18px 0 0;
}}
.kpi-icon{{font-size:1.4rem;margin-bottom:4px;line-height:1;}}
.kpi-label{{font-size:.72rem;color:{TEXT2};font-weight:600;letter-spacing:.07em;text-transform:uppercase;}}
.kpi-val{{font-size:1.9rem;font-weight:800;color:{TEXT};line-height:1.1;margin:3px 0;}}
.kpi-d-pos{{font-size:.73rem;color:{GREEN};font-weight:600;}}
.kpi-d-neg{{font-size:.73rem;color:{RED};font-weight:600;}}
.kpi-d-neu{{font-size:.73rem;color:{MUTED};font-weight:600;}}
.kpi-sub{{font-size:.7rem;color:{MUTED};margin-top:2px;}}

.card{{
    background:{CARD};border:1px solid rgba(139,92,246,0.14);
    border-radius:18px;padding:16px 18px 14px;margin-bottom:14px;
    box-shadow:0 4px 20px rgba(0,0,0,0.3);
}}
.card-title{{
    font-size:.8rem;font-weight:700;color:{TEXT};
    letter-spacing:.04em;text-transform:uppercase;
    border-bottom:1px solid rgba(139,92,246,0.15);
    padding-bottom:7px;margin-bottom:10px;
    display:flex;align-items:center;gap:7px;
}}

.alert{{background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:12px;padding:9px 14px;font-size:.83rem;color:#fca5a5;margin-bottom:10px;}}
.alert-ok{{background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.25);border-radius:12px;padding:9px 14px;font-size:.83rem;color:#6ee7b7;margin-bottom:10px;}}

/* Nav tabs styled */
.stButton>button{{border-radius:12px!important;font-weight:600!important;font-size:.82rem!important;padding:7px 14px!important;transition:all .15s!important;}}
.stDownloadButton button{{background:{ACCENT}!important;color:#fff!important;border:none!important;border-radius:12px!important;font-weight:700!important;font-size:.82rem!important;padding:8px 14px!important;}}
.stDownloadButton button:hover{{background:{GREEN}!important;}}
.js-plotly-plot .plotly .modebar{{display:none!important;}}
hr{{border-color:rgba(139,92,246,0.12);margin:10px 0;}}
label{{font-size:.82rem!important;color:{TEXT2}!important;font-weight:500!important;}}

/* Expander styling */
[data-testid="stExpander"]{{
    background:{CARD}!important;
    border:1px solid rgba(139,92,246,0.2)!important;
    border-radius:14px!important;
    margin-bottom:12px!important;
}}
[data-testid="stExpander"] summary{{color:{TEXT2}!important;font-weight:600!important;font-size:.85rem!important;}}
</style>
""", unsafe_allow_html=True)

# ── DATA ───────────────────────────────────────────────────────────────────────
CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vRBFU12b6jgWRdNJbj5yKqKJ0iucps7HFJlkmKyjNi2DeccbtnnBM4aQEEbxKOAgKL78DUZJwFIJauX"
    "/pub?gid=2079582736&single=true&output=csv"
)

EXCEL_EPOCH = pd.Timestamp("1899-12-30")

@st.cache_data(ttl=300)
def load():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        "Categoria":          "Categoría",
        "Comisaria":          "Comisaría",
        "Camara del Evento":  "Cámara",
    })

    # ── Marca temporal: puede ser string "dd/mm/yyyy HH:MM:SS" o serial numérico
    def parse_ts(val):
        if pd.isna(val): return pd.NaT
        try:
            return pd.to_datetime(str(val), format="%d/%m/%Y %H:%M:%S")
        except Exception:
            pass
        try:
            return EXCEL_EPOCH + pd.to_timedelta(float(val), unit="D")
        except Exception:
            return pd.NaT

    df["ts"]      = df["Marca temporal"].apply(parse_ts)
    df            = df.dropna(subset=["ts"])
    df["hora"]    = df["ts"].dt.hour
    df["weekday"] = df["ts"].dt.dayofweek
    df["fecha"]   = df["ts"].dt.date
    df["mes"]     = df["ts"].dt.to_period("M").astype(str)

    def turno(h, wd):
        if wd < 5:
            if 6  <= h < 14: return "Mañana"
            if 14 <= h < 22: return "Tarde"
            return "Noche"
        return "Mañana" if 6 <= h < 18 else "Noche"

    df["Turno"]   = df.apply(lambda r: turno(r["hora"], r["weekday"]), axis=1)
    df["DiaNom"]  = df["weekday"].map({0:"Lun",1:"Mar",2:"Mié",3:"Jue",4:"Vie",5:"Sáb",6:"Dom"})
    df["TipoDia"] = df["weekday"].apply(lambda x: "Semana" if x < 5 else "Fin de semana")
    df["Franja"]  = df["hora"].apply(
        lambda h: ["00-03","03-06","06-09","09-12","12-15","15-18","18-21","21-00"][min(h//3,7)]
    )

    # Subcategoría unificada
    if "Subcategoria" not in df.columns:
        sc = [c for c in df.columns if c.startswith("Subcategoria ")]
        df["Subcategoria"] = df[sc].replace("", pd.NA).bfill(axis=1).iloc[:,0].fillna("")
    df["Subcategoria"] = df["Subcategoria"].fillna("").str.strip()
    df["CGM"]          = df["CGM"].fillna("Sin CGM").str.strip()
    df["con_camara"]   = df["¿Se ve por cámara?"].str.upper().str.strip() == "SI"

    riesgo_map = {
        "Robo":3,"Hurto":2,"Heridos":5,"Obito":5,"Violencia":4,
        "Persecución":3,"Accidente de tránsito":2,"Conflicto":2,"Incendios":3,"Otros":1
    }
    df["riesgo"] = df["Categoría"].map(riesgo_map).fillna(1)
    return df

with st.spinner(""):
    try:
        df = load()
    except Exception as e:
        st.error(f"Error cargando datos: {e}"); st.stop()

min_d = df["fecha"].min()
max_d = df["fecha"].max()
cgms_lista  = sorted(df["CGM"].dropna().unique().tolist())
cats_lista  = sorted(df["Categoría"].dropna().unique().tolist())
coms_lista  = sorted(df["Comisaría"].dropna().unique().tolist())

# ── HELPERS ────────────────────────────────────────────────────────────────────
def kpi_card(icon, label, val, delta=None, sub="", invert=False):
    if delta is None:
        delta_html = f"<div class='kpi-d-neu'>{sub}</div>" if sub else ""
        sub_html   = ""
    else:
        if delta > 0:
            cls, arr = ("kpi-d-neg","▲") if invert else ("kpi-d-pos","▲")
        elif delta < 0:
            cls, arr = ("kpi-d-pos","▼") if invert else ("kpi-d-neg","▼")
        else:
            cls, arr = "kpi-d-neu","●"
        delta_html = f"<div class='{cls}'>{arr} {abs(delta):.1f}% vs período ant.</div>"
        sub_html   = f"<div class='kpi-sub'>{sub}</div>" if sub else ""
    st.markdown(f"""
    <div class="kpi">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-val">{val}</div>
        {delta_html}{sub_html}
    </div>""", unsafe_allow_html=True)

def card(title, icon=""):
    st.markdown(f'<div class="card"><div class="card-title"><span>{icon}</span>{title}</div>', unsafe_allow_html=True)

def end_card():
    st.markdown('</div>', unsafe_allow_html=True)

def pie_donut(df_filt, mode):
    col_p  = "Turno" if mode == "turno" else "TipoDia"
    pdata  = df_filt[col_p].value_counts().reset_index()
    pdata.columns = [col_p, "n"]
    colors = [ACCENT, GREEN, AMBER, RED, "#38bdf8"]
    total  = pdata["n"].sum()
    fig = go.Figure(go.Pie(
        labels=pdata[col_p], values=pdata["n"], hole=0.55,
        marker=dict(colors=colors[:len(pdata)], line=dict(color=BG, width=3)),
        textinfo="none", sort=True, direction="clockwise",
        hovertemplate="%{label}<br><b>%{value}</b> (%{percent})<extra></extra>",
    ))
    ann, ang = [], 90.0
    for _, row in pdata.iterrows():
        p  = row["n"] / total
        sw = p * 360
        ma = math.radians(ang - sw / 2)
        ann.append(dict(
            text=f"<b>{row[col_p]}</b><br>{p*100:.0f}%",
            x=0.5+0.65*0.5*math.cos(ma), y=0.5+0.65*0.5*math.sin(ma),
            xref="paper", yref="paper", showarrow=False,
            font=dict(size=9, color="#fff"),
            bgcolor="rgba(20,20,40,0.82)",
            bordercolor="rgba(255,255,255,0.1)",
            borderpad=4, borderwidth=1, align="center",
        ))
        ang -= sw
    ann.append(dict(
        text=f"<b>{total:,}</b><br><span style='font-size:9px'>Total</span>",
        x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
        font=dict(size=13, color=TEXT), align="center",
    ))
    lyt = {**CHART}
    lyt["margin"] = dict(l=10, r=10, t=10, b=28)
    fig.update_layout(**lyt, height=280, annotations=ann, showlegend=True,
        legend=dict(orientation="h", x=0.5, y=-0.04, xanchor="center",
                    font=dict(size=9, color=TEXT2), bgcolor="rgba(0,0,0,0)"))
    return fig

# ── TOPBAR ─────────────────────────────────────────────────────────────────────
cl, cm, cr = st.columns([1, 8, 1])
with cl:
    if os.path.exists("logo_izquierda.png"): st.image("logo_izquierda.png", width=58)
with cm:
    st.markdown("""
    <div class="topbar">
        <div>
            <div class="topbar-title">Centro de Operaciones Lomas &nbsp;·&nbsp; Análisis Operativo</div>
            <div class="topbar-sub">Reporte interactivo &nbsp;·&nbsp; Sistema de monitoreo del Partido de Lomas de Zamora</div>
        </div>
        <div class="topbar-live"><span class="live-dot"></span>EN VIVO</div>
    </div>""", unsafe_allow_html=True)
with cr:
    if os.path.exists("logo_derecha.png"): st.image("logo_derecha.png", width=58)

# ── FILTROS ─────────────────────────────────────────────────────────────────────
with st.expander("⚙️  Filtros", expanded=True):
    f1, f2, f3, f4, f5, f6 = st.columns([2.4, 1.4, 1.6, 1.4, 1.4, 1.2])
    with f1:
        rango = st.date_input("Período", value=(max_d.replace(day=1), max_d),
                              min_value=min_d, max_value=max_d, format="DD/MM/YYYY")
    with f2:
        cgms_sel = st.multiselect("CGM", cgms_lista, default=[], placeholder="Todos")
    with f3:
        cats_sel = st.multiselect("Categoría", cats_lista, default=[], placeholder="Todas")
    with f4:
        subs_disp = df["Subcategoria"] if not cats_sel else df[df["Categoría"].isin(cats_sel)]["Subcategoria"]
        subs_lista = sorted(subs_disp[subs_disp.str.strip()!=""].dropna().unique().tolist())
        subs_sel = st.multiselect("Subcategoría", subs_lista, default=[], placeholder="Todas")
    with f5:
        coms_sel = st.multiselect("Comisaría", coms_lista, default=[], placeholder="Todas")
    with f6:
        turnos_sel = st.multiselect("Turno", ["Mañana","Tarde","Noche"], default=[], placeholder="Todos")

# ── FILTRADO ───────────────────────────────────────────────────────────────────
if isinstance(rango, tuple) and len(rango) == 2:   sd, ed = rango
elif isinstance(rango, tuple) and len(rango) == 1: sd = ed = rango[0]
else:                                               sd = ed = rango

days    = (ed - sd).days + 1
prev_ed = sd - timedelta(days=1)
prev_sd = prev_ed - timedelta(days=days - 1)

def filtrar(frame, d0, d1):
    m = (frame["fecha"] >= d0) & (frame["fecha"] <= d1)
    if cgms_sel:   m &= frame["CGM"].isin(cgms_sel)
    if cats_sel:   m &= frame["Categoría"].isin(cats_sel)
    if subs_sel:   m &= frame["Subcategoria"].isin(subs_sel)
    if coms_sel:   m &= frame["Comisaría"].isin(coms_sel)
    if turnos_sel: m &= frame["Turno"].isin(turnos_sel)
    return frame[m].copy()

dfc = filtrar(df, sd, ed)
dfp = filtrar(df, prev_sd, prev_ed)

n_cur  = len(dfc); n_prev = len(dfp)
d_pct  = ((n_cur - n_prev) / n_prev * 100) if n_prev else 0
cam_pct  = dfc["con_camara"].mean()*100 if n_cur else 0
cam_prev = dfp["con_camara"].mean()*100 if len(dfp) else 0
d_cam    = cam_pct - cam_prev
riesgo_med  = dfc["riesgo"].mean() if n_cur else 0
riesgo_prev = dfp["riesgo"].mean() if len(dfp) else 0
d_riesgo    = riesgo_med - riesgo_prev
hora_pico = dfc["hora"].mode()[0] if n_cur else 0
cat_top   = dfc["Categoría"].value_counts().index[0] if n_cur else "—"
cat_top_n = dfc["Categoría"].value_counts().iloc[0]  if n_cur else 0
cgm_top   = dfc["CGM"].value_counts().index[0] if n_cur else "—"

# ── ALERTA ─────────────────────────────────────────────────────────────────────
if n_cur > 0:
    if d_pct > 20:
        st.markdown(f'<div class="alert">🚨 <b>Alerta:</b> Novedades <b>+{d_pct:.1f}%</b> vs período anterior · Categoría líder: <b>{cat_top}</b> ({cat_top_n}) · CGM más activo: <b>{cgm_top}</b></div>', unsafe_allow_html=True)
    elif d_pct < -20:
        st.markdown(f'<div class="alert-ok">✅ <b>Tendencia positiva:</b> Novedades <b>{d_pct:.1f}%</b> vs período anterior</div>', unsafe_allow_html=True)

# ── NAV + EXPORT ───────────────────────────────────────────────────────────────
n1, n2, n3, sp, dl = st.columns([1.1, 1.2, 1.2, 4.5, 1.4])
with n1:
    if st.button("📊 Ejecutivo", type="primary" if st.session_state.vista=="ejecutiva" else "secondary", use_container_width=True):
        st.session_state.vista = "ejecutiva"; st.rerun()
with n2:
    if st.button("🗺️ Territorial", type="primary" if st.session_state.vista=="territorial" else "secondary", use_container_width=True):
        st.session_state.vista = "territorial"; st.rerun()
with n3:
    if st.button("📡 Por CGM", type="primary" if st.session_state.vista=="cgm" else "secondary", use_container_width=True):
        st.session_state.vista = "cgm"; st.rerun()
with dl:
    buf = io.BytesIO()
    dfc.drop(columns=["hora","weekday","riesgo","con_camara"], errors="ignore").to_excel(buf, index=False, engine="openpyxl")
    st.download_button("⬇ Exportar", data=buf.getvalue(),
        file_name=f"col_{sd}_{ed}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  VISTA EJECUTIVA
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.vista == "ejecutiva":

    # KPIs fila 1
    k1,k2,k3,k4,k5,k6 = st.columns(6)
    with k1: kpi_card("📋","Total Novedades",   f"{n_cur:,}",          delta=d_pct,     invert=True)
    with k2: kpi_card("📷","Con Cámara",        f"{cam_pct:.1f}%",     delta=d_cam,     sub=f"{int(dfc['con_camara'].sum())} eventos")
    with k3: kpi_card("⚠️","Índice de Riesgo",  f"{riesgo_med:.2f}",   delta=d_riesgo,  sub="Escala 1–5", invert=True)
    with k4: kpi_card("🏘️","CGM más activo",    cgm_top,               delta=None,      sub=f"{dfc['CGM'].value_counts().iloc[0]} casos" if n_cur else "")
    with k5: kpi_card("🕐","Hora Pico",         f"{hora_pico:02d}:00", delta=None,      sub=f"Franja {hora_pico//3*3:02d}–{hora_pico//3*3+3:02d}hs")
    with k6: kpi_card("🔺","Cat. Líder",        cat_top,               delta=None,      sub=f"{cat_top_n} casos")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # Fila 1: Evolución + Heatmap día×turno
    col_ev, col_hm = st.columns([3, 2])

    with col_ev:
        card("Evolución Diaria","📈")
        daily_c = dfc.groupby("fecha").size().reset_index(name="n")
        daily_p = dfp.groupby("fecha").size().reset_index(name="n")
        fig = go.Figure()
        if len(daily_p):
            fig.add_trace(go.Scatter(
                x=daily_c["fecha"].astype(str).values[:len(daily_p)],
                y=daily_p["n"].values[:len(daily_c)], name="Anterior",
                fill="tozeroy", fillcolor="rgba(100,116,139,0.1)",
                line=dict(color="rgba(100,116,139,0.35)", width=1, dash="dot"),
                mode="lines", hovertemplate="Anterior: <b>%{y}</b><extra></extra>"
            ))
        fig.add_trace(go.Scatter(
            x=daily_c["fecha"].astype(str), y=daily_c["n"], name="Actual",
            fill="tozeroy", fillcolor="rgba(139,92,246,0.15)",
            line=dict(color=ACCENT, width=2.5, shape="spline"),
            mode="lines+markers", marker=dict(size=5, color=ACCENT, line=dict(color=BG2, width=1.5)),
            hovertemplate="%{x}<br><b>%{y} novedades</b><extra></extra>"
        ))
        if len(daily_c) >= 7:
            daily_c["mm7"] = daily_c["n"].rolling(7, min_periods=1).mean()
            fig.add_trace(go.Scatter(
                x=daily_c["fecha"].astype(str), y=daily_c["mm7"].round(1), name="Media 7d",
                line=dict(color=AMBER, width=1.8, dash="dash"), mode="lines",
                hovertemplate="Media 7d: <b>%{y:.1f}</b><extra></extra>"
            ))
        fig.update_layout(**CHART, height=265,
            legend=dict(orientation="h", y=1.1, x=0, font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
            xaxis=dict(showgrid=False, tickangle=-30, tickfont=dict(size=9)),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=False))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        end_card()

    with col_hm:
        card("Intensidad Día × Turno","🌡️")
        dias_ord = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
        turn_ord = ["Mañana","Tarde","Noche"]
        hm  = dfc.groupby(["DiaNom","Turno"]).size().reset_index(name="n")
        piv = hm.pivot(index="DiaNom", columns="Turno", values="n").fillna(0)
        piv = piv.reindex(index=[d for d in dias_ord if d in piv.index],
                          columns=[t for t in turn_ord if t in piv.columns])
        fig2 = go.Figure(go.Heatmap(
            z=piv.values, x=list(piv.columns), y=list(piv.index),
            colorscale=[[0,BG2],[0.4,"#4c1d95"],[1,ACCENT]],
            showscale=True, colorbar=dict(thickness=8, len=0.8, tickfont=dict(size=9,color=TEXT2)),
            hovertemplate="<b>%{y} · %{x}</b><br>%{z:.0f} novedades<extra></extra>",
            texttemplate="%{z:.0f}", textfont=dict(size=11, color=TEXT)
        ))
        fig2.update_layout(**CHART, height=265,
            xaxis=dict(showgrid=False, side="top"),
            yaxis=dict(showgrid=False, autorange="reversed"))
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
        end_card()

    # Fila 2: Barras categoría + Donut + Ranking comisarías
    col_cat, col_don, col_rank = st.columns([2.4, 1.6, 2])

    with col_cat:
        card("Novedades por Categoría  ·  color = nivel de riesgo","📂")
        cat_df = dfc["Categoría"].value_counts().reset_index()
        cat_df.columns = ["cat","n"]
        cat_df["pct"]    = cat_df["n"] / cat_df["n"].sum() * 100
        risk_map = {"Robo":3,"Hurto":2,"Heridos":5,"Obito":5,"Violencia":4,
                    "Persecución":3,"Accidente de tránsito":2,"Conflicto":2,"Incendios":3,"Otros":1}
        cat_df["riesgo"] = cat_df["cat"].map(risk_map).fillna(1)
        cat_df = cat_df.sort_values("n", ascending=True)
        bar_colors = [RED if r>=4 else AMBER if r==3 else ACCENT for r in cat_df["riesgo"]]
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=cat_df["n"], y=cat_df["cat"], orientation="h",
            marker=dict(color=bar_colors, line=dict(color="rgba(0,0,0,0)",width=0)),
            text=[f"{n}  ({p:.0f}%)" for n,p in zip(cat_df["n"],cat_df["pct"])],
            textposition="outside", textfont=dict(size=10, color=TEXT2),
            hovertemplate="<b>%{y}</b><br>%{x} novedades<extra></extra>",
            width=0.65, showlegend=False,
        ))
        for color, label in [(RED,"Alto"),(AMBER,"Medio"),(ACCENT,"Bajo")]:
            fig3.add_trace(go.Bar(x=[None], y=[None], marker_color=color, name=label, showlegend=True))
        fig3.update_layout(**CHART, height=305, bargap=0.3, barmode="overlay",
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, tickfont=dict(size=10)),
            legend=dict(orientation="h", y=-0.08, x=0, font=dict(size=9),
                        title=dict(text="Riesgo  ", font=dict(size=9,color=TEXT2)),
                        bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":False})
        end_card()

    with col_don:
        card("Participación Turno / Día","🌙")
        mode = st.session_state["pie_mode"]
        tc, dc = st.columns(2)
        with tc:
            if st.button("Turno", key="pt", type="primary" if mode=="turno" else "secondary", use_container_width=True):
                st.session_state["pie_mode"] = "turno"; st.rerun()
        with dc:
            if st.button("Día", key="pd", type="primary" if mode=="dia" else "secondary", use_container_width=True):
                st.session_state["pie_mode"] = "dia"; st.rerun()
        st.plotly_chart(pie_donut(dfc, mode), use_container_width=True, config={"displayModeBar":False})
        end_card()

    with col_rank:
        card("Ranking Comisarías","🏆")
        com_df = dfc["Comisaría"].value_counts().reset_index()
        com_df.columns = ["com","n"]
        com_df["rank"] = range(1, len(com_df)+1)
        com_df = com_df.head(10).sort_values("n", ascending=True)
        bar_c  = [RED if r==1 else AMBER if r==2 else ACCENT if r==3 else "#4c1d95"
                  for r in com_df["rank"].iloc[::-1]][::-1]
        fig5 = go.Figure(go.Bar(
            x=com_df["n"], y=com_df["com"], orientation="h",
            marker=dict(color=bar_c, line=dict(color="rgba(0,0,0,0)",width=0)),
            text=com_df["n"], textposition="outside",
            textfont=dict(size=10, color=TEXT2),
            hovertemplate="<b>%{y}</b><br>%{x} novedades<extra></extra>",
            width=0.65,
        ))
        fig5.update_layout(**CHART, height=305, bargap=0.28,
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, tickfont=dict(size=10)))
        st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar":False})
        end_card()


# ══════════════════════════════════════════════════════════════════════════════
#  VISTA TERRITORIAL
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.vista == "territorial":

    com_top  = dfc["Comisaría"].value_counts()
    n_coms   = dfc["Comisaría"].nunique()
    prom_com = n_cur / n_coms if n_coms else 0
    cat_cam  = dfc[dfc["con_camara"]]["Categoría"].value_counts().index[0] if dfc["con_camara"].sum() else "—"
    cam_n    = dfc[dfc["con_camara"]]["Categoría"].value_counts().iloc[0]  if dfc["con_camara"].sum() else 0

    k1,k2,k3,k4 = st.columns(4)
    with k1: kpi_card("🏢","Comisarías activas", str(n_coms),                          delta=None)
    with k2: kpi_card("📍","Comisaría líder",    com_top.index[0] if n_cur else "—",   delta=None, sub=f"{com_top.iloc[0]} casos" if n_cur else "")
    with k3: kpi_card("📊","Promedio / Comisaría", f"{prom_com:.0f}",                  delta=None, sub="novedades")
    with k4: kpi_card("📷","Cat. más filmada",   cat_cam,                               delta=None, sub=f"{cam_n} con cámara")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    col_a, col_b = st.columns([3, 2])

    with col_a:
        card("Comisaría × Categoría (Top 5 categorías)","🗂️")
        ct    = dfc.groupby(["Comisaría","Categoría"]).size().reset_index(name="n")
        top5c = dfc["Categoría"].value_counts().head(5).index.tolist()
        ct    = ct[ct["Categoría"].isin(top5c)]
        fig6 = px.bar(ct, x="Comisaría", y="n", color="Categoría",
                      color_discrete_sequence=SEQ_DIV, barmode="stack")
        fig6.update_layout(**CHART, height=305,
            xaxis=dict(showgrid=False, tickangle=-40, tickfont=dict(size=9), title=None),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=False, title=None),
            legend=dict(orientation="h", y=1.12, x=0, font=dict(size=9), title_text="", bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar":False})
        end_card()

    with col_b:
        card("% Cobertura de Cámara por Comisaría","🎥")
        cam_c = dfc.groupby("Comisaría")["con_camara"].agg(["sum","count"]).reset_index()
        cam_c.columns = ["Comisaría","con_cam","total"]
        cam_c["pct"] = cam_c["con_cam"] / cam_c["total"] * 100
        cam_c = cam_c.sort_values("pct", ascending=True).tail(12)
        fig7 = go.Figure(go.Bar(
            x=cam_c["pct"], y=cam_c["Comisaría"], orientation="h",
            marker=dict(color=cam_c["pct"],
                        colorscale=[[0,"#1e1b4b"],[0.5,ACCENT],[1,GREEN]],
                        showscale=False, line=dict(color="rgba(0,0,0,0)",width=0)),
            text=[f"{p:.0f}%" for p in cam_c["pct"]],
            textposition="outside", textfont=dict(size=10, color=TEXT2),
            hovertemplate="<b>%{y}</b><br>%{x:.1f}% cámara<extra></extra>",
            width=0.65,
        ))
        fig7.update_layout(**CHART, height=305, bargap=0.28,
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[0,115]),
            yaxis=dict(showgrid=False, tickfont=dict(size=10)))
        st.plotly_chart(fig7, use_container_width=True, config={"displayModeBar":False})
        end_card()

    card("Mapa de Calor  ·  Comisaría × Día de Semana","🌐")
    dias_ord = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
    mat  = dfc.groupby(["Comisaría","DiaNom"]).size().reset_index(name="n")
    piv2 = mat.pivot(index="Comisaría", columns="DiaNom", values="n").fillna(0)
    piv2 = piv2.reindex(columns=[d for d in dias_ord if d in piv2.columns])
    fig8 = go.Figure(go.Heatmap(
        z=piv2.values, x=list(piv2.columns), y=list(piv2.index),
        colorscale=[[0,BG2],[0.5,"#4c1d95"],[1,ACCENT]],
        showscale=True, colorbar=dict(thickness=8, tickfont=dict(size=9,color=TEXT2)),
        hovertemplate="<b>%{y}</b> · <b>%{x}</b><br>%{z:.0f} novedades<extra></extra>",
        texttemplate="%{z:.0f}", textfont=dict(size=9, color=TEXT)
    ))
    fig8.update_layout(**CHART, height=360,
        xaxis=dict(showgrid=False, side="top"),
        yaxis=dict(showgrid=False))
    st.plotly_chart(fig8, use_container_width=True, config={"displayModeBar":False})
    end_card()


# ══════════════════════════════════════════════════════════════════════════════
#  VISTA POR CGM
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.vista == "cgm":

    n_cgms     = dfc["CGM"].nunique()
    cgm_lider  = dfc["CGM"].value_counts().index[0] if n_cur else "—"
    cgm_n_lid  = dfc["CGM"].value_counts().iloc[0]  if n_cur else 0
    prom_cgm   = n_cur / n_cgms if n_cgms else 0
    # CGM con mayor riesgo promedio
    cgm_riesgo = dfc.groupby("CGM")["riesgo"].mean().idxmax() if n_cur else "—"
    cgm_risk_v = dfc.groupby("CGM")["riesgo"].mean().max()    if n_cur else 0

    k1,k2,k3,k4 = st.columns(4)
    with k1: kpi_card("🏘️","CGMs activos",     str(n_cgms),   delta=None)
    with k2: kpi_card("🔝","CGM líder",         cgm_lider,     delta=None, sub=f"{cgm_n_lid} novedades")
    with k3: kpi_card("📊","Promedio / CGM",    f"{prom_cgm:.0f}", delta=None, sub="novedades")
    with k4: kpi_card("⚠️","CGM mayor riesgo",  cgm_riesgo,    delta=None, sub=f"Índice {cgm_risk_v:.2f}")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # Fila 1: Barras CGM + Heatmap CGM×Turno
    col_c1, col_c2 = st.columns([3, 2])

    with col_c1:
        card("Novedades Totales por CGM","🏘️")
        cgm_df = dfc["CGM"].value_counts().reset_index()
        cgm_df.columns = ["cgm","n"]
        cgm_df["pct"] = cgm_df["n"] / cgm_df["n"].sum() * 100
        cgm_df = cgm_df.sort_values("n", ascending=True)
        # Color degradado por volumen
        fig_c1 = go.Figure(go.Bar(
            x=cgm_df["n"], y=cgm_df["cgm"], orientation="h",
            marker=dict(
                color=cgm_df["n"],
                colorscale=[[0,"#2e1065"],[0.5,ACCENT],[1,"#a78bfa"]],
                showscale=False, line=dict(color="rgba(0,0,0,0)",width=0)
            ),
            text=[f"{n}  ({p:.0f}%)" for n,p in zip(cgm_df["n"],cgm_df["pct"])],
            textposition="outside", textfont=dict(size=10, color=TEXT2),
            hovertemplate="<b>%{y}</b><br>%{x} novedades<extra></extra>",
            width=0.65,
        ))
        fig_c1.update_layout(**CHART, height=360, bargap=0.25,
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, tickfont=dict(size=10)))
        st.plotly_chart(fig_c1, use_container_width=True, config={"displayModeBar":False})
        end_card()

    with col_c2:
        card("Intensidad CGM × Turno","🌡️")
        turn_ord = ["Mañana","Tarde","Noche"]
        hm_c = dfc.groupby(["CGM","Turno"]).size().reset_index(name="n")
        piv_c = hm_c.pivot(index="CGM", columns="Turno", values="n").fillna(0)
        piv_c = piv_c.reindex(columns=[t for t in turn_ord if t in piv_c.columns])
        # Ordenar por total descendente
        piv_c = piv_c.loc[piv_c.sum(axis=1).sort_values(ascending=True).index]
        fig_c2 = go.Figure(go.Heatmap(
            z=piv_c.values, x=list(piv_c.columns), y=list(piv_c.index),
            colorscale=[[0,BG2],[0.4,"#4c1d95"],[1,ACCENT]],
            showscale=True, colorbar=dict(thickness=8, tickfont=dict(size=9,color=TEXT2)),
            hovertemplate="<b>%{y}</b> · %{x}<br>%{z:.0f} novedades<extra></extra>",
            texttemplate="%{z:.0f}", textfont=dict(size=10, color=TEXT)
        ))
        fig_c2.update_layout(**CHART, height=360,
            xaxis=dict(showgrid=False, side="top"),
            yaxis=dict(showgrid=False))
        st.plotly_chart(fig_c2, use_container_width=True, config={"displayModeBar":False})
        end_card()

    # Fila 2: CGM × Categoría stacked + Índice de riesgo por CGM
    col_c3, col_c4 = st.columns([3, 2])

    with col_c3:
        card("Distribución de Categorías por CGM","📂")
        top5c = dfc["Categoría"].value_counts().head(5).index.tolist()
        cgm_cat = dfc[dfc["Categoría"].isin(top5c)].groupby(["CGM","Categoría"]).size().reset_index(name="n")
        # Ordenar CGMs por total
        order_cgm = dfc["CGM"].value_counts().index.tolist()
        cgm_cat["CGM"] = pd.Categorical(cgm_cat["CGM"], categories=order_cgm, ordered=True)
        fig_c3 = px.bar(cgm_cat, x="CGM", y="n", color="Categoría",
                        color_discrete_sequence=SEQ_DIV, barmode="stack")
        fig_c3.update_layout(**CHART, height=300,
            xaxis=dict(showgrid=False, tickangle=-35, tickfont=dict(size=9), title=None),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=False, title=None),
            legend=dict(orientation="h", y=1.12, x=0, font=dict(size=9), title_text="", bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig_c3, use_container_width=True, config={"displayModeBar":False})
        end_card()

    with col_c4:
        card("Índice de Riesgo Promedio por CGM","⚠️")
        risk_cgm = dfc.groupby("CGM")["riesgo"].mean().reset_index()
        risk_cgm.columns = ["cgm","r"]
        risk_cgm = risk_cgm.sort_values("r", ascending=True)
        # Color: verde→amarillo→rojo según riesgo
        fig_c4 = go.Figure(go.Bar(
            x=risk_cgm["r"], y=risk_cgm["cgm"], orientation="h",
            marker=dict(
                color=risk_cgm["r"],
                colorscale=[[0,GREEN],[0.5,AMBER],[1,RED]],
                showscale=True,
                colorbar=dict(thickness=8, tickfont=dict(size=9,color=TEXT2),
                              tickvals=[1,2,3,4,5], ticktext=["1","2","3","4","5"]),
                line=dict(color="rgba(0,0,0,0)",width=0)
            ),
            text=[f"{r:.2f}" for r in risk_cgm["r"]],
            textposition="outside", textfont=dict(size=10, color=TEXT2),
            hovertemplate="<b>%{y}</b><br>Riesgo: %{x:.2f}<extra></extra>",
            width=0.65,
        ))
        fig_c4.update_layout(**CHART, height=300, bargap=0.28,
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[0, 5.5]),
            yaxis=dict(showgrid=False, tickfont=dict(size=10)))
        st.plotly_chart(fig_c4, use_container_width=True, config={"displayModeBar":False})
        end_card()

    # Fila 3: % Cámara por CGM + Mapa calor CGM × día
    col_c6, col_c7 = st.columns([2, 3])

    with col_c6:
        card("% Cobertura de Cámara por CGM","🎥")
        cam_cgm = dfc.groupby("CGM")["con_camara"].agg(["sum","count"]).reset_index()
        cam_cgm.columns = ["cgm","con","total"]
        cam_cgm["pct"] = cam_cgm["con"] / cam_cgm["total"] * 100
        cam_cgm = cam_cgm.sort_values("pct", ascending=True)
        fig_c6 = go.Figure(go.Bar(
            x=cam_cgm["pct"], y=cam_cgm["cgm"], orientation="h",
            marker=dict(color=cam_cgm["pct"],
                        colorscale=[[0,"#1e1b4b"],[0.5,ACCENT],[1,GREEN]],
                        showscale=False, line=dict(color="rgba(0,0,0,0)",width=0)),
            text=[f"{p:.0f}%" for p in cam_cgm["pct"]],
            textposition="outside", textfont=dict(size=10, color=TEXT2),
            hovertemplate="<b>%{y}</b><br>%{x:.1f}% cámara<extra></extra>",
            width=0.65,
        ))
        fig_c6.update_layout(**CHART, height=350, bargap=0.25,
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[0,115]),
            yaxis=dict(showgrid=False, tickfont=dict(size=10)))
        st.plotly_chart(fig_c6, use_container_width=True, config={"displayModeBar":False})
        end_card()

    with col_c7:
        card("Mapa de Calor  ·  CGM × Día de Semana","🗓️")
        dias_ord2 = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
        mat2  = dfc.groupby(["CGM","DiaNom"]).size().reset_index(name="n")
        piv3  = mat2.pivot(index="CGM", columns="DiaNom", values="n").fillna(0)
        piv3  = piv3.reindex(columns=[d for d in dias_ord2 if d in piv3.columns])
        piv3  = piv3.loc[piv3.sum(axis=1).sort_values(ascending=True).index]
        fig_c7 = go.Figure(go.Heatmap(
            z=piv3.values, x=list(piv3.columns), y=list(piv3.index),
            colorscale=[[0,BG2],[0.5,"#4c1d95"],[1,ACCENT]],
            showscale=True, colorbar=dict(thickness=8, tickfont=dict(size=9,color=TEXT2)),
            hovertemplate="<b>%{y}</b> · <b>%{x}</b><br>%{z:.0f} novedades<extra></extra>",
            texttemplate="%{z:.0f}", textfont=dict(size=9, color=TEXT)
        ))
        fig_c7.update_layout(**CHART, height=350,
            xaxis=dict(showgrid=False, side="top"),
            yaxis=dict(showgrid=False))
        st.plotly_chart(fig_c7, use_container_width=True, config={"displayModeBar":False})
        end_card()

# ── FOOTER ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;color:{MUTED};font-size:.7rem;margin-top:10px;padding:6px;">
    COL · Análisis Operativo &nbsp;·&nbsp; {sd.strftime('%d/%m/%Y')} → {ed.strftime('%d/%m/%Y')}
    &nbsp;·&nbsp; {n_cur:,} registros &nbsp;·&nbsp; Actualización automática cada 5 min
</div>""", unsafe_allow_html=True)
