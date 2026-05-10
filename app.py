import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# Configuração focada em dispositivos móveis
st.set_page_config(page_title="Avaliação Afya", layout="centered")

# Estilo CSS para melhorar a visualização em telas pequenas
st.markdown("""
    <style>
    .main {
        padding: 10px;
    }
    .stButton button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(aba, tempo_cache=120):
    return conn.read(worksheet=aba, ttl=tempo_cache)

# 1. CARREGAMENTO
try:
    df_escalacao = get_data("Escalacao", tempo_cache=300)
except:
    st.error("Erro ao carregar dados. Tente atualizar a página.")
    st.stop()

st.title("🎓 Avaliação de Bancas")

# --- ÁREA DE LOGIN (No centro, para facilitar no celular) ---
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    with st.container():
        st.write("### Identificação")
        email_input = st.text_input("Digite seu e-mail cadastrado:").strip().lower()
        if st.button("Acessar Sistema"):
            if email_input in df_escalacao['Email'].str.lower().unique():
                st.session_state.email = email_input
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("E-mail não encontrado. Verifique a grafia.")
    st.stop()

# --- SE CHEGOU AQUI, ESTÁ LOGADO ---
prof_dados = df_escalacao[df_escalacao['Email'].str.lower() == st.session_state.email].iloc[0]
nome_avaliador = prof_dados['Avaliador']

# Cabeçalho compacto para celular
col_logo, col_user = st.columns([1, 3])
with col_user:
    st.write(f"Olá, **Prof. {nome_avaliador}**")
    if st.button("Sair", key="btn_sair"):
        st.session_state.logado = False
        st.rerun()

st.divider()

# 2. SELEÇÃO DO GRUPO
try:
    df_respostas = get_data("Respostas", tempo_cache=10)
    feitos = df_respostas[df_respostas["Email_Avaliador"] == st.session_state.email]["Alunos"].tolist()
except:
    feitos = []

pendentes = df_escalacao[(df_escalacao['Email'].str.lower() == st.session_state.email) & (~df_escalacao['Alunos'].isin(feitos))]

if pendentes.empty:
    st.success("🎉 Todas as suas bancas foram avaliadas!")
else:
    lista_grupos = sorted(pendentes["Alunos"].tolist())
    aluno_selecionado = st.selectbox("🎯 Escolha o Grupo/Aluno:", [""] + lista_grupos)

    if aluno_selecionado:
        dados = pendentes[pendentes["Alunos"] == aluno_selecionado].iloc[0]
        turma_bruta = str(dados['Turma']).strip().upper()

        # Informações do Trabalho em um Expander (ocupa menos espaço)
        with st.expander("📖 Ver Detalhes do Trabalho"):
            st.write(f"**Título:** {dados['Titulo']}")
            st.write(f"**Orientador:** {dados['Orientador']}")
            st.write(f"**Turma:** {turma_bruta}")

        # --- FORMULÁRIO DE NOTAS ---
        st.write("### 📝 Critérios")
        
        # Lógica de Rubricas (Igual às versões anteriores)
        notas = {}
        if "TCC I" in turma_bruta and "TCC II" not in turma_bruta:
            rubrica = {"Tema Contemporâneo": 3, "Resumo": 1, "Introdução": 5, "Justificativa/Problema": 5, "Objetivos": 5, "Metodologia": 10, "Referências": 1, "Apresentação Oral": 10, "Coerência": 10, "Qualidade Visual": 9, "Tempo (10-15min)": 1}
            nota_max = 60
        elif "TCC II" in turma_bruta:
            rubrica = {"Tema e Resumo": 4, "Introdução": 5, "Metodologia": 5, "Resultados": 5, "Discussão e Conclusão": 10, "Referências": 1, "Apresentação Oral": 10, "Coerência": 10, "Qualidade Visual": 9, "Tempo (15-20min)": 1}
            nota_max = 60
        elif "MCM V" in turma_bruta:
            rubrica = {"Resumo": 10, "Introdução": 10, "Metodologia": 10, "Resultados": 20, "Discussão": 10, "Conclusão": 10, "Redação/ABNT": 10, "Arguição": 10, "Apresentação": 10}
            nota_max = 100
        else:
            rubrica = {"Domínio de Conteúdo": 5, "Coerência": 5, "Comunicação": 5, "Organização/Tempo": 5, "Recursos Visuais": 5, "Métodos": 5}
            nota_max = 30

        st.info(f"**Nota máxima: {nota_max} pts**")

        for item, p in rubrica.items():
            notas[item] = st.slider(f"{item} (0-{p})", 0, p, 0)

        total = sum(notas.values())
        st.markdown(f"## Total: {total} / {nota_max}")

        if st.button("🚀 GRAVAR AVALIAÇÃO"):
            with st.spinner("Enviando..."):
                try:
                    nova_linha = pd.DataFrame([{
                        "Avaliador": nome_avaliador, 
                        "Email_Avaliador": st.session_state.email,
                        "Alunos": aluno_selecionado, 
                        "Titulo": dados['Titulo'], 
                        "Nota_Final": total,
                        "Data_Hora": datetime.now().strftime("%d/%m/%Y %H:%M")
                    }])
                    df_atual = conn.read(worksheet="Respostas", ttl=0)
                    df_final = pd.concat([df_atual, nova_linha], ignore_index=True)
                    conn.update(worksheet="Respostas", data=df_final)
                    st.balloons()
                    st.success("✅ GRAVADO!")
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error("Erro na rede. Tente novamente.")
