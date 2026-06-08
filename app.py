import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="CRIVO - Teste")
st.title("Sistema Crivo - Teste de Conexão")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Escalacao", ttl=0)
    st.success("Conexão realizada com sucesso!")
    st.write(df.head())
except Exception as e:
    st.error(f"Erro na conexão: {e}")
    st.write("Verifique se as Secrets estão configuradas no painel do Streamlit Cloud.")
