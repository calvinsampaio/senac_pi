# src/dashboard/app.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import streamlit as st
from src.dashboard.utils import load_casos

st.set_page_config(page_title="Dengue SENAC PI", layout="wide")
st.title("Dengue SENAC PI")

# Carregar dados
df = load_casos()
if df is None:
    st.warning("Dados processados não encontrados. Rode: python src/etl/run_etl.py")
    st.stop()

# Normalizar nomes de colunas possíveis (compatibilidade)
# Ex.: sg_uf_not (SINAN) ou uf (padronizado)
if 'sg_uf_not' in df.columns and 'uf' not in df.columns:
    df = df.rename(columns={'sg_uf_not': 'uf'})

# Garantir colunas que usaremos
available_cols = set(df.columns)

# Filtros (com proteção caso coluna não exista)
col1, col2, col3, col4 = st.columns([3,2,2,2])
with col1:
    anos = sorted(df['ano'].dropna().unique().tolist()) if 'ano' in df.columns else []
    ano = st.selectbox("Ano", options=[None] + anos)
with col2:
    ufs = sorted(df['uf'].dropna().unique().tolist()) if 'uf' in df.columns else []
    uf = st.selectbox("UF", options=[None] + ufs)
with col3:
    sexos = sorted(df['sexo'].dropna().unique().tolist()) if 'sexo' in df.columns else []
    sexo = st.selectbox("Sexo", options=[None] + sexos)
with col4:
    faixas = sorted(df['faixa_etaria'].dropna().unique().tolist()) if 'faixa_etaria' in df.columns else []
    faixa = st.selectbox("Faixa Etária", options=[None] + faixas)

# Aplicar filtros de forma defensiva
q = df.copy()
if ano is not None and 'ano' in q.columns:
    q = q[q['ano'] == ano]
if uf is not None and 'uf' in q.columns:
    q = q[q['uf'] == uf]
if sexo is not None and 'sexo' in q.columns:
    q = q[q['sexo'] == sexo]
if faixa is not None and 'faixa_etaria' in q.columns:
    q = q[q['faixa_etaria'] == faixa]

# KPIs e mensagens quando vazio
c1, c2, c3 = st.columns(3)
c1.metric("Total de registros", int(q.shape[0]))
if q.shape[0] == 0:
    st.warning("Nenhum registro encontrado com os filtros atuais.")
    st.stop()

# Últimos 12 meses
if 'dt_notific' in q.columns and pd.api.types.is_datetime64_any_dtype(q['dt_notific']):
    max_date = q['dt_notific'].max()
    last12 = q[q['dt_notific'] >= (max_date - pd.Timedelta(days=365))]
    c2.metric("Últimos 12 meses", int(last12.shape[0]))
else:
    c2.metric("Últimos 12 meses", "N/A")

# Óbitos (se coluna evolucao existir)
if 'evolucao' in q.columns:
    obitos = int(q['evolucao'].astype(str).str.lower().str.strip().isin(['óbito','obito','obituário','obituario','obito ']).sum())
    c3.metric("Óbitos", obitos)
else:
    c3.metric("Óbitos", "N/A")

# Série temporal (ano x contagem)
if 'ano' in q.columns:
    st.subheader("Casos por ano")
    series = q.groupby('ano').size().sort_index()
    st.line_chart(series)
else:
    st.info("Coluna 'ano' não disponível para série temporal.")

# Tabela amostra e download
st.subheader("Amostra dos dados (até 200 linhas)")
st.dataframe(q.head(200))

# Download CSV da seleção
csv = q.to_csv(index=False).encode('utf-8')
st.download_button("Baixar seleção CSV", csv, "casos_selecao.csv", "text/csv")

# Se quiser, mostrar resumo do ETL
summary_path = Path(__file__).resolve().parents[2] / "data" / "processed" / "etl_summary.json"
if summary_path.exists():
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = f.read()
    with st.expander("Resumo do ETL (etl_summary.json)"):
        st.code(summary)
