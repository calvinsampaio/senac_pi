import streamlit as st
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"

st.set_page_config(page_title="Dashboard Dengue", layout="wide")
st.title("Dashboard de Análise de Casos de Dengue")
st.markdown("Dados fictícios — SINAN / Brasil 2000–2024")

@st.cache_data
def load_data():
    casos = pd.read_parquet(PROCESSED_DIR / "casos_tratados.parquet")
    pacientes = pd.read_parquet(PROCESSED_DIR / "pacientes_tratados.parquet")
    municipios = pd.read_parquet(PROCESSED_DIR / "municipios_tratados.parquet")
    return casos, pacientes, municipios

casos, pacientes, municipios = load_data()

st.sidebar.header("Filtros")

ufs = sorted(casos["sg_uf_not"].dropna().unique())
uf_sel = st.sidebar.multiselect("UF de Notificação", ufs, default=ufs)

anos = sorted(casos["ano"].dropna().unique().astype(int))
ano_sel = st.sidebar.slider("Ano", min(anos), max(anos), (min(anos), max(anos)))

classif = sorted(casos["classi_fin"].dropna().unique())
classif_sel = st.sidebar.multiselect("Classificação Final", classif, default=classif)

mask = (
    casos["sg_uf_not"].isin(uf_sel)
    & casos["ano"].between(*ano_sel)
    & casos["classi_fin"].isin(classif_sel)
)
casos_filt = casos[mask]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Casos", len(casos_filt))
col2.metric("Evolução para Óbito", int(casos_filt["obito"].sum()) if "obito" in casos_filt.columns else 0)
col3.metric("Casos Graves", int(casos_filt["caso_grave"].sum()) if "caso_grave" in casos_filt.columns else 0)
col4.metric("UF Distintas", casos_filt["sg_uf_not"].nunique())

st.subheader("Casos por Mês / Ano")
ts = casos_filt.groupby(["ano", "mes"]).size().reset_index(name="contagem")
ts["ano_mes"] = ts["ano"].astype(str) + "-" + ts["mes"].astype(str).str.zfill(2)
ts = ts.sort_values(["ano", "mes"])
st.bar_chart(ts.set_index("ano_mes")["contagem"])

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Casos por UF")
    uf_count = casos_filt["sg_uf_not"].value_counts()
    st.bar_chart(uf_count)

with col_b:
    st.subheader("Classificação Final")
    classif_count = casos_filt["classi_fin"].value_counts()
    st.bar_chart(classif_count)

st.subheader("Casos por Faixa Etária e Sexo")
if "faixa_etaria" in pacientes.columns and "sexo" in pacientes.columns:
    fe = pacientes.groupby(["faixa_etaria", "sexo"]).size().reset_index(name="contagem")
    pivot = fe.pivot(index="faixa_etaria", columns="sexo", values="contagem").fillna(0)
    st.bar_chart(pivot)
else:
    st.info("Dados de faixa etária/sexo não disponíveis nos pacientes.")

st.subheader("Top 10 Municípios por Casos")
top_mun = municipios.nlargest(10, "total_casos")[["municipio", "total_casos", "obitos"]].set_index("municipio")
st.bar_chart(top_mun)

st.subheader("Dados Brutos (amostra)")
with st.expander("Casos"):
    st.dataframe(casos_filt.head(100))
with st.expander("Pacientes"):
    st.dataframe(pacientes.head(100))
with st.expander("Municípios"):
    st.dataframe(municipios.head(100))
