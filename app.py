import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.title("CRIVO - Teste de Conexão")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Escalacao", ttl=0)
    st.success("Conectado com sucesso!")
    st.write(df.head())
except Exception as e:
    st.error(f"Erro: {e}")
