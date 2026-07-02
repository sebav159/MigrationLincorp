"""
Dashboard de avance - Proyecto de Migracion RMS a Xstore (Tambo / Aruma)
Cliente: Lindcorp
"""
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"

# Pestaña "Finanzas" (gastos/ingresos de caja chica del proveedor) oculta por
# defecto: es informacion interna del proveedor (pasajes, movilidad), no se
# expone al cliente. Poner en True solo para uso interno del equipo.
SHOW_FINANZAS = False

# ---------------------------------------------------------------------------
# Tema visual — inspirado en la identidad de Tambo (naranja de marca) con un
# acabado limpio y profesional para uso corporativo frente al cliente.
# ---------------------------------------------------------------------------
PRIMARY = "#5B2A86"        # Morado Tambo
PRIMARY_DARK = "#3E1D5C"
PRIMARY_LIGHT = "#EDE1F7"
ACCENT = "#FDC700"         # Amarillo Tambo
ACCENT_DARK = "#C79A00"
CHARCOAL = "#1A1A1A"       # Negro Tambo
GREY_TEXT = "#5C5866"
BG = "#FAF9FB"
CARD_BG = "#FFFFFF"
BORDER = "#E9E4F0"
GREEN = "#1E8E5A"
RED = "#E53935"            # Rojo Tambo (descuentos / alertas)
AMBER = "#E0A030"
BLUE = "#3A6EA5"

PALETTE = [PRIMARY, ACCENT, RED, BLUE, GREEN, CHARCOAL, "#8A5A44", "#B8B0A6"]

