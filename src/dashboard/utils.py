# src/dashboard/utils.py
from pathlib import Path
import pandas as pd
import streamlit as st

PROCESSED = Path(__file__).resolve().parents[2] / "data" / "processed"
CASOS_PATH = PROCESSED / "casos_tratados.parquet"

@st.cache_data(ttl=3600)
def load_casos(path: Path = CASOS_PATH) -> pd.DataFrame | None:
    """
    Carrega o Parquet de casos com cache. Retorna None se o arquivo não existir.
    TTL 1h para forçar recarga eventual após ETL.
    """
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    # garantir colunas mínimas e tipos básicos
    if 'ano' in df.columns:
        df['ano'] = pd.to_numeric(df['ano'], errors='coerce').astype('Int64')
    if 'dt_notific' in df.columns:
        df['dt_notific'] = pd.to_datetime(df['dt_notific'], errors='coerce', infer_datetime_format=True)
    return df

