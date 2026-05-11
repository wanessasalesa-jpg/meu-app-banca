import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta
import time
import pytz 

# Configuração estável
st.set_page_config(page_title="CRIVO - Gestão de Bancas", layout="centered")

# Alterado para o padrão nacional de Brasília (comercialmente melhor)
fuso_bruta = pytz.timezone('America/Sao_Paulo')

# CSS para esconder menus e estilizar botões
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

# --- CABEÇALHO COM IDENTIDADE VISUAL ---
col_logo, col_tit = st.columns([1, 4])
with col_logo:
    # Exibe a logo do CRIVO
    st.image("http://googleusercontent.com/image_collection/image_retrieval/8612724178582184266", width=100)

with col_tit:
    st.title("CRIVO")
    st.subheader("Sistema de Gestão de Bancas")

st.caption("© 2026 Desenvolvido por Wanessa Sales de Almeida")
st.divider()

conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(aba, ttl_sec=2):
    return conn.read(worksheet=aba, ttl=ttl_sec)

# 1. CARREGAMENTO
try:
    df_escalacao = get_data("Escalacao", ttl_sec=300)
except:
    st.error("Sincronizando dados...")
    time.sleep(1)
    st.rerun()

# --- LOGIN PERSISTENTE ---
query_params = st.query_params
if "user" in query_params and "email" not in st.session_state:
    st.session_state.email = query_params["user"]

if 'email' not in st.session_state:
    st.write("### Identificação")
    email_raw = st.text_input("E-mail cadastrado:").strip()
    if st.button("Acessar CRIVO"):
        if email_raw:
            email_limpo = email_raw.lower()
            if email_limpo in df_escalacao['Email'].str.lower().unique():
                st.session_state.email = email_limpo
                st.query_params["user"] = email_limpo
                st.rerun()
            else:
                st.error("Acesso não autorizado.")
    st.stop()

# --- INTERFACE DO AVALIADOR ---
prof_dados = df_escalacao[df_escalacao['Email'].str.lower() == st.session_state.email].iloc[0]
nome_avaliador = prof_dados['Avaliador']

col_user, col_exit = st.columns([3, 1])
with col_user:
    st.write(f"**Avaliador:** {nome_avaliador}")
with col_exit:
    if st.button("Sair"):
        del st.session_state.email
        st.query_params.clear()
        st.rerun()

# BUSCA DE PENDENTES
try:
    df_respostas = get_data("Respostas", ttl_sec=0)
    feitos = df_respostas[df_respostas["Email_Avaliador"] == st.session_state.email]["Alunos"].tolist()
except:
    feitos = []

# --- LÓGICA DE TRAVA (Horário de Brasília) ---
agora_local = datetime.now(fuso_bruta).replace(tzinfo=None)

def verificar_liberacao(linha):
    try:
        data_banca = pd.to_datetime(linha['Data'], dayfirst=True).date()
        hora_banca = pd.to_datetime(linha['Horario']).time()
        momento_banca = datetime.combine(data_banca, hora_banca)
        # Libera 15 min antes
        return agora_local >= (momento_banca - timedelta(minutes=15))
    except:
        return True

pendentes = df_escalacao[(df_escalacao['Email'].str.lower() == st.session_state.email) & (~df_escalacao['Alunos'].isin(feitos))].copy()

if pendentes.empty:
    st.balloons()
    st.success("🎉 Todas as avaliações foram concluídas!")
