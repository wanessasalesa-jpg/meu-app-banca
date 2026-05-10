import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO E CONEXÃO ---
# O Streamlit tem uma função nativa para conectar com Google Sheets
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Avaliação Afya Marabá", layout="wide")

# Conectando à sua planilha (necessário configurar o link no Streamlit Cloud)
conn = st.connection("gsheets", type=GSheetsConnection)
df_escalacao = conn.read(worksheet="Escalacao")

st.title("🎓 Portal do Avaliador - Afya")

# --- LOGIN / IDENTIFICAÇÃO ---
lista_professores = df_escalacao["Avaliador"].unique()
professor_logado = st.selectbox("Selecione seu nome para ver suas bancas de hoje:", [""] + list(lista_professores))

if professor_logado:
    # FILTRANDO OS GRUPOS DO DIA PARA ESTE PROFESSOR
    meus_grupos = df_escalacao[df_escalacao["Avaliador"] == professor_logado]
    
    st.write(f"### Olá, Prof. {professor_logado}! Você tem {len(meus_grupos)} bancas hoje.")
    
    # SELEÇÃO DO GRUPO
    # O avaliador só vê os títulos dos trabalhos dele
    escolha_grupo = st.selectbox("Selecione o grupo para iniciar a avaliação:", 
                                 meus_grupos["Título"].tolist())
    
    if escolha_grupo:
        dados_grupo = meus_grupos[meus_grupos["Título"] == escolha_grupo].iloc[0]
        
        # Mostra os dados que VOCÊ já cadastrou
        st.info(f"**Turma:** {dados_grupo['Turma']}  |  **Horário:** {dados_grupo['Horário']}")
        st.write(f"**Integrantes:** {dados_grupo['Alunos']}")
        
        st.divider()
        
        # Aqui entra a lógica das rubricas (que já fizemos anteriormente)
        # O app já sabe qual a turma (TCC I, MCM V, etc.) através do 'dados_grupo'
        turma_atual = dados_grupo['Turma']
        
        # --- (O código das rubricas que te passei antes entra aqui, 
        #      usando a variável 'turma_atual' para decidir qual ficha mostrar) ---
        
        # BOTÃO PARA SALVAR
        if st.button("Finalizar Avaliação e Enviar Notas"):
            # Lógica para escrever de volta na planilha
            st.success(f"Avaliação do grupo {escolha_grupo} enviada com sucesso!")
            st.balloons()
