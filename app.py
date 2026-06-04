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

# FUNÇÃO SEGURA PARA CHECAR E-MAIL LOWERCASE ADAPTADA PARA IGNORAR CASE DO CABEÇALHO
def checar_email_na_coluna(email, df, coluna_alvo):
    # Procura a coluna mapeando o nome em minúsculo para evitar KeyError
    colunas_df = {col.lower().strip(): col for col in df.columns}
    coluna_real = colunas_df.get(coluna_alvo.lower().strip())
    if not coluna_real:
        return False
    return email in df[coluna_real].astype(str).str.strip().str.lower().unique()

# FUNÇÃO PARA RETORNAR O VALOR DE UMA COLUNA IGNORANDO CASE DO CABEÇALHO
def obter_valor_coluna(df_linha, coluna_alvo):
    colunas_linha = {col.lower().strip(): col for col in df_linha.index}
    coluna_real = colunas_linha.get(coluna_alvo.lower().strip())
    if not coluna_real:
        return ""
    return df_linha[coluna_real]

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
            id_suplente = checar_email_na_coluna(email_limpo, df_escalacao, 'Email_Suplente')
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

# Mapeamento dinâmico de cabeçalhos da escalação para evitar KeyError
colunas_esc = {col.lower().strip(): col for col in df_escalacao.columns}

if checar_email_na_coluna(email_user, df_escalacao, 'Email_Orientador'):
    eh_orientador = True
    c_orientador = colunas_esc.get('orientador')
    c_email_or = colunas_esc.get('email_orientador')
    nome_completo_docente = df_escalacao[df_escalacao[c_email_or].astype(str).str.lower() == email_user][c_orientador].iloc[0]
elif checar_email_na_coluna(email_user, df_escalacao, 'Email_Avaliador_1'):
    eh_banca = True
    c_av1 = colunas_esc.get('avaliador_1')
    c_email_av1 = colunas_esc.get('email_avaliador_1')
    nome_completo_docente = df_escalacao[df_escalacao[c_email_av1].astype(str).str.lower() == email_user][c_av1].iloc[0]
elif checar_email_na_coluna(email_user, df_escalacao, 'Email_Avaliador_2'):
    eh_banca = True
    c_av2 = colunas_esc.get('avaliador_2')
    c_email_av2 = colunas_esc.get('email_avaliador_2')
    nome_completo_docente = df_escalacao[df_escalacao[c_email_av2].astype(str).str.lower() == email_user][c_av2].iloc[0]
elif checar_email_na_coluna(email_user, df_escalacao, 'Email_Suplente'):
    eh_banca = True
    c_sup = colunas_esc.get('avaliador_suplente')
    c_email_sup = colunas_esc.get('email_suplente')
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
if not df_escalacao.empty:
    c_alunos = colunas_esc.get('alunos')
    if eh_orientador:
        c_email_or = colunas_esc.get('email_orientador')
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
        c_em_av1 = colunas_esc.get('email_avaliador_1')
        c_em_av2 = colunas_esc.get('email_avaliador_2')
        c_em_sup = colunas_esc.get('email_suplente')
        
        cond_banca = (
            (df_escalacao[c_em_av1].astype(str).str.lower() == email_user) | 
            (df_escalacao[c_em_av2].astype(str).str.lower() == email_user) | 
            (df_escalacao[c_em_sup].astype(str).str.lower() == email_user)
        )
        possiveis = df_escalacao[cond_banca].copy()
        items_feitos = df_respostas[(df_respostas["Email_Avaliador"] == email_user) & (df_respostas["Papel"] == "Banca")]["Alunos"].tolist()
        pendentes = possiveis[~possiveis[c_alunos].isin(items_feitos)].copy()

if pendentes.empty:
    st.balloons()
    st.success("🎉 Todas as suas avaliações pendentes foram concluídas!")
else:
    c_alunos = colunas_esc.get('alunos')
    # Correção completa e definitiva do fechamento de strings/parênteses do lambda
    pendentes['Alunos_Curto'] = pendentes[c_alunos].apply(lambda x: ", ".join([tratar_nome_curto(n) for n in str(x).split(",")]))
    lista_grupos_display = pendentes["Alunos_Curto"].tolist()
    lista_grupos_reais = pendentes[c_alunos].tolist()
    
    grupo_map = dict(zip(lista_grupos_display, lista_grupos_reais))
    selecionado_display = st.selectbox("🎯 Escolha o Grupo para Avaliar:", [""] + lista_grupos_display)

    if selecionado_display and selecionado_display != "":
        aluno_selecionado = grupo_map[selecionado_display]
        dados = pendentes[pendentes[c_alunos] == aluno_selecionado].iloc[0]
        turma_bruta = str(obter_valor_coluna(dados, 'turma')).strip().upper()
        
        # --- TRAVA DE HORÁRIO RÍGIDA (5 MINUTOS ANTES) ---
        banca_liberada = True
        msg_trava = ""
        try:
            val_data = str(obter_valor_coluna(dados, 'data')).strip()
            val_horario = str(obter_valor_coluna(dados, 'horario')).strip()
            data_
