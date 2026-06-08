import streamlit as st
import subprocess
import sys

# Tenta garantir que a biblioteca esteja instalada
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    st.write("Instalando dependências...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit-gsheets"])
    from streamlit_gsheets import GSheetsConnection

st.title("Sistema Crivo - Conexão Final")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Escalacao", ttl=0)
    st.success("Conexão estabelecida com sucesso!")
    st.dataframe(df.head())
except Exception as e:
    st.error(f"Erro na conexão: {e}")
