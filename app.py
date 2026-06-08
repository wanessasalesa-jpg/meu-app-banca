import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="CRIVO - Gestão", layout="centered")

# CSS para o estilo que você gosta
st.markdown("""
    <style>
    .stButton button {
        width: 100%; border-radius: 10px; height: 3.5em;
        background-color: #002147; color: white; font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎓 CRIVO")

# Conexão com a planilha (usando o Secrets que já configuramos)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Escalacao", ttl=0)
    
    st.success("Conectado com sucesso!")
    st.write("Dados da Escalacao carregados:")
    st.dataframe(df.head())
    
except Exception as e:
    st.error(f"Erro ao ler a planilha: {e}")
