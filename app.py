import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.title("Sistema Crivo")

try:
    # Cria o dicionário de credenciais usando os campos do Secrets
    creds_dict = {
        "type": st.secrets["type"],
        "project_id": st.secrets["project_id"],
        "private_key_id": st.secrets["private_key_id"],
        "private_key": st.secrets["private_key"],
        "client_email": st.secrets["client_email"],
        "client_id": st.secrets["client_id"],
        "auth_uri": st.secrets["auth_uri"],
        "token_uri": st.secrets["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["client_x509_cert_url"]
    }
    
    # Autoriza e conecta
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    gc = gspread.authorize(creds)
    
    sh = gc.open_by_url("COLE_AQUI_A_URL_DA_PLANILHA")
    st.success("Conexão estável!")
except Exception as e:
    st.error(f"Erro: {e}")
