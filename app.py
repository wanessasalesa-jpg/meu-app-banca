import streamlit as st
import gspread

st.title("Sistema Crivo")

try:
    # Lê as chaves individuais configuradas no Secrets
    creds = {
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
    
    gc = gspread.service_account_from_dict(creds)
    # Coloque a URL da planilha aqui:
    sh = gc.open_by_url("SUA_URL_DA_PLANILHA_AQUI")
    
    st.success("Conexão estabelecida!")
    st.write("Planilha conectada.")
except Exception as e:
    st.error(f"Erro na conexão: {e}")
