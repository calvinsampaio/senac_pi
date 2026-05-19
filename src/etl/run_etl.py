"""
src/etl/run_etl.py

ETL robusto para o projeto senac_pi:
- lê CSVs em data/raw (casos.csv, pacientes.csv, municipios.csv)
- normaliza colunas e tipos
- remove duplicidades e aplica mapeamentos categóricos
- gera features temporais e faixa etária padronizada
- grava artefatos em data/processed/ e um resumo em etl_summary.json

Uso:
    python src/etl/run_etl.py
"""
from pathlib import Path
import pandas as pd
import numpy as np
import sys
import json
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Arquivos esperados
CASOS_CSV = RAW_DIR / "casos.csv"
PACIENTES_CSV = RAW_DIR / "pacientes.csv"
MUNICIPIOS_CSV = RAW_DIR / "municipios.csv"

# Leitura
CSV_SEP = ";"
DEFAULT_ENCODING = "latin-1"

def read_csv_if_exists(path: Path, parse_dates=None, dtype=None):
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path, sep=CSV_SEP, dtype=dtype or str, low_memory=False, header=1, encoding=DEFAULT_ENCODING)
        if parse_dates:
            for col in parse_dates:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
        return df
    except Exception as e:
        print(f"[ERROR] Falha ao ler {path}: {e}")
        raise

def snake_case_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [
        str(c).strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        for c in df.columns
    ]
    return df

def ensure_date_columns(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], dayfirst=True, errors='coerce')
    return df

def compute_date_features(df: pd.DataFrame):
    if 'dt_notific' in df.columns:
        df['ano'] = df['dt_notific'].dt.year
        df['mes'] = df['dt_notific'].dt.month
    if 'dt_notific' in df.columns and 'dt_sin_pri' in df.columns:
        df['dias_ate_notif'] = (df['dt_notific'] - df['dt_sin_pri']).dt.days
    return df

def normalize_sexo(df: pd.DataFrame):
    if 'sexo' in df.columns:
        df['sexo'] = df['sexo'].astype(str).str.strip().str.upper().replace({
            'M': 'M', 'F': 'F', 'I': 'IGNORADO', '': 'IGNORADO', 'NAO INFORMADO': 'IGNORADO', 'NÃO INFORMADO': 'IGNORADO', 'NONE': 'IGNORADO', 'NAN': 'IGNORADO'
        })
    return df

def normalize_uf(df: pd.DataFrame):
    if 'uf' in df.columns:
        df['uf'] = df['uf'].astype(str).str.strip().str.upper()
    return df

