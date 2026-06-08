import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("Sistema Crivo - Conexão Direta")

# Aqui o sistema vai ler a chave que você vai colocar no Secrets
try:
    # Se você ainda tiver o seu JSON, vamos usá-lo
    # Caso contrário, vamos tentar apenas o link
    st.write("Tentando conectar...")
    # O código abaixo é apenas um teste de vida
    st.success("O sistema está rodando!")
except Exception as e:
    st.error(f"Erro: {e}")
