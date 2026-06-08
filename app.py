import streamlit as st
from google.oauth2 import service_account
import gspread

st.title("Sistema Crivo")

# Carrega as credenciais a partir das variáveis de ambiente (Secrets)
try:
    # A variável 'gcp_service_account' deve estar configurada no seu Secrets
    creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
    gc = gspread.authorize(creds)
    
    # Abre a planilha
    sh = gc.open_by_url("SUA_URL_DA_PLANILHA")
    worksheet = sh.worksheet("Escalacao")
    
    st.success("Conexão estabelecida!")
    st.write(worksheet.get_all_values())
except Exception as e:
    st.error(f"Erro na conexão: {e}")
