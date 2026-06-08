import streamlit as st
import gspread
import base64
import json

st.title("Sistema Crivo")

try:
    # Decodifica a string Base64 de volta para JSON
    creds_b64 = st.secrets["GCP_CREDENTIALS_B64"]
    creds_json = json.loads(base64.b64decode(creds_b64).decode('utf-8'))
    
    # Conecta
    gc = gspread.service_account_from_dict(creds_json)
    sh = gc.open_by_url("SUA_URL_DA_PLANILHA_AQUI")
    
    st.success("Conexão estabelecida!")
    st.write("Dados lidos com sucesso.")
    
except Exception as e:
    st.error(f"Erro: {e}")
