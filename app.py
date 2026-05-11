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

# 3. ESTILIZAÇÃO INTERNA (CSS)
st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stButton button {
        width: 100%;
        border-radius: 10px;
        height: 3.5em;
        background-color: #002147;
        color: white;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. CABEÇALHO
st.title("🎓 CRIVO")
st.subheader("Sistema de Gestão de Bancas Acadêmicas")
st.caption("© 2026 Desenvolvido por Wanessa Sales de Almeida")
st.divider()

# 5. CONEXÃO COM GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(aba, ttl_sec=2):
    return conn.read(worksheet=aba, ttl=ttl_sec)

# 6. CARREGAMENTO DOS DADOS
try:
    df_escalacao = get_data("Escalacao", ttl_sec=300)
except:
    st.error("Conectando ao banco de dados... Aguarde.")
    time.sleep(1)
    st.rerun()

# --- A TRAVA REAL DE LOGOUT (QUERY PARAMS ATUALIZADO) ---
# Verifica se existe um utilizador na URL ou na sessão
if 'email' not in st.session_state:
    if "user" in st.query_params:
        st.session_state.email = st.query_params["user"]

if 'email' not in st.session_state:
    st.write("### Identificação de Avaliador")
    email_raw = st.text_input("Digite seu e-mail cadastrado:").strip()
    if st.button("Acessar Sistema"):
        if email_raw:
            email_limpo = email_raw.lower()
            if email_limpo in df_escalacao['Email'].str.lower().unique():
                st.session_state.email = email_limpo
                # Esta linha trava o e-mail na URL
                st.query_params["user"] = email_limpo
                st.rerun()
            else:
                st.error("E-mail não autorizado ou não encontrado.")
    st.stop()

# --- AMBIENTE DO PROFESSOR ---
prof_dados = df_escalacao[df_escalacao['Email'].str.lower() == st.session_state.email].iloc[0]
nome_avaliador = prof_dados['Avaliador']

col_user, col_exit = st.columns([3, 1])
with col_user:
    st.write(f"**Avaliador:** {nome_avaliador}")
with col_exit:
    if st.button("Sair"):
        # Limpa tudo para permitir novo login
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()

# Busca de trabalhos já avaliados
try:
    df_respostas = get_data("Respostas", ttl_sec=0)
    feitos = df_respostas[df_respostas["Email_Avaliador"] == st.session_state.email]["Alunos"].tolist()
except:
    feitos = []

pendentes = df_escalacao[(df_escalacao['Email'].str.lower() == st.session_state.email) & (~df_escalacao['Alunos'].isin(feitos))].copy()

if pendentes.empty:
    st.balloons()
    st.success("🎉 Todas as suas avaliações foram enviadas com sucesso!")
else:
    lista_grupos = pendentes["Alunos"].tolist()
    aluno_selecionado = st.selectbox("🎯 Escolha o Grupo para Avaliar:", [""] + lista_grupos)

    if aluno_selecionado:
        dados = pendentes[pendentes["Alunos"] == aluno_selecionado].iloc[0]
        turma_bruta = str(dados['Turma']).strip().upper()
        
        with st.expander("📖 Informações do Trabalho", expanded=True):
            st.write(f"**Turma:** {turma_bruta}")
            st.write(f"**Título:** {dados['Titulo']}")
            st.write(f"**Orientador:** {dados['Orientador']}")

        @st.fragment
        def formulario_avaliacao():
            st.write("### 📝 Critérios de Avaliação")
            notas = {}
            
            # --- RUBRICAS COM TEMPO E HELP ---
            if "TCC I" in turma_bruta and "TCC II" not in turma_bruta:
                rubrica = {
                    "Tema": (3, "Clareza, delimitação e atualidade do tema."),
                    "Resumo": (1, "Objetivo, método, resultados esperados e palavras-chave."),
                    "Introdução": (5, "Contextualização e problema de pesquisa."),
                    "Justificativa": (5, "Importância e contribuição do trabalho."),
                    "Objetivos": (5, "Geral e específicos claros."),
                    "Metodologia": (10, "Desenho do estudo e rigor técnico."),
                    "Referências": (1, "Normas ABNT/Vancouver."),
                    "Apresentação Oral": (10, "Domínio de conteúdo e clareza."),
                    "Coerência": (10, "Lógica entre as partes do texto."),
                    "Qualidade Visual": (9, "Organização dos slides."),
                    "Tempo": (1, "Respeito ao tempo limite.")
                }
            elif "TCC II" in turma_bruta:
                rubrica = {
                    "Tema/Resumo": (4, "Qualidade técnica e aderência ao tema."),
                    "Introdução": (5, "Fundamentação teórica sólida."),
                    "Metodologia": (5, "Execução do método proposto."),
                    "Resultados": (5, "Apresentação clara dos dados."),
                    "Discussão": (10, "Capacidade crítica e confronto literário."),
                    "Referências": (1, "Rigor técnico nas citações."),
                    "Apresentação Oral": (10, "Segurança na defesa."),
                    "Coerência": (10, "União lógica do trabalho final."),
                    "Qualidade Visual": (9, "Profissionalismo nos slides."),
                    "Tempo": (1, "Cumprimento rigoroso do tempo limite de apresentação.")
                }
            else:
                rubrica = {
                    "Resumo/Introdução": (10, "Síntese e fundamentação."),
                    "Metodologia": (10, "Rigor e descrição."),
                    "Resultados/Discussão": (20, "Análise e crítica."),
                    "Redação/ABNT": (10, "Gramática e normas."),
                    "Arguição": (10, "Segurança nas respostas."),
                    "Apresentação Oral": (10, "Domínio de conteúdo."),
                    "Qualidade Visual": (10, "Estética dos slides."),
                    "Tempo": (10, "Respeito ao limite de tempo.")
                }

            for item, (p, help_t) in rubrica.items():
                notas[item] = st.slider(f"**{item} ({p} pts)**", 0, p, 0, help=help_t, key=f"s_{item}")

            total = sum(notas.values())
            st.markdown(f"## Nota Final: {total}")

            # --- TRAVA DE NOTA ZERO ---
            tem_zero = any(v == 0 for v in notas.values())
            conf_zero = True
            if tem_zero:
                st.error("⚠️ Atenção: Existem critérios com nota zero.")
                conf_zero = st.checkbox("Confirmo que as notas zero são intencionais.")

            if st.button("🚀 GRAVAR AVALIAÇÃO NO SISTEMA"):
                if tem_zero and not conf_zero:
                    st.warning("Marque o checkbox acima para confirmar as notas zero.")
                else:
                    try:
                        df_at = conn.read(worksheet="Respostas", ttl=0)
                        nova_l = pd.DataFrame([{
                            "Avaliador": nome_avaliador, 
                            "Email_Avaliador": st.session_state.email, 
                            "Alunos": aluno_selecionado, 
                            "Nota_Final": total, 
                            "Data_Hora": datetime.now(fuso_bruta).strftime("%d/%m/%Y %H:%M")
                        }])
                        df_f = pd.concat([df_at, nova_l], ignore_index=True)
                        conn.update(worksheet="Respostas", data=df_f)
                        st.success("✅ Avaliação gravada com sucesso!")
                        time.sleep(2)
                        st.rerun()
                    except:
                        st.error("Erro de conexão.")

        formulario_avaliacao()
