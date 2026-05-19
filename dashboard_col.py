import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import timedelta
import math, io, os

st.set_page_config(page_title="COL · Análisis Operativo", page_icon="🔵", layout="wide", initial_sidebar_state="collapsed")

# ── SESSION ────────────────────────────────────────────────────────────────────
for k, v in [("vista","ejecutiva"),("pie_mode","turno")]:
    if k not in st.session_state: st.session_state[k] = v

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
SEQ_DIV = [GREEN, ACCENT, AMBER, RED, "#38bdf8"]

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
    display:flex;align-items:center;justify-content:space-between;
    background:linear-gradient(90deg,{BG2} 0%,#1a1535 50%,{BG2} 100%);
    border:1px solid {BORDER};border-radius:16px;
    padding:14px 24px;margin-bottom:14px;
    box-shadow:0 4px 24px rgba(0,0,0,0.5);
}}
.topbar-title{{font-size:1.35rem;font-weight:800;color:{TEXT};letter-spacing:-.3px;}}
.topbar-sub{{font-size:.82rem;color:{TEXT2};margin-top:2px;}}

/* Filtros bar */
.filter-bar{{
    background:{BG2};border:1px solid rgba(139,92,246,0.16);border-radius:14px;
    padding:12px 18px;margin-bottom:14px;
}}

.kpi{{
    background:{CARD};border:1px solid {BORDER};border-radius:18px;
    padding:18px 20px;position:relative;overflow:hidden;height:100%;
}}
.kpi::before{{
    content:'';position:absolute;top:0;left:0;right:0;height:3px;
    background:linear-gradient(90deg,{ACCENT},{ACCENT2});border-radius:18px 18px 0 0;
}}
.kpi-icon{{font-size:1.5rem;margin-bottom:4px;}}
.kpi-label{{font-size:.75rem;color:{TEXT2};font-weight:600;letter-spacing:.06em;text-transform:uppercase;}}
.kpi-val{{font-size:2rem;font-weight:800;color:{TEXT};line-height:1.1;margin:4px 0;}}
.kpi-d-pos{{font-size:.75rem;color:{GREEN};font-weight:600;}}
.kpi-d-neg{{font-size:.75rem;color:{RED};font-weight:600;}}
.kpi-d-neu{{font-size:.75rem;color:{MUTED};font-weight:600;}}
.kpi-sub{{font-size:.72rem;color:{MUTED};margin-top:3px;}}

.card{{
    background:{CARD};border:1px solid rgba(139,92,246,0.14);
    border-radius:18px;padding:18px 20px 16px;margin-bottom:14px;
    box-shadow:0 4px 20px rgba(0,0,0,0.3);
}}
.card-title{{
    font-size:.85rem;font-weight:700;color:{TEXT};
    letter-spacing:.03em;text-transform:uppercase;
    border-bottom:1px solid rgba(139,92,246,0.15);
    padding-bottom:8px;margin-bottom:12px;
    display:flex;align-items:center;gap:7px;
}}

.alert{{
    background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);
    border-radius:12px;padding:10px 16px;font-size:.85rem;color:#fca5a5;
    margin-bottom:12px;
}}
.alert-ok{{
    background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.25);
    border-radius:12px;padding:10px 16px;font-size:.85rem;color:#6ee7b7;
    margin-bottom:12px;
}}

