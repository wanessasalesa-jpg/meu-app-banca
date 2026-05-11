import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta
import time
import pytz 

# Configuração de página
st.set_page_config(page_title="CRIVO - Gestão Acadêmica", layout="centered")

# Fuso horário oficial de Brasília
fuso_bruta = pytz.timezone('America/Sao_Paulo')

# Estilização Profissional
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
    .stProgress > div > div > div > div { background-color: #002147; }
    </style>
    """, unsafe_allow_html=True)

# Cabeçalho Limpo
st.title("🎓 CRIVO")
st.subheader("Sistema de Gestão de Bancas Acadêmicas")
st.caption("© 2026 Desenvolvido por Wanessa Sales de Almeida")
st.divider()

# Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(aba, ttl_sec=2):
    return conn.read(worksheet=aba, ttl=ttl_sec)

# Carregamento de Dados
try:
    df_escalacao = get_data("Escalacao", ttl_sec=300)
except:
    st.error("Sincronizando com o banco de dados... Aguarde.")
    time.sleep(1)
    st.rerun()

# --- LOGIN ---
if 'email' not in st.session_state:
    st.write("### Identificação de Avaliador")
    email_raw = st.text_input("Digite seu e-mail cadastrado:").strip()
    if st.button("Acessar Sistema"):
        if email_raw:
            email_limpo = email_raw.lower()
            if email_limpo in df_escalacao['Email'].str.lower().unique():
                st.session_state.email = email_limpo
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
        del st.session_state.email
        st.rerun()

# Busca de trabalhos pendentes
try:
    df_respostas = get_data("Respostas", ttl_sec=0)
    feitos = df_respostas[df_respostas["Email_Avaliador"] == st.session_state.email]["Alunos"].tolist()
except:
    feitos = []

agora_local = datetime.now(fuso_bruta).replace(tzinfo=None)

pendentes = df_escalacao[(df_escalacao['Email'].str.lower() == st.session_state.email) & (~df_escalacao['Alunos'].isin(feitos))].copy()

if pendentes.empty:
    st.balloons()
    st.success("🎉 Todas as suas avaliações foram enviadas!")
else:
    lista_grupos = pendentes["Alunos"].tolist()
    aluno_selecionado = st.selectbox("🎯 Escolha o Grupo para Avaliar:", [""] + lista_grupos)

    if aluno_selecionado:
        dados = pendentes[pendentes["Alunos"] == aluno_selecionado].iloc[0]
        # AQUI ESTÁ A CORREÇÃO DA TURMA:
        turma_bruta = str(dados['Turma']).strip().upper()
        
        with st.expander("📖 Detalhes do Trabalho", expanded=True):
            st.write(f"**Turma:** {turma_bruta}")
            st.write(f"**Título:** {dados['Titulo']}")
            st.write(f"**Orientador:** {dados['Orientador']}")

        @st.fragment
        def formulario_avaliacao():
            st.write("### 📝 Critérios de Avaliação")
            notas = {}
            
            # --- RUBRICAS DETALHADAS (O "HELP" MARAVILHOSO VOLTOU) ---
            if "TCC I" in turma_bruta and "TCC II" not in turma_bruta:
                rubrica = {
                    "Tema": (3, "Avalie a clareza, delimitação e a atualidade do tema proposto."),
                    "Resumo": (1, "Verifique se contém objetivo, método, resultados esperados e palavras-chave."),
                    "Introdução": (5, "Contextualização do tema e se o problema de pesquisa está claro."),
                    "Justificativa": (5, "A importância do trabalho e contribuição para a ciência/sociedade."),
                    "Objetivos": (5, "Se o objetivo geral e específicos são mensuráveis e claros."),
                    "Metodologia": (10, "Descrição detalhada do desenho do estudo, critérios e ética."),
                    "Referências": (1, "Uso de normas ABNT/Vancouver e atualidade das fontes."),
                    "Apresentação Oral": (10, "Domínio de conteúdo, postura e clareza na fala."),
                    "Coerência": (10, "Lógica entre introdução, objetivos e métodos."),
                    "Qualidade Visual": (9, "Organização dos slides, tempo e recursos visuais."),
                    "Tempo": (1, "Respeito ao tempo limite estipulado.")
                }
            elif "TCC II" in turma_bruta:
                rubrica = {
                    "Tema/Resumo": (4, "Qualidade técnica do resumo e aderência ao tema."),
                    "Introdução": (5, "Fundamentação teórica sólida e revisão de literatura."),
                    "Metodologia": (5, "Execução real do método proposto no TCC I."),
                    "Resultados": (5, "Apresentação clara dos dados obtidos."),
                    "Discussão": (10, "Capacidade crítica de comparar resultados com a literatura."),
                    "Referências": (1, "Rigor técnico nas citações e bibliografia."),
                    "Apresentação Oral": (10, "Segurança na defesa dos resultados."),
                    "Coerência": (10, "União lógica de todas as partes do trabalho final."),
                    "Qualidade Visual": (9, "Profissionalismo na apresentação visual."),
                    "Tempo": (1, "Cumprimento rigoroso do tempo.")
                }
            else: # Padrão para outras turmas como MCM
                rubrica = {
                    "Domínio": (10, "Conhecimento profundo do tema."),
                    "Argumentação": (10, "Capacidade de responder à banca."),
                    "Organização": (10, "Estrutura lógica do trabalho.")
                }

            for item, (p, help_t) in rubrica.items():
                notas[item] = st.slider(f"**{item} ({p} pts)**", 0, p, 0, help=help_t, key=f"s_{item}")

            total = sum(notas.values())
            st.markdown(f"## Nota Final: {total}")

            if st.button("🚀 GRAVAR AVALIAÇÃO"):
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
                    st.success("✅ Avaliação gravada com sucesso no banco de dados!")
                    time.sleep(2)
                    st.rerun()
                except:
                    st.error("Erro ao salvar. Verifique sua conexão.")

        formulario_avaliacao()
