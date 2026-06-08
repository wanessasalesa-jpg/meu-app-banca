import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("Teste de Conexão")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Escalacao", ttl=0)
    st.success("Conexão feita! A planilha foi lida com sucesso.")
    st.write(df.head())
except Exception as e:
    st.error(f"Erro ao conectar: {e}")
