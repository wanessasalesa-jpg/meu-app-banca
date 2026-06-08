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

# FUNÇÃO PARA ENCURTUR NOMES NA EXIBIÇÃO DO APP
def tratar_nome_curto(nome_completo):
    if not nome_completo or pd.isna(nome_completo):
        return ""
    partes = str(nome_completo).strip().split()
    if len(partes) > 1:
        return f"{partes[0]} {partes[1]}"
    return partes[0]

# 3. CONEXÃO COM GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(aba, ttl_sec=2):
    return conn.read(worksheet=aba, ttl=ttl_sec)

try:
    df_escalacao = get_data("Escalacao", ttl_sec=300)
    if 'Aptidão Defesa' in df_escalacao.columns:
        df_escalacao['Aptidão Defesa'] = df_escalacao['Aptidão Defesa'].astype(str).replace('nan', '')
    if 'Assinatura Orientador' in df_escalacao.columns:
        df_escalacao['Assinatura Orientador'] = df_escalacao['Assinatura Orientador'].astype(str).replace('nan', '')
except:
    st.error("Conectando ao banco de dados... Aguarde.")
    time.sleep(1)
    st.rerun()

# --- MAPEAMENTO CASE-INSENSITIVE DAS COLUNAS DA ESCALAÇÃO ---
colunas_reais = {str(col).strip().lower(): col for col in df_escalacao.columns}

c_av1_email = colunas_reais.get('email_avaliador_1')
c_av1_nome = colunas_reais.get('avaliador_1')
c_av2_email = colunas_reais.get('email_avaliador_2')
c_av2_nome = colunas_reais.get('avaliador_2')
c_sup_email = colunas_reais.get('email_suplente')
c_sup_nome = colunas_reais.get('avaliador_suplente')
c_ori_email = colunas_reais.get('email_orientador')
c_ori_nome = colunas_reais.get('orientador')
c_turma = colunas_reais.get('turma')
c_titulo = colunas_reais.get('titulo')
c_data = colunas_reais.get('data')
c_horario = colunas_reais.get('horario')

c_aptidao_col = colunas_reais.get('aptidão defesa')
c_assinatura_col = colunas_reais.get('assinatura orientador')

# MAPEAMENTO DAS COLUNAS SEPARADAS DE ALUNOS
c_aluno1 = colunas_reais.get('aluno_1')
c_aluno2 = colunas_reais.get('aluno_2')
c_aluno3 = colunas_reais.get('aluno_3')
c_aluno4 = colunas_reais.get('aluno_4')
c_aluno5 = colunas_reais.get('aluno_5')

# FUNÇÃO AUXILIAR PARA CHECAR SE O EMAIL EXISTE NA COLUNA MAPEADA
def verificar_presenca_email(email, coluna_real):
    if not coluna_real:
        return False
    return email in df_escalacao[coluna_real].astype(str).str.strip().str.lower().unique()

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
    st.markdown("""
        <style>
        header {visibility: hidden !important;}
        #MainMenu {visibility: hidden !important;}
        footer {visibility: hidden;}
        .stButton button {
            width: 100% !important;
            border-radius: 10px !important;
            height: 3.5em !important;
            background-color: #002147 !important;
            color: white !important;
            font-weight: bold !important;
            border: none !important;
        }
        </style>
        """, unsafe_allow_html=True)

    st.title("🎓 CRIVO")
    st.subheader("Sistema de Gestão de Bancas Acadêmicas")
    st.caption("© 2026 Desenvolvido por Wanessa Sales de Almeida")
    st.divider()

    st.write("### Identificação do Docente")
    email_raw = st.text_input("Digite seu e-mail cadastrado:").strip()
    if st.button("Acessar Sistema"):
        if email_raw:
            email_limpo = email_raw.lower()
            
            id_banca1 = verificar_presenca_email(email_limpo, c_av1_email)
            id_banca2 = verificar_presenca_email(email_limpo, c_av2_email)
            id_suplente = verificar_presenca_email(email_limpo, c_sup_email)
            id_orienta = verificar_presenca_email(email_limpo, c_ori_email)
            
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

if verificar_presenca_email(email_user, c_ori_email):
    eh_orientador = True
    nome_completo_docente = df_escalacao[df_escalacao[c_ori_email].astype(str).str.lower() == email_user][c_ori_nome].iloc[0]
elif verificar_presenca_email(email_user, c_av1_email):
    eh_banca = True
    nome_completo_docente = df_escalacao[df_escalacao[c_av1_email].astype(str).str.lower() == email_user][c_av1_nome].iloc[0]
elif verificar_presenca_email(email_user, c_av2_email):
    eh_banca = True
    nome_completo_docente = df_escalacao[df_escalacao[c_av2_email].astype(str).str.lower() == email_user][c_av2_nome].iloc[0]
elif verificar_presenca_email(email_user, c_sup_email):
    eh_banca = True
    nome_completo_docente = df_escalacao[df_escalacao[c_sup_email].astype(str).str.lower() == email_user][c_sup_nome].iloc[0]

nome_exibicao = tratar_nome_curto(nome_completo_docente)

# --- DEFINIÇÃO DINÂMICA DE CORES ---
cor_primaria = "#002147" if not eh_orientador else "#FF1493"
cor_texto_bloco = "#ffffff"

st.markdown(f"""
    <style>
    header {{visibility: hidden !important;}}
    #MainMenu {{visibility: hidden !important;}}
    footer {{visibility: hidden;}}
    
    .bloco-cabecalho {{
        background-color: {cor_primaria} !important;
        padding: 25px !important;
        border-radius: 12px !important;
        color: {cor_texto_bloco} !important;
        margin-bottom: 25px !important;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1) !important;
    }}
    .bloco-cabecalho h1, .bloco-cabecalho h3, .bloco-cabecalho p {{
        color: {cor_texto_bloco} !important;
        margin: 0 !important;
        padding: 2px 0 !important;
    }}
    
    .stButton button {{
        width: 100% !important;
        border-radius: 10px !important;
        height: 3.5em !important;
        background-color: {cor_primaria} !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
    }}
    </style>
    """, unsafe_allow_html=True)

