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
    pendentes['Alunos_Curto'] = pendentes['Alunos'].apply(lambda x: ", ".join([tratar_nome_curto(n) for n in str(x).split(",")]))
    lista_grupos_display = pendentes["Alunos_Curto"].tolist()
    lista_grupos_reais = pendentes["Alunos"].tolist()
    
    grupo_map = dict(zip(lista_grupos_display, lista_grupos_reais))
    selecionado_display = st.selectbox("🎯 Escolha o Grupo para Avaliar:", [""] + lista_grupos_display)

    if selecionado_display and selecionado_display != "":
        aluno_selecionado = grupo_map[selecionado_display]
        dados = pendentes[pendentes["Alunos"] == aluno_selecionado].iloc[0]
        turma_bruta = str(dados['Turma']).strip().upper()
        
        # --- TRAVA DE HORÁRIO RÍGIDA (5 MINUTOS ANTES) ---
        banca_liberada = True
        msg_trava = ""
        try:
            data_banca = datetime.strptime(str(dados['Data']).strip(), "%d/%m/%Y").date()
            horario_banca = datetime.strptime(str(dados['Horario']).strip(), "%H:%M").time()
            dt_banca_completa = fuso_bruta.localize(datetime.combine(data_banca, horario_banca))
            
            agora = obter_agora()
            limite_liberacao = dt_banca_completa - timedelta(minutes=5)
            
            if agora < limite_liberacao:
                banca_liberada = False
                msg_trava = f"⏳ Esta avaliação só estará disponível a partir das {limite_liberacao.strftime('%H:%M')} do dia {data_banca.strftime('%d/%m/%Y')}."
        except:
            pass

        with st.expander("📖 Informações do Trabalho", expanded=True):
            st.write(f"**Turma:** {turma_bruta}")
            st.write(f"**Título:** {dados['Titulo']}")
            st.write(f"**Orientador:** {tratar_nome_curto(dados['Orientador'])}")
            st.write(f"**Integrantes do Grupo:** {aluno_selecionado}")
            st.write(f"**Data/Horário Cadastrado:** {dados['Data']} às {dados['Horario']}")

        if not banca_liberada:
            st.warning(msg_trava)
        else:
            aluno_alvo_final = aluno_selecionado
            exibir_formulario = True

            if eh_orientador:
                if "MCM V" in turma_bruta or "MCM 5" in turma_bruta:
                    exibir_formulario = False
                    st.warning("⚠️ Nota do orientador não aplicável para esta turma. A turma MCM V possui 100% da nota final atribuída exclusivamente pela banca examinadora.")
                else:
                    lista_alunos_individuais = [a.strip() for a in str(aluno_selecionado).split(",") if a.strip()]
                    avaliados_na_aba = df_respostas[(df_respostas["Email_Avaliador"] == email_user) & (df_respostas["Papel"] == "Orientador")]["Alunos"].tolist()
                    lista_alunos_individuais = [a for a in lista_alunos_individuais if a not in avaliados_na_aba]
                    
                    if lista_alunos_individuais:
                        aluno_alvo_final = st.selectbox("👤 Selecione o Aluno para atribuir a nota individual:", lista_alunos_individuais)
                    else:
                        exibir_formulario = False
                        st.success("Todos os alunos deste grupo já foram avaliados por você!")

            if exibir_formulario:
                @st.fragment
                def formulario_avaliacao(aluno_para_salvar):
                    rubrica = {}
                    
                    # --- FLUXO 1: VISÃO DO ORIENTADOR ---
                    if eh_orientador:
                        st.info(f"🌱 Avaliando individualmente o discente: **{aluno_para_salvar}**")
                        
                        if "MCM IV" in turma_bruta or "MCM 4" in turma_bruta:
                            rubrica = {
                                "Desenv. - Envolvimento e Responsabilidade": (5, "Participação proativa, demonstrando alta responsabilidade e comprometimento."),
                                "Desenv. - Relação com Orientador / Diálogo": (5, "Relação colaborativa, com boa abertura ao diálogo e aceitação de sugestões."),
                                "Desenv. - Desempenho e Cumprimento de Tarefas": (5, "Desempenho satisfatório, com atividades realizadas de forma competente e engajada."),
                                "Desenv. - Pontualidade e Compromisso": (5, "Pontualidade é mantida consistentemente, demonstrando compromisso com o processo."),
                                "Desenv. - Resp. com Processo de Aprendizagem": (5, "Responsabilidade evidente em buscar ativamente oportunidades de aprendizado e aprimoramento."),
                                "Texto - Justificativa do Estudo": (6, "Apresenta com clareza a relevância científica, social ou profissional vinculada ao problema."),
                                "Texto - Objetivo Geral e Específicos": (6, "Objetivo geral claro e coerente com a justificativa; específicos bem articulados."),
                                "Texto - Fundamentação Teórica / Referências": (6, "Referencial teórico relevante, atualizado e articulado."),
