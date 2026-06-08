import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Configuração básica
st.set_page_config(page_title="CRIVO - Teste de Conexão")

# Tenta conectar
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Escalacao", ttl=0)
    st.success("Conexão realizada! A planilha foi encontrada.")
    st.write(df.head()) # Mostra as primeiras linhas para confirmar que os dados chegaram
except Exception as e:
    st.error(f"Erro ao conectar: {e}")
    st.write("Se o erro persistir, verifique se o link da planilha no Secrets está correto.")
