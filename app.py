import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta
import time
import pytz 

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CRIVO - Gestão Acadêmica", layout="centered")

# 2. FUSO HORÁRIO DE BRASÍLIA
fuso_bruta = pytz.timezone('America/Sao_Paulo')

def obter_agora():
    return datetime.now(fuso_bruta)

# FUNÇÃO PARA ENCURTAR NOMES NA EXIBIÇÃO DO APP
def tratar_nome_curto(nome_completo):
    if not nome_completo or pd.isna(nome_completo):
        return ""
    partes = str(nome_completo).strip().split()
    if len(partes) > 1:
        return f"{partes[0]} {partes[1]}"
    return partes[0]

# FUNÇÃO SEGURA PARA CHECAR E-MAIL LOWERCASE NA COLUNA (EVITA ATTRIBUTEERROR)
def checar_email_na_coluna(email, df, coluna):
    if coluna not in df.columns:
        return False
    return email in df[coluna].astype(str).str.strip().str.lower().unique()

# 3. CONEXÃO COM GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(aba, ttl_sec=2):
    return conn.read(worksheet=aba, ttl=ttl_sec)

try:
    df_escalacao = get_data("Escalacao", ttl_sec=300)
except:
    st.error("Conectando ao banco de dados... Aguarde.")
    time.sleep(1)
    st.rerun()

# --- TRATAMENTO SEGURO DA ABA DE RESPOSTAS ---
colunas_respostas_obrigatorias = ["Avaliador", "Email_Avaliador", "Alunos", "Nota_Final", "Papel", "Data_Hora"]
try:
    df_respostas = get_data("Respostas", ttl_sec=0)
    if df_respostas.empty or not all(col in df_respostas.columns for col in colunas_respostas_obrigatorias):
        df_respostas = pd.DataFrame(columns=colunas_respostas_obrigatorias)
except:
    df_respostas = pd.DataFrame(columns=colunas_respostas_obrigatorias)

# --- TRAVA DE LOGOUT E IDENTIFICAÇÃO DE PAPEL ---
if 'email' not in st.session_state:
    if "user" in st.query_params:
        st.session_state.email = st.query_params["user"]

if 'email' not in st.session_state:
    st.title("🎓 CRIVO")
    st.subheader("Sistema de Gestão de Bancas Acadêmicas")
    st.caption("© 2026 Desenvolvido por Wanessa Sales de Almeida")
    st.divider()

    st.write("### Identificação do Docente")
    email_raw = st.text_input("Digite seu e-mail cadastrado:").strip()
    if st.button("Acessar Sistema"):
        if email_raw:
            email_limpo = email_raw.lower()
            
            id_banca1 = checar_email_na_coluna(email_limpo, df_escalacao, 'Email_Avaliador_1')
            id_banca2 = checar_email_na_coluna(email_limpo, df_escalacao, 'Email_Avaliador_2')
            id_suplente = checar_email_na_coluna(email_limpo, df_escalacao, 'Email_suplente')
            id_orienta = checar_email_na_coluna(email_limpo, df_escalacao, 'Email_Orientador')
            
            if id_banca1 or id_banca2 or id_suplente or id_orienta:
                st.session_state.email = email_limpo
                st.query_params["user"] = email_limpo
                st.rerun()
            else:
                st.error("E-mail não autorizado ou não encontrado na escalação.")
    st.stop()

# --- DEFINIÇÃO DO PAPEL LOGADO ---
email_user = st.session_state.email
eh_orientador = False
eh_banca = False
nome_completo_docente = ""

if checar_email_na_coluna(email_user, df_escalacao, 'Email_Orientador'):
    eh_orientador = True
    nome_completo_docente = df_escalacao[df_escalacao['Email_Orientador'].astype(str).str.lower() == email_user]['Orientador'].iloc[0]
elif checar_email_na_coluna(email_user, df_escalacao, 'Email_Avaliador_1'):
    eh_banca = True
    nome_completo_docente = df_escalacao[df_escalacao['Email_Avaliador_1'].astype(str).str.lower() == email_user]['Avaliador_1'].iloc[0]
elif checar_email_na_coluna(email_user, df_escalacao, 'Email_Avaliador_2'):
    eh_banca = True
    nome_completo_docente = df_escalacao[df_escalacao['Email_Avaliador_2'].astype(str).str.lower() == email_user]['Avaliador_2'].iloc[0]
elif checar_email_na_coluna(email_user, df_escalacao, 'Email_suplente'):
    eh_banca = True
    nome_completo_docente = df_escalacao[df_escalacao['Email_suplente'].astype(str).str.lower() == email_user]['Avaliador_Suplente'].iloc[0]

nome_exibicao = tratar_nome_curto(nome_completo_docente)

# --- DEFINIÇÃO DINÂMICA DE CORES (CSS) ---
cor_primaria = "#002147" if not eh_orientador else "#1b4d3e"
st.markdown(f"""
    <style>
    header {{visibility: hidden;}}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    .stButton button {{
        width: 100%;
        border-radius: 10px;
        height: 3.5em;
        background-color: {cor_primaria};
        color: white;
        font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

# CABEÇALHO DO APP APÓS LOGIN
st.title("🎓 CRIVO")
st.subheader("Sistema de Gestão de Bancas Acadêmicas" if not eh_orientador else "Sistema de Gestão de Orientações")
st.caption("© 2026 Desenvolvido por Wanessa Sales de Almeida")
st.divider()

col_user, col_exit = st.columns([3, 1])
with col_user:
    st.write(f"**Docente:** {nome_exibicao} ({'Orientador' if eh_orientador else 'Banca Examinadora'})")
with col_exit:
    if st.button("Sair"):
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()

# FILTRAGEM DE GRUPOS PENDENTES
pendentes = pd.DataFrame()
if not df_escalacao.empty:
    if eh_orientador:
        possiveis = df_escalacao[df_escalacao['Email_Orientador'].astype(str).str.lower() == email_user].copy()
        linhas_pendentes = []
        for idx, row in possiveis.iterrows():
            alunos_grupo = [a.strip() for a in str(row['Alunos']).split(",") if a.strip()]
            avaliados = df_respostas[(df_respostas["Email_Avaliador"] == email_user) & (df_respostas["Papel"] == "Orientador")]["Alunos"].tolist()
            alunos_restantes = [a for a in alunos_grupo if a not in avaliados]
            
            if alunos_restantes:
                linhas_pendentes.append(row)
        if linhas_pendentes:
            pendentes = pd.DataFrame(linhas_pendentes)
    else:
        cond_banca = (
            (df_escalacao['Email_Avaliador_1'].astype(str).str.lower() == email_user) | 
            (df_escalacao['Email_Avaliador_2'].astype(str).str.lower() == email_user) | 
            (df_escalacao['Email_suplente'].astype(str).str.lower() == email_user)
        )
        possiveis = df_escalacao[cond_banca].copy()
        items_feitos = df_respostas[(df_respostas["Email_Avaliador"] == email_user) & (df_respostas["Papel"] == "Banca")]["Alunos"].tolist()
        pendentes = possiveis[~possiveis['Alunos'].isin(items_feitos)].copy()

if pendentes.empty:
    st.balloons()
    st.success("🎉 Todas as suas avaliações pendentes foram concluídas!")
else:
    pendentes['Alunos_Curto'] = pendentes['Alunos'].apply(lambda x: ", ".join(
