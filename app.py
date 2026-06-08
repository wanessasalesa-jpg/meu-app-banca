import streamlit as st

st.title("Teste de Conexão")

try:
    conn = st.connection("gsheets", type="gsheets")
    df = conn.read(worksheet="Escalacao", ttl=0)
    st.success("Conexão feita! A planilha foi lida.")
    st.write(df.head())
except Exception as e:
    st.error(f"Erro detectado: {e}")