def normalize_text_cols(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().replace({'nan': None, 'None': None})
    return df

def standardize_faixa_etaria(df: pd.DataFrame):
    if 'faixa_etaria' not in df.columns and 'idade' in df.columns:
        def map_idade(x):
            try:
                if pd.isna(x):
                    return 'ignorado'
                x = float(x)
            except Exception:
                return 'ignorado'
            if x < 5:
                return '<5a'
            if 5 <= x <= 11:
                return '5-11a'
            if 12 <= x <= 17:
                return '12-17a'
            if 18 <= x <= 29:
                return '18-29a'
            if 30 <= x <= 44:
                return '30-44a'
            if 45 <= x <= 59:
                return '45-59a'
            return '60+a'
        df['faixa_etaria'] = df['idade'].apply(map_idade).astype('string')
    else:
        if 'faixa_etaria' in df.columns:
            df['faixa_etaria'] = df['faixa_etaria'].astype(str).str.strip().str.replace(" ", "").str.lower().replace({'nan': 'ignorado'})
    return df

def basic_quality_checks(df: pd.DataFrame, name: str):
    checks = {}
    checks['rows'] = int(df.shape[0])
    checks['cols'] = int(df.shape[1])
    checks['null_percent'] = (df.isna().mean() * 100).round(2).to_dict()
    if 'id_caso' in df.columns:
        dup_count = int(df['id_caso'].duplicated().sum())
        checks['duplicated_id_caso'] = dup_count
    if 'id_paciente' in df.columns:
        dup_p = int(df['id_paciente'].duplicated().sum())
        checks['duplicated_id_paciente'] = dup_p
    print(f"[QA] {name}: rows={checks['rows']} cols={checks['cols']} duplicated_id_caso={checks.get('duplicated_id_caso', 'n/a')}")
    nulls = sorted(checks['null_percent'].items(), key=lambda x: -x[1])[:10]
    print(f"[QA] {name} top nulls: {nulls}")
    return checks

def save_parquet(df: pd.DataFrame, path: Path):
    try:
        df.to_parquet(path, index=False)
        print(f"[SAVE] Gravado {path} ({len(df)} registros)")
    except Exception as e:
        print(f"[ERROR] Falha ao salvar {path}: {e}")
        raise

def clean_casos(df: pd.DataFrame):
    df = df.copy()
    # Trim strings
    str_cols = [c for c in ['id_caso','id_paciente','municipio','bairro','classi_fin','evolucao','sorotipo','tipo_notif'] if c in df.columns]
    for c in str_cols:
        df[c] = df[c].astype(str).str.strip().replace({'nan': None, 'None': None})

    initial_rows = len(df)

    # Remove duplicatas por id_caso
    removed_dup = 0
    if 'id_caso' in df.columns:
        dup_mask = df['id_caso'].duplicated(keep='first')
        removed_dup = int(dup_mask.sum())
        if removed_dup > 0:
            df = df[~dup_mask].reset_index(drop=True)

    # Casting numéricos
    if 'idade' in df.columns:
        df['idade'] = pd.to_numeric(df['idade'], errors='coerce').astype('Int64')
    if 'dias_internacao' in df.columns:
        df['dias_internacao'] = pd.to_numeric(df['dias_internacao'], errors='coerce').astype('Int16')
    if 'dias_ate_notif' in df.columns:
        df['dias_ate_notif'] = pd.to_numeric(df['dias_ate_notif'], errors='coerce').astype('Int16')

    # Mapear booleanos
    bool_map = {
        'sim': True, 's': True, 'yes': True, 'y': True, '1': True,
        'nao': False, 'n': False, 'no': False, '0': False, 'não': False, 'nao ': False
    }
    for col in ['hospitalizado','caso_grave','obito']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower().map(bool_map).astype('boolean')

    # Padronizar evolucao
    evol_map = {'cura':'Cura', 'óbito':'Obito', 'obito':'Obito', 'em tratamento':'Em Tratamento', 'ignorado':'Ignorado'}
    if 'evolucao' in df.columns:
        df['evolucao'] = df['evolucao'].astype(str).str.strip().str.lower().map(evol_map).fillna(df['evolucao'])

    # Sexo e faixa etaria política de nulos
    if 'sexo' in df.columns:
        df['sexo'] = df['sexo'].fillna('IGNORADO')
    if 'faixa_etaria' in df.columns:
        df['faixa_etaria'] = df['faixa_etaria'].fillna('ignorado')

    final_rows = len(df)
    summary = {
        'initial_rows': int(initial_rows),
        'final_rows': int(final_rows),
        'removed_duplicates': int(removed_dup)
    }
    print(f"[CLEAN] casos: {summary}")
    return df, summary

def clean_pacientes(df: pd.DataFrame):
    df = df.copy()
    str_cols = [c for c in ['id_paciente','raca_cor','escolaridade','ocupacao','zona','comorbidade'] if c in df.columns]
    for c in str_cols:
        df[c] = df[c].astype(str).str.strip().replace({'nan': None, 'None': None})
    initial_rows = len(df)
    if 'dt_nascimento' in df.columns and 'idade' not in df.columns:
        today = pd.Timestamp('today')
        df['dt_nascimento'] = pd.to_datetime(df['dt_nascimento'], dayfirst=True, errors='coerce')
        df['idade'] = ((today - df['dt_nascimento']).dt.days // 365).astype('Int64')
    if 'idade' in df.columns:
        df['idade'] = pd.to_numeric(df['idade'], errors='coerce').astype('Int64')
    if 'sexo' in df.columns:
        df['sexo'] = df['sexo'].astype(str).str.strip().str.upper().replace({'M':'M','F':'F','I':'IGNORADO','':'IGNORADO'})
    final_rows = len(df)
    summary = {'initial_rows': int(initial_rows), 'final_rows': int(final_rows)}
    print(f"[CLEAN] pacientes: {summary}")
    return df, summary

def clean_municipios(df: pd.DataFrame):
    df = df.copy()
    for c in ['municipio','uf','estado','regiao']:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()

    # Converter colunas numéricas com formato brasileiro (ex: "5.263.791" ou "710,2")
    numeric_candidates = [c for c in ['populacao','area_km2','densidade_hab_km2','total_casos','casos_graves','obitos','incidencia_100k','tx_letalidade_pct'] if c in df.columns]
    for c in numeric_candidates:
        df[c] = df[c].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df[c] = pd.to_numeric(df[c], errors='coerce')

    summary = {'rows': int(len(df))}
    print(f"[CLEAN] municipios: {summary}")
    return df, summary

def run_etl():
    summary = {'timestamp': datetime.utcnow().isoformat(), 'files': {}}

    # CASOS
    df_casos = read_csv_if_exists(CASOS_CSV, parse_dates=['DT_NOTIFIC','DT_SIN_PRI'])
    if df_casos is None:
        print(f"[WARN] {CASOS_CSV} não encontrado. Coloque um CSV em data/raw/ e rode novamente.")
    else:
        df_casos = snake_case_columns(df_casos)
        df_casos = ensure_date_columns(df_casos, ['dt_notific','dt_sin_pri'])
        df_casos = compute_date_features(df_casos)
        df_casos = normalize_sexo(df_casos)
        df_casos = normalize_uf(df_casos)
        df_casos = normalize_text_cols(df_casos, ['classi_fin','evolucao','sorotipo','tipo_notif','municipio','bairro'])
        df_casos = standardize_faixa_etaria(df_casos)
        df_casos, clean_summary = clean_casos(df_casos)
        checks = basic_quality_checks(df_casos, 'casos')
        # atualizar summary com clean_summary
        checks.update(clean_summary)
        summary['files']['casos'] = checks
        out_casos = PROCESSED_DIR / "casos_tratados.parquet"
        save_parquet(df_casos, out_casos)

    # PACIENTES
    df_pac = read_csv_if_exists(PACIENTES_CSV, parse_dates=['DT_NASCIMENTO'])
    if df_pac is not None:
        df_pac = snake_case_columns(df_pac)
        df_pac = ensure_date_columns(df_pac, ['dt_nascimento'])
        df_pac = normalize_sexo(df_pac)
        df_pac = normalize_text_cols(df_pac, ['raca_cor','escolaridade','ocupacao','zona','comorbidade'])
        df_pac, pac_summary = clean_pacientes(df_pac)
        checks_pac = basic_quality_checks(df_pac, 'pacientes')
        checks_pac.update(pac_summary)
        summary['files']['pacientes'] = checks_pac
        out_pac = PROCESSED_DIR / "pacientes_tratados.parquet"
        save_parquet(df_pac, out_pac)
    else:
        print("[INFO] pacientes.csv não encontrado — pulando etapa pacientes.")

    # MUNICIPIOS
    df_mun = read_csv_if_exists(MUNICIPIOS_CSV)
    if df_mun is not None:
        df_mun = snake_case_columns(df_mun)
        df_mun = normalize_text_cols(df_mun, ['municipio','uf','estado','regiao'])
        df_mun, mun_summary = clean_municipios(df_mun)
        checks_mun = basic_quality_checks(df_mun, 'municipios')
        checks_mun.update(mun_summary)
        summary['files']['municipios'] = checks_mun
        out_mun = PROCESSED_DIR / "municipios_tratados.parquet"
        save_parquet(df_mun, out_mun)
    else:
        print("[INFO] municipios.csv não encontrado — pulando etapa municipios.")

    # salvar resumo
    summary_path = PROCESSED_DIR / "etl_summary.json"
    try:
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"[SUMMARY] Resumo do ETL salvo em {summary_path}")
    except Exception as e:
        print(f"[ERROR] Falha ao salvar resumo: {e}")

    print("[DONE] ETL finalizado.")

if __name__ == "__main__":
    try:
        run_etl()
    except Exception as exc:
        print(f"[FATAL] ETL abortado: {exc}")
        sys.exit(1)