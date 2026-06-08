import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.title("Sistema Crivo - Restauração")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Escalacao", ttl=0)
    st.success("Conexão estabelecida com sucesso!")
    st.write(df.head())
except Exception as e:
    st.error(f"Erro: {e}")