st.set_page_config(
    page_title="Migracion Tambo / Aruma — Lindcorp",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {BG};
        color: {CHARCOAL};
        font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}
    section[data-testid="stSidebar"] {{
        background-color: {CHARCOAL};
    }}
    section[data-testid="stSidebar"] * {{
        color: #F2EEE9 !important;
    }}
    .dash-header {{
        background: {PRIMARY};
        padding: 22px 28px;
        border-radius: 14px;
        margin-bottom: 18px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .dash-header h1 {{
        color: white;
        font-size: 30px;
        margin: 0;
        font-weight: 700;
    }}
    .dash-header p {{
        color: {PRIMARY_LIGHT};
        margin: 4px 0 0 0;
        font-size: 15px;
    }}
    div[data-testid="column"] {{
        display: flex;
        align-items: stretch;
    }}
    div[data-testid="column"] > div {{
        width: 100%;
    }}
    .kpi-card {{
        background: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        height: 100%;
        min-height: 128px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }}
    .kpi-label {{
        color: {GREY_TEXT};
        font-size: 13.5px;
        text-transform: uppercase;
        letter-spacing: .04em;
        font-weight: 600;
        margin-bottom: 6px;
        min-height: 2.4em;
        display: flex;
        align-items: flex-start;
    }}
    .kpi-value {{
        color: {CHARCOAL};
        font-size: 34px;
        font-weight: 700;
        line-height: 1.15;
    }}
    .kpi-sub {{
        color: {GREY_TEXT};
        font-size: 13.5px;
        margin-top: 4px;
    }}
    .badge {{
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
    }}
    .section-title {{
        font-size: 20px;
        font-weight: 700;
        color: {CHARCOAL};
        margin: 6px 0 10px 0;
        border-left: 4px solid {PRIMARY};
        padding-left: 10px;
    }}
    .note {{
        color: {GREY_TEXT};
        font-size: 13.5px;
        font-style: italic;
    }}
    div[data-testid="stMetricValue"] {{
        color: {CHARCOAL};
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: white;
        border-radius: 8px 8px 0 0;
        padding: 8px 16px;
        border: 1px solid {BORDER};
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {PRIMARY} !important;
        color: white !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

PLOTLY_LAYOUT = dict(
    font=dict(family="Segoe UI, Helvetica, Arial, sans-serif", color=CHARCOAL, size=16),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=-0.3, font=dict(size=14)),
    xaxis=dict(tickfont=dict(size=14), title_font=dict(size=15)),
    yaxis=dict(tickfont=dict(size=14), title_font=dict(size=15)),
    uniformtext=dict(minsize=13, mode="hide"),
)


def style_fig(fig):
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig


def kpi_card(label, value, sub=""):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    cronograma = pd.read_csv(DATA_DIR / "cronograma.csv")
    resumen_olas = pd.read_csv(DATA_DIR / "resumen_olas.csv")
    incidencias = pd.read_csv(DATA_DIR / "incidencias.csv")
    tecnicos = pd.read_csv(DATA_DIR / "tecnicos.csv")
    gastos = pd.read_csv(DATA_DIR / "gastos.csv", parse_dates=["fecha"])
    ingresos = pd.read_csv(DATA_DIR / "ingresos.csv", parse_dates=["fecha"])
    plan_contrato = pd.read_csv(DATA_DIR / "plan_contrato.csv")
    cobertura = pd.read_csv(DATA_DIR / "cobertura_provincias.csv")

    cronograma["fecha"] = pd.to_datetime(cronograma["fecha"])
    cronograma = compute_durations(cronograma)
    return {
        "cronograma": cronograma,
        "resumen_olas": resumen_olas,
        "incidencias": incidencias,
        "tecnicos": tecnicos,
        "gastos": gastos,
        "ingresos": ingresos,
        "plan_contrato": plan_contrato,
        "cobertura": cobertura,
    }


def _to_dt(base_date, time_str):
    if pd.isna(time_str) or str(time_str).strip() == "":
        return pd.NaT
    try:
        return pd.to_datetime(
            base_date.strftime("%Y-%m-%d") + " " + str(time_str).strip(),
            format="%Y-%m-%d %I:%M %p",
        )
    except ValueError:
        return pd.NaT


def compute_durations(df):
    """Reconstruye timestamps completos (con rollover de medianoche) y calcula
    el tiempo muerto operativo: desde el INGRESO del tecnico a tienda (objetivo
    desde las 9:30 PM) hasta el CIERRE DE CAJA del sistema anterior (objetivo
    maximo 10:30 PM), que es la ventana que definen los procedimientos del
    proyecto para dejar la tienda lista para el corte."""
    seq_cols = ["ingreso", "cierre_caja", "inicio_xstore", "fin_xstore", "inicio_xadmin", "fin_xadmin"]
    downtime_min = []
    duracion_total_min = []
    for _, row in df.iterrows():
        base = row["fecha"]
        prev_dt = None
        resolved = {}
        for col in seq_cols:
            dt = _to_dt(base, row.get(col))
            if pd.notna(dt) and prev_dt is not None:
                while dt < prev_dt:
                    dt = dt + pd.Timedelta(days=1)
            if pd.notna(dt):
                prev_dt = dt
            resolved[col] = dt
        # El 23/06 "ingreso" quedo registrado en horario AM (llegada matutina
        # del tecnico), a diferencia del resto de fechas donde "ingreso" es la
        # entrada previa al corte (~8-9:30 PM). No son el mismo hito operativo,
        # asi que esas filas quedan fuera de este calculo para no mezclar
        # horas de espera de +12h que no son tiempo muerto real. Se compara
        # ademas contra el cierre de caja del MISMO dia (sin rollover): si
        # aparece antes que el ingreso es un error de registro puntual en la
        # fuente, no un cruce de medianoche legitimo.
        ingreso_es_pm = "PM" in str(row.get("ingreso") or "").upper()
        cierre_mismo_dia = _to_dt(base, row.get("cierre_caja"))
        if (
            pd.notna(resolved["ingreso"])
            and pd.notna(cierre_mismo_dia)
            and ingreso_es_pm
            and cierre_mismo_dia >= resolved["ingreso"]
        ):
            downtime_min.append((cierre_mismo_dia - resolved["ingreso"]).total_seconds() / 60)
        else:
            downtime_min.append(None)
        if pd.notna(resolved["ingreso"]) and pd.notna(resolved["fin_xadmin"]):
            duracion_total_min.append((resolved["fin_xadmin"] - resolved["ingreso"]).total_seconds() / 60)
        else:
            duracion_total_min.append(None)
    df = df.copy()
    df["downtime_min"] = downtime_min
    df["duracion_total_min"] = duracion_total_min
    return df


def explode_tecnicos(df):
    """Divide celdas con varios tecnicos ('Carlos y Adrian', 'A, B') en filas
    individuales para poder contabilizar carga de trabajo por persona."""
    rows = []
    for _, row in df.iterrows():
        raw = str(row.get("tecnico", "") or "")
        parts = [p.strip() for p in re.split(r"\s+y\s+|,\s*", raw) if p.strip()]
        for p in parts or [raw]:
            r = row.copy()
            r["tecnico_individual"] = p
            rows.append(r)
    return pd.DataFrame(rows)


data = load_data()
cronograma = data["cronograma"]
resumen_olas = data["resumen_olas"]
incidencias = data["incidencias"]
tecnicos = data["tecnicos"]
gastos = data["gastos"]
ingresos = data["ingresos"]
plan_contrato = data["plan_contrato"]
cobertura = data["cobertura"]

TOTAL_TIENDAS_PLAN = int(plan_contrato["total"].sum())  # 965
TOTAL_MIGRADAS_CONFIRMADAS = int(resumen_olas["tiendas_migradas"].sum())
DOWNTIME_TARGET_MIN = 60  # ingreso 9:30 PM -> cierre de caja maximo 10:30 PM

# ---------------------------------------------------------------------------
# Sidebar — filtros interactivos
# ---------------------------------------------------------------------------
st.sidebar.markdown("## Filtros")
st.sidebar.caption("Aplican a las vistas de Cronograma, Incidencias, Equipo y Detalle de tiendas.")

min_date = cronograma["fecha"].min().date()
max_date = cronograma["fecha"].max().date()
date_range = st.sidebar.date_input(
    "Rango de fechas", value=(min_date, max_date), min_value=min_date, max_value=max_date
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

estatus_opts = sorted(cronograma["estatus"].dropna().unique().tolist())
estatus_sel = st.sidebar.multiselect("Estatus", estatus_opts, default=estatus_opts)

distrito_opts = sorted(cronograma["distrito"].dropna().unique().tolist())
distrito_sel = st.sidebar.multiselect("Distrito", distrito_opts, default=[])

tecnico_opts = sorted(cronograma["tecnico"].dropna().unique().tolist())
tecnico_sel = st.sidebar.multiselect("Tecnico asignado", tecnico_opts, default=[])

mask = (
    (cronograma["fecha"].dt.date >= start_date)
    & (cronograma["fecha"].dt.date <= end_date)
    & (cronograma["estatus"].isin(estatus_sel))
)
if distrito_sel:
    mask &= cronograma["distrito"].isin(distrito_sel)
if tecnico_sel:
    mask &= cronograma["tecnico"].isin(tecnico_sel)

cron_f = cronograma[mask].copy()

st.sidebar.markdown("---")
st.sidebar.caption(
    "Fuente: carpeta de Google Drive 'Migration Lincorp' "
    "(Cronograma de migracion, Resumen RMS a Xstore, Gastos diarios, "
    "Tecnicos del proyecto, Detalles del contrato)."
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="dash-header">
        <div>
            <h1>Migracion RMS &rarr; Xstore | Tambo &amp; Aruma</h1>
            <p>Panel de avance del proyecto para Lindcorp — actualizado al {max_date.strftime('%d/%m/%Y')}</p>
        </div>
        <div style="text-align:right;">
            <span style="color:{PRIMARY_LIGHT}; font-size:14px;">Alcance total</span><br>
            <span style="color:{ACCENT}; font-size:32px; font-weight:800;">{TOTAL_TIENDAS_PLAN:,} tiendas</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_names = [
    "Resumen ejecutivo",
    "Cronograma y operacion",
    "Incidencias",
    "Equipo tecnico",
]
if SHOW_FINANZAS:
    tab_names.append("Finanzas")
tab_names.append("Detalle de tiendas")

tabs = dict(zip(tab_names, st.tabs(tab_names)))

# ---------------------------------------------------------------------------
# TAB — Resumen ejecutivo
# ---------------------------------------------------------------------------
with tabs["Resumen ejecutivo"]:
    avance_pct = TOTAL_MIGRADAS_CONFIRMADAS / TOTAL_TIENDAS_PLAN * 100
    migradas_log = int((cronograma["estatus"] == "Migrada").sum())
    programadas_log = int((cronograma["estatus"] == "Programada").sum())

    ola0_row = resumen_olas.loc[resumen_olas["ola"] == "Ola 0"].iloc[0]
    ola1_row = resumen_olas.loc[resumen_olas["ola"] == "Ola 1"].iloc[0]

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Avance global confirmado", f"{avance_pct:.1f}%", f"{TOTAL_MIGRADAS_CONFIRMADAS} / {TOTAL_TIENDAS_PLAN} tiendas")
    with c2:
        kpi_card("Exito Ola 0", f"{ola0_row['exito_pct']:.1f}%", f"{int(ola0_row['tiendas_migradas'])} migradas / {int(ola0_row['tiendas_procesadas'])} procesadas")
    with c3:
        kpi_card("Exito Ola 1 (a la fecha)", f"{ola1_row['exito_pct']:.0f}%", f"{int(ola1_row['tiendas_migradas'])} / {int(ola1_row['tiendas_procesadas'])} tiendas")

    st.markdown("<br>", unsafe_allow_html=True)
    col_a, col_b = st.columns([1, 2])

    with col_a:
        st.markdown('<div class="section-title">Avance global</div>', unsafe_allow_html=True)
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=avance_pct,
                domain={"x": [0.08, 0.92], "y": [0.05, 1]},
                number={"suffix": "%", "font": {"color": CHARCOAL, "size": 44}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": CHARCOAL, "tickfont": {"size": 13}},
                    "bar": {"color": PRIMARY},
                    "bgcolor": "white",
                    "borderwidth": 0,
                    "steps": [
                        {"range": [0, 33], "color": "#F1E6FA"},
                        {"range": [33, 66], "color": "#DCC3F0"},
                        {"range": [66, 100], "color": "#C7A0E6"},
                    ],
                },
            )
        )
        fig.update_layout(**{**PLOTLY_LAYOUT, "margin": dict(l=40, r=40, t=30, b=10)})
        fig.update_layout(height=300)
        st.plotly_chart(fig, width='stretch')
        st.markdown(
            f'<span class="note">Calculado sobre tiendas migradas confirmadas oficialmente '
            f"({TOTAL_MIGRADAS_CONFIRMADAS}) frente al alcance contractual total (965 tiendas: "
            f"824 Tambo + 141 Aruma).</span>",
            unsafe_allow_html=True,
        )

    with col_b:
        st.markdown('<div class="section-title">Plan vs. ejecutado por Ola</div>', unsafe_allow_html=True)
        plan_ola = plan_contrato.groupby("ola")["total"].sum().reset_index()
        merged = plan_ola.merge(resumen_olas[["ola", "tiendas_migradas"]], on="ola", how="left").fillna(0)
        fig2 = go.Figure()
        fig2.add_bar(
            name="Plan contractual", x=merged["ola"], y=merged["total"],
            marker_color=BORDER, marker_line_color=GREY_TEXT, marker_line_width=1,
            text=merged["total"].astype(int), textposition="outside",
        )
        fig2.add_bar(
            name="Migradas (confirmado)", x=merged["ola"], y=merged["tiendas_migradas"],
            marker_color=ACCENT_DARK,
            text=merged["tiendas_migradas"].astype(int), textposition="outside",
        )
        max_val = max(merged["total"].max(), merged["tiendas_migradas"].max())
        fig2.update_yaxes(range=[0, max_val * 1.18])
        fig2.update_layout(barmode="group", height=320, **PLOTLY_LAYOUT)
        fig2.update_traces(textfont_size=14)
        st.plotly_chart(fig2, width='stretch')
        st.markdown(
            '<span class="note">Nota: la Ola 0 contractual contempla 32 tiendas (20 Tambo + 12 Aruma); '
            "el informe operativo del 28/06 reporta 78 tiendas procesadas en ese periodo, ya que el equipo "
            "adelanto tiendas de la Ola 1 en paralelo.</span>",
            unsafe_allow_html=True,
        )

    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown('<div class="section-title">Cobertura geografica</div>', unsafe_allow_html=True)
        lima_total = int(cobertura.loc[cobertura["departamento"] == "LIMA", "tiendas"].sum())
        prov_total = int(cobertura.loc[cobertura["departamento"] != "LIMA", "tiendas"].sum())
        fig3 = px.pie(
            names=["Lima Metropolitana", "Provincias"],
            values=[lima_total, prov_total],
            color_discrete_sequence=[PRIMARY, ACCENT],
            hole=0.55,
        )
        fig3.update_traces(textinfo="label+percent", textfont_size=15)
        fig3.update_layout(height=280, **PLOTLY_LAYOUT)
        st.plotly_chart(fig3, width='stretch')

    with col_d:
        st.markdown('<div class="section-title">Timeline estimado del proyecto</div>', unsafe_allow_html=True)
        timeline = pd.DataFrame(
            [
                dict(Ola="Ola 0", Inicio="2026-06-12", Fin="2026-06-24", Tipo="Confirmado"),
                dict(Ola="Ola 1", Inicio="2026-06-18", Fin="2026-07-19", Tipo="Estimado"),
                dict(Ola="Ola 2", Inicio="2026-07-19", Fin="2026-08-05", Tipo="Estimado"),
                dict(Ola="Ola 3", Inicio="2026-08-05", Fin="2026-08-23", Tipo="Estimado"),
            ]
        )
        timeline["Inicio"] = pd.to_datetime(timeline["Inicio"])
        timeline["Fin"] = pd.to_datetime(timeline["Fin"])
        fig4 = px.timeline(
            timeline, x_start="Inicio", x_end="Fin", y="Ola", color="Tipo",
            color_discrete_map={"Confirmado": PRIMARY, "Estimado": PRIMARY_LIGHT},
        )
        fig4.add_vline(
            x=pd.Timestamp("2026-07-01"), line_dash="dot", line_color=CHARCOAL,
            annotation_text="Hoy", annotation_position="top", annotation_font_color=CHARCOAL,
        )
        fig4.update_yaxes(autorange="reversed", title_text="")
        fig4.update_xaxes(title_text="", tickformat="%d %b")
        fig4.update_layout(**{
            **PLOTLY_LAYOUT,
            "margin": dict(l=10, r=10, t=40, b=70),
            "legend": dict(orientation="h", yanchor="bottom", y=-0.45, font=dict(size=14), title_text=""),
        })
        fig4.update_layout(height=320)
        st.plotly_chart(fig4, width='stretch')
        st.markdown(
            '<span class="note">Ola 0 y el inicio de Ola 1 estan confirmados por el contrato y los informes '
            "operativos. Los limites de Ola 1/2/3 son una estimacion proporcional al numero de tiendas de cada "
            "ola dentro del plazo contractual (18/06 al 23/08/2026), sujeta a actualizacion.</span>",
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# TAB 2 — Cronograma y operacion
# ---------------------------------------------------------------------------
with tabs["Cronograma y operacion"]:
    st.markdown('<div class="section-title">Tiendas migradas por dia (dias con operacion)</div>', unsafe_allow_html=True)
    daily_src = cron_f[cron_f["estatus"].isin(["Migrada", "Reprogramada"])].copy()
    if daily_src.empty:
        st.info("No hay tiendas migradas o reprogramadas en el filtro seleccionado.")
    else:
        daily_src["fecha_label"] = daily_src["fecha"].dt.strftime("%d %b")
        orden_fechas = (
            daily_src[["fecha", "fecha_label"]]
            .drop_duplicates()
            .sort_values("fecha")["fecha_label"]
            .tolist()
        )
        daily = daily_src.groupby(["fecha_label", "estatus"]).size().reset_index(name="tiendas")
        fig = px.bar(
            daily, x="fecha_label", y="tiendas", color="estatus", barmode="stack",
            category_orders={"fecha_label": orden_fechas},
            color_discrete_map={"Migrada": PRIMARY, "Reprogramada": RED},
        )
        fig.update_xaxes(type="category", title_text="")
        fig.update_yaxes(title_text="Tiendas")
        fig.update_layout(**{**PLOTLY_LAYOUT, "margin": dict(l=10, r=10, t=40, b=80)})
        fig.update_layout(height=340)
        st.plotly_chart(fig, width='stretch')

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="section-title">Tiempo muerto por tienda (min)</div>', unsafe_allow_html=True)
        dt_df = cron_f[cron_f["downtime_min"].notna()].sort_values("downtime_min", ascending=False)
        if not dt_df.empty:
            fig = px.bar(
                dt_df, x="nombre_tienda", y="downtime_min", color="downtime_min",
                color_continuous_scale=[PRIMARY_LIGHT, PRIMARY_DARK],
            )
            fig.add_hline(
                y=DOWNTIME_TARGET_MIN, line_dash="dot", line_color=RED,
                annotation_text=f"Objetivo maximo: {DOWNTIME_TARGET_MIN} min", annotation_position="top left",
                annotation_font_color=RED,
            )
            fig.update_layout(height=420, xaxis_tickangle=-45, yaxis_title="Minutos", **PLOTLY_LAYOUT)
            st.plotly_chart(fig, width='stretch')
            st.markdown(
                '<span class="note">Tiempo muerto = intervalo entre el ingreso del tecnico a tienda (objetivo: '
                "9:30 PM) y el cierre de caja del sistema anterior (objetivo: maximo 10:30 PM). Barras por encima "
                "de la linea punteada superaron la ventana objetivo de 60 minutos.</span>",
                unsafe_allow_html=True,
            )
        else:
            st.info("No hay tiendas migradas con datos de tiempo en el filtro seleccionado.")

    with col_b:
        st.markdown('<div class="section-title">Tendencia de tiempo muerto promedio por dia</div>', unsafe_allow_html=True)
        trend = (
            cron_f[cron_f["downtime_min"].notna()]
            .groupby(cron_f["fecha"].dt.date)["downtime_min"]
            .mean()
            .reset_index()
        )
        if not trend.empty:
            fig = px.line(trend, x="fecha", y="downtime_min", markers=True, color_discrete_sequence=[PRIMARY])
            fig.add_hline(
                y=DOWNTIME_TARGET_MIN, line_dash="dot", line_color=RED,
                annotation_text=f"Objetivo: {DOWNTIME_TARGET_MIN} min", annotation_position="top left",
                annotation_font_color=RED,
            )
            fig.update_layout(height=380, yaxis_title="Minutos", xaxis_title="", **PLOTLY_LAYOUT)
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("Sin datos suficientes para la tendencia con el filtro actual.")

# ---------------------------------------------------------------------------
# TAB 3 — Incidencias
# ---------------------------------------------------------------------------
with tabs["Incidencias"]:
    col_a, col_b = st.columns([1.3, 1])
    with col_a:
        st.markdown('<div class="section-title">Incidencias mas frecuentes (Ola 0)</div>', unsafe_allow_html=True)
        inc_sorted = incidencias.sort_values("severidad_score", ascending=True)
        fig = px.bar(
            inc_sorted, x="severidad_score", y="incidencia", orientation="h", color="frecuencia",
            color_discrete_map={"Muy alta": RED, "Alta": PRIMARY, "Media": AMBER, "Baja": GREEN},
        )
        fig.update_layout(height=380, xaxis_title="Nivel de severidad (reportado)", yaxis_title="", **PLOTLY_LAYOUT)
        st.plotly_chart(fig, width='stretch')
        st.markdown(
            '<span class="note">Segun el informe "Resumen Migracion RMS a Xstore — Ola 0 y Ola 1". La escala de '
            "severidad es una traduccion numerica de las categorias cualitativas del informe (Muy alta=4 ... Baja=1) "
            "para fines de visualizacion.</span>",
            unsafe_allow_html=True,
        )

    with col_b:
        st.markdown('<div class="section-title">Tiendas con incidencias registradas</div>', unsafe_allow_html=True)
        con_obs = cron_f[(cron_f["estatus"] == "Migrada") & (cron_f["observaciones"] != "Sin observaciones")]
        sin_obs = cron_f[(cron_f["estatus"] == "Migrada") & (cron_f["observaciones"] == "Sin observaciones")]
        fig = px.pie(
            names=["Con incidencia", "Sin incidencia"],
            values=[len(con_obs), len(sin_obs)],
            color_discrete_sequence=[RED, GREEN],
            hole=0.55,
        )
        fig.update_traces(textinfo="label+percent", textfont_size=15)
        fig.update_layout(height=300, **PLOTLY_LAYOUT)
        st.plotly_chart(fig, width='stretch')

    st.markdown('<div class="section-title">Detalle de observaciones (filtro activo)</div>', unsafe_allow_html=True)
    st.dataframe(
        con_obs[["fecha", "nombre_tienda", "distrito", "tecnico", "observaciones"]].sort_values("fecha"),
        width='stretch',
        hide_index=True,
    )

# ---------------------------------------------------------------------------
# TAB 4 — Equipo tecnico
# ---------------------------------------------------------------------------
with tabs["Equipo tecnico"]:
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="section-title">Tiendas atendidas por tecnico (filtro activo)</div>', unsafe_allow_html=True)
        exploded = explode_tecnicos(cron_f[cron_f["estatus"] == "Migrada"])
        counts = exploded["tecnico_individual"].value_counts().reset_index()
        counts.columns = ["tecnico", "tiendas"]
        fig = px.bar(counts.sort_values("tiendas"), x="tiendas", y="tecnico", orientation="h", color_discrete_sequence=[PRIMARY])
        fig.update_layout(height=420, **PLOTLY_LAYOUT)
        st.plotly_chart(fig, width='stretch')

    with col_b:
        st.markdown('<div class="section-title">Modalidad del equipo tecnico</div>', unsafe_allow_html=True)
        mod_counts = tecnicos["modalidad"].value_counts().reset_index()
        mod_counts.columns = ["modalidad", "tecnicos"]
        fig = px.pie(mod_counts, names="modalidad", values="tecnicos", color_discrete_sequence=[PRIMARY, ACCENT], hole=0.55)
        fig.update_traces(textinfo="label+percent", textfont_size=15)
        fig.update_layout(height=320, **PLOTLY_LAYOUT)
        st.plotly_chart(fig, width='stretch')
        st.markdown('<div class="section-title" style="margin-top:16px;">Roster</div>', unsafe_allow_html=True)
        st.dataframe(tecnicos, width='stretch', hide_index=True)

# ---------------------------------------------------------------------------
# TAB — Finanzas (oculta al cliente por defecto — ver SHOW_FINANZAS al inicio
# del archivo; el proveedor cubre pasajes/movilidad y esta info no se expone).
# ---------------------------------------------------------------------------
if SHOW_FINANZAS:
    with tabs["Finanzas"]:
        gasto_total = gastos["monto"].sum()
        ingreso_total = ingresos["monto"].sum()
        c1, c2, c3 = st.columns(3)
        with c1:
            kpi_card("Gastos operativos registrados", f"S/ {gasto_total:,.2f}", f"{len(gastos)} movimientos")
        with c2:
            kpi_card("Ingresos registrados (Yape)", f"S/ {ingreso_total:,.2f}", f"{len(ingresos)} movimientos")
        with c3:
            saldo = ingreso_total - gasto_total
            color = GREEN if saldo >= 0 else RED
            kpi_card("Saldo de caja chica", f"S/ {saldo:,.2f}", "Ingresos - Gastos")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<div class="section-title">Gasto diario por categoria</div>', unsafe_allow_html=True)
            daily_gasto = gastos.groupby([gastos["fecha"].dt.date, "descripcion"])["monto"].sum().reset_index()
            daily_gasto.columns = ["fecha", "categoria", "monto"]
            fig = px.bar(
                daily_gasto, x="fecha", y="monto", color="categoria", barmode="stack",
                color_discrete_sequence=PALETTE,
            )
            fig.update_layout(height=340, **PLOTLY_LAYOUT)
            st.plotly_chart(fig, width='stretch')

        with col_b:
            st.markdown('<div class="section-title">Distribucion del gasto por categoria</div>', unsafe_allow_html=True)
            cat = gastos.groupby("descripcion")["monto"].sum().reset_index().sort_values("monto", ascending=False)
            fig = px.pie(cat, names="descripcion", values="monto", color_discrete_sequence=PALETTE, hole=0.5)
            fig.update_traces(textinfo="label+percent", textfont_size=15)
            fig.update_layout(height=340, **PLOTLY_LAYOUT)
            st.plotly_chart(fig, width='stretch')

        st.markdown('<div class="section-title">Detalle de movimientos</div>', unsafe_allow_html=True)
        col_g, col_i = st.columns(2)
        with col_g:
            st.caption("Gastos")
            st.dataframe(gastos, width='stretch', hide_index=True)
        with col_i:
            st.caption("Ingresos")
            st.dataframe(ingresos, width='stretch', hide_index=True)

# ---------------------------------------------------------------------------
# TAB 6 — Detalle de tiendas
# ---------------------------------------------------------------------------
with tabs["Detalle de tiendas"]:
    st.markdown('<div class="section-title">Buscador de tiendas</div>', unsafe_allow_html=True)
    search = st.text_input("Buscar por nombre de tienda, distrito o tecnico")
    view = cron_f.copy()
    if search:
        s = search.lower()
        view = view[
            view["nombre_tienda"].str.lower().str.contains(s, na=False)
            | view["distrito"].str.lower().str.contains(s, na=False)
            | view["tecnico"].str.lower().str.contains(s, na=False)
        ]

    st.dataframe(
        view[
            [
                "fecha", "nombre_tienda", "distrito", "tecnico", "coordinador", "estatus",
                "ingreso", "cierre_caja", "inicio_xstore", "fin_xstore", "downtime_min", "observaciones",
            ]
        ].sort_values("fecha"),
        width='stretch',
        hide_index=True,
        column_config={
            "downtime_min": st.column_config.NumberColumn("Tiempo muerto (min)", format="%.0f"),
        },
    )
    st.download_button(
        "Descargar vista filtrada (CSV)",
        data=view.to_csv(index=False).encode("utf-8"),
        file_name="cronograma_filtrado.csv",
        mime="text/csv",
    )
