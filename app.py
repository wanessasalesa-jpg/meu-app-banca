import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("Sistema de Bancas")

# Conexão Simples
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(worksheet="Escalacao", ttl=0)

st.success("Conectado com sucesso!")
st.write(df.head())