else:
    pendentes['liberado'] = pendentes.apply(verificar_liberacao, axis=1)
    visiveis = pendentes[pendentes['liberado'] == True].copy()

    if visiveis.empty:
        st.warning("⏳ **Bancas em espera.**")
        st.info("As avaliações serão liberadas conforme o cronograma oficial.")
    else:
        visiveis['ordem_tempo'] = pd.to_datetime(visiveis['Data'].astype(str) + ' ' + visiveis['Horario'].astype(str))
        visiveis = visiveis.sort_values(by='ordem_tempo')
        lista_grupos = visiveis["Alunos"].tolist()
        aluno_selecionado = st.selectbox("🎯 Selecione o Grupo:", [""] + lista_grupos)

        if aluno_selecionado:
            dados = visiveis[visiveis["Alunos"] == aluno_selecionado].iloc[0]
            turma_bruta = str(dados['Turma']).strip().upper()
            
            with st.expander("📖 Ficha Técnica", expanded=True):
                st.write(f"**Trabalho:** {turma_bruta}")
                st.write(f"**Título:** {dados['Titulo']}")
                st.write(f"**Orientador:** {dados['Orientador']}")

            @st.fragment
            def formulario_avaliacao():
                st.write("### 📝 Rubricas de Avaliação")
                notas = {}
                
                # Definição de Rubricas (TCC I, II e MCM V)
                if "TCC I" in turma_bruta and "TCC II" not in turma_bruta:
                    rubrica = {"Tema Contemporâneo": (3, "Escolha de tema contemporâneo."), "Resumo": (1, "Autoexplicativo, objetivos e conclusão."), "Introdução": (5, "Clareza e sequência lógica."), "Justificativa/Problema": (5, "ABNT e relevância."), "Objetivos": (5, "Claros e exequíveis."), "Metodologia": (10, "Tipo de estudo e ética."), "Referências": (1, "Fontes confiáveis e atuais."), "Apresentação Oral": (10, "Postura e domínio."), "Coerência": (10, "Sintonia fala/escrita."), "Qualidade Visual": (9, "Material bem estruturado."), "Tempo (10-15min)": (1, "Respeito ao limite.")}
                elif "TCC II" in turma_bruta:
                    rubrica = {"Tema e Resumo": (4, "Contemporaneidade e DECS."), "Introdução": (5, "Justificativa e objetivos."), "Metodologia": (5, "Rigor científico e ética."), "Resultados": (5, "Descrição concisa."), "Discussão/Conclusão": (10, "Análise crítica."), "Referências": (1, "Pertinentes e atuais."), "Apresentação Oral": (10, "Domínio e clareza."), "Coerência": (10, "Lógica oral/escrita."), "Qualidade Visual": (9, "Slides organizados."), "Tempo (15-20min)": (1, "Cumprimento do tempo.")}
                elif "MCM V" in turma_bruta:
                    rubrica = {"Resumo": (10, "Qualidade da síntese."), "Introdução": (10, "Fundamentação e objetivos."), "Metodologia": (10, "Desenho e métodos."), "Resultados": (20, "Análise clara."), "Discussão": (10, "Confronto com literatura."), "Conclusão": (10, "Pertinência."), "Redação/ABNT": (10, "Gramática e normas."), "Arguição": (10, "Segurança nas respostas."), "Apresentação": (10, "Fluidez e domínio (15-20 min).")}
                else:
                    rubrica = {"Domínio": (5, "Conhecimento."), "Coerência": (5, "Lógica."), "Comunicação": (5, "Postura."), "Organização": (5, "Gestão."), "Visual": (5, "Qualidade."), "Métodos": (5, "Adequação.")}

                total = 0
                for item, (p, help_t) in rubrica.items():
                    notas[item] = st.slider(f"**{item} ({p} pts)**", 0, p, 0, help=help_t, key=f"s_{item}")

                total = sum(notas.values())
                st.markdown(f"## Pontuação Final: {total}")

                tem_zero = any(v == 0 for v in notas.values())
                conf_zero = True
                if tem_zero:
                    st.error("⚠️ Critérios com nota zero detectados.")
                    conf_zero = st.checkbox("Confirmo que as notas zero são intencionais.")

                if st.button("🚀 FINALIZAR AVALIAÇÃO"):
                    if tem_zero and not conf_zero:
                        st.warning("Por favor, confirme as notas zero.")
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
                            st.balloons()
                            st.success("Avaliação enviada com sucesso!")
                            time.sleep(2)
                            st.rerun()
                        except:
                            st.error("Erro ao salvar. Verifique sua conexão.")

            formulario_avaliacao()
