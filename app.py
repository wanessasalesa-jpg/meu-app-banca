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

# FUNÇÃO SEGURA PARA MAPEAR COLUNAS IGNORANDO MAIÚSCULAS/MINÚSCULAS
def obter_nome_real_coluna(df, nome_desejado):
    for col in df.columns:
        if str(col).strip().lower() == str(nome_desejado).strip().lower():
            return col
    return None

def checar_email_na_coluna(email, df, coluna_alvo):
    coluna_real = obter_nome_real_coluna(df, coluna_alvo)
    if not coluna_real:
        return False
    return email in df[coluna_real].astype(str).str.strip().str.lower().unique()

def obter_valor_coluna(df_linha, coluna_alvo):
    for col in df_linha.index:
        if str(col).strip().lower() == str(coluna_alvo).strip().lower():
            return df_linha[col]
    return ""

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
    c_orientador = obter_real_coluna := obter_nome_real_coluna(df_escalacao, 'orientador')
    c_email_or = obter_nome_real_coluna(df_escalacao, 'email_orientador')
    nome_completo_docente = df_escalacao[df_escalacao[c_email_or].astype(str).str.lower() == email_user][c_orientador].iloc[0]
elif checar_email_na_coluna(email_user, df_escalacao, 'Email_Avaliador_1'):
    eh_banca = True
    c_av1 = obter_nome_real_coluna(df_escalacao, 'avaliador_1')
    c_email_av1 = obter_nome_real_coluna(df_escalacao, 'email_avaliador_1')
    nome_completo_docente = df_escalacao[df_escalacao[c_email_av1].astype(str).str.lower() == email_user][c_av1].iloc[0]
elif checar_email_na_coluna(email_user, df_escalacao, 'Email_Avaliador_2'):
    eh_banca = True
    c_av2 = obter_nome_real_coluna(df_escalacao, 'avaliador_2')
    c_email_av2 = obter_nome_real_coluna(df_escalacao, 'email_avaliador_2')
    nome_completo_docente = df_escalacao[df_escalacao[c_email_av2].astype(str).str.lower() == email_user][c_av2].iloc[0]
elif checar_email_na_coluna(email_user, df_escalacao, 'Email_suplente'):
    eh_banca = True
    c_sup = obter_nome_real_coluna(df_escalacao, 'avaliador_suplente')
    c_email_sup = obter_nome_real_coluna(df_escalacao, 'email_suplente')
    nome_completo_docente = df_escalacao[df_escalacao[c_email_sup].astype(str).str.lower() == email_user][c_sup].iloc[0]

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
c_alunos = obter_nome_real_coluna(df_escalacao, 'alunos')

if not df_escalacao.empty and c_alunos:
    if eh_orientador:
        c_email_or = obter_nome_real_coluna(df_escalacao, 'email_orientador')
        possiveis = df_escalacao[df_escalacao[c_email_or].astype(str).str.lower() == email_user].copy()
        linhas_pendentes = []
        for idx, row in possiveis.iterrows():
            alunos_grupo = [a.strip() for a in str(row[c_alunos]).split(",") if a.strip()]
            avaliados = df_respostas[(df_respostas["Email_Avaliador"] == email_user) & (df_respostas["Papel"] == "Orientador")]["Alunos"].tolist()
            alunos_restantes = [a for a in alunos_grupo if a not in avaliados]
            
            if alunos_restantes:
                linhas_pendentes.append(row)
        if linhas_pendentes:
            pendentes = pd.DataFrame(linhas_pendentes)
    else:
        c_em_av1 = obter_nome_real_coluna(df_escalacao, 'email_avaliador_1')
        c_em_av2 = obter_nome_real_coluna(df_escalacao, 'email_avaliador_2')
        c_em_sup = obter_nome_real_coluna(df_escalacao, 'email_suplente')
        
        cond_banca = (
            (df_escalacao[c_em_av1].astype(str).str.lower() == email_user) | 
            (df_escalacao[c_em_av2].astype(str).
