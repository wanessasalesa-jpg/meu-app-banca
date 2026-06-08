import streamlit as st
import gspread
import pandas as pd
import json

st.title("Sistema Crivo - Conexão Direta")

# Carrega as credenciais do Secrets
# Você precisará colocar o seu JSON lá dentro como uma string única
try:
    credentials_dict = json.loads(st.secrets["gcp_service_account"])
    
    # Conexão
    gc = gspread.service_account_from_dict(credentials_dict)
    sh = gc.open_by_url("SUA_URL_DA_PLANILHA_AQUI")
    worksheet = sh.worksheet("Escalacao")
    
    data = worksheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])
    
    st.success("Conexão direta estabelecida!")
    st.dataframe(df)
    
except Exception as e:
    st.error(f"Erro na conexão: {e}")