sub_titulo_texto = "Sistema de Gestão de Bancas Acadêmicas" if not eh_orientador else "Sistema de Gestão de Orientações"
st.markdown(f"""
    <div class="bloco-cabecalho">
        <h1>🎓 CRIVO</h1>
        <h3>{sub_titulo_texto}</h3>
        <p style="font-size: 0.85em; opacity: 0.8;">© 2026 Desenvolvido por Wanessa Sales de Almeida</p>
    </div>
    """, unsafe_allow_html=True)

# FUNÇÃO AUXILIAR PARA MONTAR A LISTA DE ALUNOS REAL DE UMA LINHA DA ESCALAÇÃO
def obter_lista_alunos_linha(row):
    lista = []
    for col_aluno in [c_aluno1, c_aluno2, c_aluno3, c_aluno4, c_aluno5]:
        if col_aluno and col_aluno in row and pd.notna(row[col_aluno]):
            nome = str(row[col_aluno]).strip()
            if nome and nome.lower() != "nan" and nome != "":
                lista.append(nome)
    return lista

# --- FILTRAGEM DE GRUPOS PENDENTES EM TEMPO REAL ---
pendentes = pd.DataFrame()
total_pendencias_contador = 0

if not df_escalacao.empty:
    if eh_orientador:
        possiveis = df_escalacao[df_escalacao[c_ori_email].astype(str).str.lower() == email_user].copy()
        linhas_pendentes = []
        for idx, row in possiveis.iterrows():
            turma_check = str(row[c_turma]).strip().upper() if c_turma else ""
            
            # Bloqueia estritamente MCM V e TCC I da tela do orientador
            if "MCM V" in turma_check or "MCM 5" in turma_check or "TCC I" in turma_check or "TCC 1" in turma_check:
                continue
                
            alunos_grupo = obter_lista_alunos_linha(row)
            avaliados = df_respostas[(df_respostas["Email_Avaliador"] == email_user) & (df_respostas["Papel"] == "Orientador")]["Alunos"].tolist()
            alunos_restantes = [a for a in alunos_grupo if a not in avaliados]
            
            val_apt = row.get(c_aptidao_col)
            ja_preencheu_aptidao = pd.notna(val_apt) and str(val_apt).strip() != "" and str(val_apt).strip().lower() != "nan"
            precisa_tela_aptidao = ("TCC II" in turma_check or "TCC 2" in turma_check) and not ja_preencheu_aptidao
            
            if alunos_restantes or precisa_tela_aptidao:
                linhas_pendentes.append(row)
                total_pendencias_contador += len(alunos_restantes) + (1 if precisa_tela_aptidao and not alunos_restantes else 0)
        if linhas_pendentes:
            pendentes = pd.DataFrame(linhas_pendentes)
    else:
        cond_banca = pd.Series(False, index=df_escalacao.index)
        if c_av1_email:
            cond_banca |= (df_escalacao[c_av1_email].astype(str).str.lower() == email_user)
        if c_av2_email:
            cond_banca |= (df_escalacao[c_av2_email].astype(str).str.lower() == email_user)
        if c_sup_email:
            cond_banca |= (df_escalacao[c_sup_email].astype(str).str.lower() == email_user)
            
        possiveis = df_escalacao[cond_banca].copy()
        linhas_pendentes = []
        for idx, row in possiveis.iterrows():
            alunos_grupo = obter_lista_alunos_linha(row)
            string_grupo_banca = ", ".join(alunos_grupo)
            
            ja_avaliou = df_respostas[(df_respostas["Email_Avaliador"] == email_user) & (df_respostas["Papel"] == "Banca") & (df_respostas["Alunos"] == string_grupo_banca)]
            if ja_avaliou.empty and alunos_grupo:
                linhas_pendentes.append(row)
                total_pendencias_contador += 1
        if linhas_pendentes:
            pendentes = pd.DataFrame(linhas_pendentes)

# --- AMBIENTE VISUAL DO DOCENTE ---
col_user, col_exit = st.columns([3, 1])
with col_user:
    st.write(f"**Docente:** {nome_exibicao} ({'Orientador' if eh_orientador else 'Banca Examinadora'})")
with col_exit:
    if st.button("Sair"):
        if total_pendencias_contador > 0:
            st.session_state.tentou_sair_com_pendencia = True
        else:
            st.session_state.clear()
            st.query_params.clear()
            st.rerun()

if st.session_state.get("tentou_sair_com_pendencia", False):
    st.warning(f"⚠️ **Atenção:** Ainda possui **{total_pendencias_contador}** avaliações pendentes registadas no seu nome!")
    col_cancela, col_confirma = st.columns(2)
    with col_cancela:
        if st.button("🔄 Voltar e Avaliar"):
            st.session_state.tentou_sair_com_pendencia = False
            st.rerun()
    with col_confirma:
        if st.button("🏃 Sair Mesmo Assim"):
            st.session_state.clear()
            st.query_params.clear()
            st.rerun()
    st.stop()

if pendentes.empty:
    st.balloons()
    st.success("🎉 Todas as suas avaliações pendentes foram concluídas!")
    if "grupo_selecionado" in st.session_state:
        del st.session_state["grupo_selecionado"]
else:
    def gerar_display_grupo(row):
        alunos = obter_lista_alunos_linha(row)
        return ", ".join(