.stButton>button{{border-radius:12px!important;font-weight:600!important;font-size:.83rem!important;padding:7px 14px!important;transition:all .15s!important;}}
.stDownloadButton button{{background:{ACCENT}!important;color:#fff!important;border:none!important;border-radius:12px!important;font-weight:700!important;font-size:.83rem!important;padding:8px 14px!important;}}
.stDownloadButton button:hover{{background:{GREEN}!important;}}
.js-plotly-plot .plotly .modebar{{display:none!important;}}
hr{{border-color:rgba(139,92,246,0.12);margin:10px 0;}}
label{{font-size:.82rem!important;color:{TEXT2}!important;font-weight:500!important;}}
</style>
""", unsafe_allow_html=True)

# ── DATA ───────────────────────────────────────────────────────────────────────
CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vRBFU12b6jgWRdNJbj5yKqKJ0iucps7HFJlkmKyjNi2DeccbtnnBM4aQEEbxKOAgKL78DUZJwFIJauX"
    "/pub?gid=2079582736&single=true&output=csv"
)

@st.cache_data(ttl=300)
def load():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={"Categoria":"Categoría","Comisaria":"Comisaría","Camara del Evento":"Cámara"})
    df["ts"]      = pd.to_datetime(df["Marca temporal"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
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
    df["Franja"]  = df["hora"].apply(lambda h: ["00-03","03-06","06-09","09-12","12-15","15-18","18-21","21-00"][min(h//3,7)])

    if "Subcategoria" not in df.columns:
        sc = [c for c in df.columns if c.startswith("Subcategoria ")]
        df["Subcategoria"] = df[sc].replace("", pd.NA).bfill(axis=1).iloc[:,0].fillna("")
    df["Subcategoria"] = df["Subcategoria"].fillna("").str.strip()
    df["con_camara"]   = df["¿Se ve por cámara?"].str.upper().str.strip() == "SI"

    riesgo_map = {"Robo":3,"Hurto":2,"Heridos":5,"Obito":5,"Violencia":4,
                  "Persecución":3,"Accidente de tránsito":2,"Conflicto":2,"Incendios":3,"Otros":1}
    df["riesgo"] = df["Categoría"].map(riesgo_map).fillna(1)
    return df

with st.spinner(""):
    try:
        df = load()
    except Exception as e:
        st.error(f"Error cargando datos: {e}"); st.stop()

min_d = df["fecha"].min()
max_d = df["fecha"].max()

# ── HELPERS ────────────────────────────────────────────────────────────────────
def kpi_card(icon, label, val, delta=None, sub="", invert=False):
    """delta=None → no muestra variación. delta=float → muestra flecha."""
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
        delta_html = f"<div class='{cls}'>{arr} {abs(delta):.1f}% vs período anterior</div>"
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
    col_pie  = "Turno" if mode == "turno" else "TipoDia"
    pie_data = df_filt[col_pie].value_counts().reset_index()
    pie_data.columns = [col_pie, "n"]
    pie_colors = [ACCENT, GREEN, AMBER, RED, "#38bdf8"]
    total_pie  = pie_data["n"].sum()
    fig = go.Figure(go.Pie(
        labels=pie_data[col_pie], values=pie_data["n"], hole=0.55,
        marker=dict(colors=pie_colors[:len(pie_data)], line=dict(color=BG, width=3)),
        textinfo="none", sort=True, direction="clockwise",
        hovertemplate="%{label}<br><b>%{value}</b> (%{percent})<extra></extra>",
    ))
    ann = []
    ang = 90.0
    for _, row in pie_data.iterrows():
        p  = row["n"] / total_pie
        sw = p * 360
        ma = math.radians(ang - sw / 2)
        ann.append(dict(
            text=f"<b>{row[col_pie]}</b><br>{p*100:.0f}%",
            x=0.5 + 0.65*0.5*math.cos(ma), y=0.5 + 0.65*0.5*math.sin(ma),
            xref="paper", yref="paper", showarrow=False,
            font=dict(size=9, color="#fff"),
            bgcolor="rgba(20,20,40,0.82)",
            bordercolor="rgba(255,255,255,0.1)",
            borderpad=4, borderwidth=1, align="center",
        ))
        ang -= sw
    ann.append(dict(
        text=f"<b>{total_pie:,}</b><br><span style='font-size:9px'>Total</span>",
        x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
        font=dict(size=13, color=TEXT), align="center",
    ))
    lyt = {**CHART}
    lyt["margin"] = dict(l=10, r=10, t=10, b=30)
    fig.update_layout(**lyt, height=290, annotations=ann,
        showlegend=True,
        legend=dict(orientation="h", x=0.5, y=-0.04, xanchor="center",
                    font=dict(size=9, color=TEXT2), bgcolor="rgba(0,0,0,0)"))
    return fig

# ── TOPBAR ─────────────────────────────────────────────────────────────────────
c_logo, c_mid, c_logo2 = st.columns([1, 8, 1])
with c_logo:
    if os.path.exists("logo_izquierda.png"): st.image("logo_izquierda.png", width=60)
with c_mid:
    st.markdown("""
    <div class="topbar">
        <div>
            <div class="topbar-title">Centro de Operaciones Lomas &nbsp;·&nbsp; Análisis Operativo</div>
            <div class="topbar-sub">Reporte interactivo · Sistema de monitoreo</div>
        </div>
    </div>""", unsafe_allow_html=True)
with c_logo2:
    if os.path.exists("logo_derecha.png"): st.image("logo_derecha.png", width=60)

# ── FILTROS VISIBLES EN LA PÁGINA ──────────────────────────────────────────────
with st.expander("🔽  Filtros", expanded=True):
    f1, f2, f3, f4, f5 = st.columns([2.5, 1.4, 1.6, 1.4, 1.4])
    with f1:
        rango = st.date_input("Período", value=(max_d.replace(day=1), max_d),
                              min_value=min_d, max_value=max_d, format="DD/MM/YYYY")
    with f2:
        cats = st.multiselect("Categoría", sorted(df["Categoría"].dropna().unique()), default=[], placeholder="Todas")
    with f3:
        # Subcategorías dinámicas según categoría elegida
        if cats:
            subs_disp = df[df["Categoría"].isin(cats)]["Subcategoria"]
        else:
            subs_disp = df["Subcategoria"]
        subs_disp = subs_disp[subs_disp.str.strip() != ""].dropna().unique().tolist()
        subcats = st.multiselect("Subcategoría", sorted(subs_disp), default=[], placeholder="Todas")
    with f4:
        coms = st.multiselect("Comisaría", sorted(df["Comisaría"].dropna().unique()), default=[], placeholder="Todas")
    with f5:
        turnos = st.multiselect("Turno", sorted(df["Turno"].dropna().unique()), default=[], placeholder="Todos")

# ── FILTRADO ───────────────────────────────────────────────────────────────────
if isinstance(rango, tuple) and len(rango) == 2:
    sd, ed = rango
elif isinstance(rango, tuple) and len(rango) == 1:
    sd = ed = rango[0]
else:
    sd = ed = rango

days    = (ed - sd).days + 1
prev_ed = sd - timedelta(days=1)
prev_sd = prev_ed - timedelta(days=days - 1)

def filtrar(frame, d0, d1):
    m = (frame["fecha"] >= d0) & (frame["fecha"] <= d1)
    if cats:   m &= frame["Categoría"].isin(cats)
    if subcats: m &= frame["Subcategoria"].isin(subcats)
    if coms:   m &= frame["Comisaría"].isin(coms)
    if turnos: m &= frame["Turno"].isin(turnos)
    return frame[m].copy()

dfc = filtrar(df, sd, ed)
dfp = filtrar(df, prev_sd, prev_ed)

n_cur  = len(dfc)
n_prev = len(dfp)
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

# ── ALERTA ─────────────────────────────────────────────────────────────────────
if n_cur > 0:
    if d_pct > 20:
        st.markdown(f'<div class="alert">🚨 <b>Alerta:</b> Las novedades aumentaron un <b>{d_pct:.1f}%</b> vs el período anterior · Categoría más afectada: <b>{cat_top}</b> ({cat_top_n} casos)</div>', unsafe_allow_html=True)
    elif d_pct < -20:
        st.markdown(f'<div class="alert-ok">✅ <b>Tendencia positiva:</b> Las novedades bajaron un <b>{abs(d_pct):.1f}%</b> vs el período anterior</div>', unsafe_allow_html=True)

# ── NAV VISTAS + EXPORTAR ──────────────────────────────────────────────────────
nav1, nav2, sp, dl_col = st.columns([1.2, 1.3, 5, 1.5])
with nav1:
    if st.button("📊 Ejecutivo", type="primary" if st.session_state.vista=="ejecutiva" else "secondary", use_container_width=True):
        st.session_state.vista = "ejecutiva"; st.rerun()
with nav2:
    if st.button("🗺️ Territorial", type="primary" if st.session_state.vista=="territorial" else "secondary", use_container_width=True):
        st.session_state.vista = "territorial"; st.rerun()
with dl_col:
    buf = io.BytesIO()
    dfc.drop(columns=["hora","weekday","riesgo","con_camara"], errors="ignore").to_excel(buf, index=False, engine="openpyxl")
    st.download_button("⬇ Exportar Excel", data=buf.getvalue(),
        file_name=f"col_{sd}_{ed}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True)

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  VISTA EJECUTIVA
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.vista == "ejecutiva":

    # ── KPIs ──────────────────────────────────────────────────────────────────
    k1,k2,k3,k4,k5 = st.columns(5)
    with k1: kpi_card("📋","Total Novedades", f"{n_cur:,}", delta=d_pct, invert=True)
    with k2: kpi_card("📷","Con Cámara", f"{cam_pct:.1f}%", delta=d_cam, sub=f"{int(dfc['con_camara'].sum())} eventos")
    with k3: kpi_card("⚠️","Índice de Riesgo", f"{riesgo_med:.2f}", delta=d_riesgo, sub="Escala 1–5", invert=True)
    with k4: kpi_card("🕐","Hora Pico", f"{hora_pico:02d}:00", delta=None, sub=f"Franja {hora_pico//3*3:02d}–{hora_pico//3*3+3:02d}hs")
    with k5: kpi_card("🔺","Categoría Líder", cat_top, delta=None, sub=f"{cat_top_n} casos")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Fila 1: Evolución + Heatmap Día×Turno ─────────────────────────────────
    col_ev, col_hm = st.columns([3, 2])

    with col_ev:
        card("Evolución Diaria de Novedades","📈")
        daily_c = dfc.groupby("fecha").size().reset_index(name="n")
        daily_p = dfp.groupby("fecha").size().reset_index(name="n")
        fig = go.Figure()
        if len(daily_p):
            x_p = daily_c["fecha"].astype(str).values[:len(daily_p)]
            fig.add_trace(go.Scatter(
                x=x_p, y=daily_p["n"].values[:len(x_p)], name="Anterior",
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
                hovertemplate="Media 7d: <b>%{y}</b><extra></extra>"
            ))
        fig.update_layout(**CHART, height=270,
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
            showscale=True,
            colorbar=dict(thickness=10, len=0.8, tickfont=dict(size=9, color=TEXT2)),
            hovertemplate="<b>%{y} · %{x}</b><br>%{z:.0f} novedades<extra></extra>",
            texttemplate="%{z:.0f}", textfont=dict(size=11, color=TEXT)
        ))
        fig2.update_layout(**CHART, height=270,
            xaxis=dict(showgrid=False, side="top"),
            yaxis=dict(showgrid=False, autorange="reversed"))
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
        end_card()

    # ── Fila 2: Barras categoría + Donut + Ranking comisarías ─────────────────
    col_cat, col_don, col_rank = st.columns([2.4, 1.6, 2])

    with col_cat:
        card("Novedades por Categoría  ·  color = nivel de riesgo","📂")
        cat_df = dfc["Categoría"].value_counts().reset_index()
        cat_df.columns = ["cat","n"]
        cat_df["pct"]   = cat_df["n"] / cat_df["n"].sum() * 100
        risk_map = {"Robo":3,"Hurto":2,"Heridos":5,"Obito":5,"Violencia":4,
                    "Persecución":3,"Accidente de tránsito":2,"Conflicto":2,"Incendios":3,"Otros":1}
        cat_df["riesgo"] = cat_df["cat"].map(risk_map).fillna(1)
        cat_df = cat_df.sort_values("n", ascending=True)
        bar_colors = [RED if r>=4 else AMBER if r==3 else ACCENT for r in cat_df["riesgo"]]
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=cat_df["n"], y=cat_df["cat"], orientation="h",
            marker=dict(color=bar_colors, line=dict(color="rgba(0,0,0,0)", width=0)),
            text=[f"{n}  ({p:.0f}%)" for n,p in zip(cat_df["n"], cat_df["pct"])],
            textposition="outside", textfont=dict(size=10, color=TEXT2),
            hovertemplate="<b>%{y}</b><br>%{x} novedades<extra></extra>",
            width=0.65, showlegend=False,
        ))
        for color, label in [(RED,"Alto"),(AMBER,"Medio"),(ACCENT,"Bajo")]:
            fig3.add_trace(go.Bar(x=[None], y=[None], marker_color=color, name=label, showlegend=True))
        fig3.update_layout(**CHART, height=310, bargap=0.3, barmode="overlay",
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, tickfont=dict(size=10)),
            legend=dict(orientation="h", y=-0.08, x=0, font=dict(size=9),
                        title=dict(text="Riesgo  ", font=dict(size=9, color=TEXT2)),
                        bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":False})
        end_card()

    with col_don:
        card("Distribución por Turno / Día","🌙")
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
        card("Ranking de Comisarías","🏆")
        com_df = dfc["Comisaría"].value_counts().reset_index()
        com_df.columns = ["com","n"]
        com_df["rank"] = range(1, len(com_df)+1)
        com_df = com_df.head(10).sort_values("n", ascending=True)
        bar_c  = [RED if r==1 else AMBER if r==2 else ACCENT if r==3 else "#4c1d95"
                  for r in com_df["rank"].iloc[::-1]][::-1]
        fig5 = go.Figure(go.Bar(
            x=com_df["n"], y=com_df["com"], orientation="h",
            marker=dict(color=bar_c, line=dict(color="rgba(0,0,0,0)", width=0)),
            text=com_df["n"], textposition="outside",
            textfont=dict(size=10, color=TEXT2),
            hovertemplate="<b>%{y}</b><br>%{x} novedades<extra></extra>",
            width=0.65,
        ))
        fig5.update_layout(**CHART, height=310, bargap=0.28,
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, tickfont=dict(size=10)))
        st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar":False})
        end_card()


# ══════════════════════════════════════════════════════════════════════════════
#  VISTA TERRITORIAL
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.vista == "territorial":

    com_top    = dfc["Comisaría"].value_counts()
    n_coms     = dfc["Comisaría"].nunique()
    prom_com   = n_cur / n_coms if n_coms else 0
    cat_cam    = dfc[dfc["con_camara"]]["Categoría"].value_counts().index[0] if dfc["con_camara"].sum() else "—"
    cam_top_n  = dfc[dfc["con_camara"]]["Categoría"].value_counts().iloc[0] if dfc["con_camara"].sum() else 0

    # KPIs sin delta
    k1,k2,k3,k4 = st.columns(4)
    with k1: kpi_card("🏢","Comisarías activas", str(n_coms), delta=None)
    with k2: kpi_card("📍","Comisaría líder", com_top.index[0] if n_cur else "—", delta=None, sub=f"{com_top.iloc[0]} casos" if n_cur else "")
    with k3: kpi_card("📊","Promedio por Comisaría", f"{prom_com:.0f}", delta=None, sub="novedades")
    with k4: kpi_card("📷","Categoría más filmada", cat_cam, delta=None, sub=f"{cam_top_n} con cámara")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    col_a, col_b = st.columns([3, 2])

    with col_a:
        card("Novedades por Comisaría y Categoría (Top 5 categorías)","🗂️")
        ct = dfc.groupby(["Comisaría","Categoría"]).size().reset_index(name="n")
        top5 = dfc["Categoría"].value_counts().head(5).index.tolist()
        ct   = ct[ct["Categoría"].isin(top5)]
        fig6 = px.bar(ct, x="Comisaría", y="n", color="Categoría",
                      color_discrete_sequence=SEQ_DIV, barmode="stack")
        fig6.update_layout(**CHART, height=310,
            xaxis=dict(showgrid=False, tickangle=-40, tickfont=dict(size=9), title=None),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=False, title=None),
            legend=dict(orientation="h", y=1.12, x=0, font=dict(size=9),
                        title_text="", bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar":False})
        end_card()

    with col_b:
        card("% Cobertura de Cámara por Comisaría","🎥")
        cam_com = dfc.groupby("Comisaría")["con_camara"].agg(["sum","count"]).reset_index()
        cam_com.columns = ["Comisaría","con_cam","total"]
        cam_com["pct"] = cam_com["con_cam"] / cam_com["total"] * 100
        cam_com = cam_com.sort_values("pct", ascending=True).tail(12)
        fig7 = go.Figure(go.Bar(
            x=cam_com["pct"], y=cam_com["Comisaría"], orientation="h",
            marker=dict(color=cam_com["pct"],
                        colorscale=[[0,"#1e1b4b"],[0.5,ACCENT],[1,GREEN]],
                        showscale=False, line=dict(color="rgba(0,0,0,0)", width=0)),
            text=[f"{p:.0f}%" for p in cam_com["pct"]],
            textposition="outside", textfont=dict(size=10, color=TEXT2),
            hovertemplate="<b>%{y}</b><br>%{x:.1f}% con cámara<extra></extra>",
            width=0.65,
        ))
        fig7.update_layout(**CHART, height=310, bargap=0.28,
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
        showscale=True, colorbar=dict(thickness=10, tickfont=dict(size=9, color=TEXT2)),
        hovertemplate="<b>%{y}</b> · <b>%{x}</b><br>%{z:.0f} novedades<extra></extra>",
        texttemplate="%{z:.0f}", textfont=dict(size=9, color=TEXT)
    ))
    fig8.update_layout(**CHART, height=360,
        xaxis=dict(showgrid=False, side="top"),
        yaxis=dict(showgrid=False))
    st.plotly_chart(fig8, use_container_width=True, config={"displayModeBar":False})
    end_card()

# ── FOOTER ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;color:{MUTED};font-size:.72rem;margin-top:10px;padding:6px;">
    COL · Análisis Operativo &nbsp;·&nbsp; {sd.strftime('%d/%m/%Y')} → {ed.strftime('%d/%m/%Y')}
    &nbsp;·&nbsp; {n_cur:,} registros &nbsp;·&nbsp; Actualización automática cada 5 min
</div>""", unsafe_allow_html=True)
