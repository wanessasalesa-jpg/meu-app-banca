import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="CRIVO", layout="centered")

# Conexão direta usando as configurações do Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

# Tenta ler a aba principal
try:
    df_escalacao = conn.read(worksheet="Escalacao", ttl=0)
    st.success("Conexão com a planilha estabelecida com sucesso!")
    st.write(df_escalacao.head())
except Exception as e:
    st.error(f"Erro ao conectar na planilha: {e}")
    st.write("Verifica se as Secrets estão configuradas corretamente no Streamlit Cloud.")
