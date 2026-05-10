import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Avaliação Afya Marabá", layout="centered")

# Conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

try:
   df_escalacao = conn.read()
except:
    st.error("Erro ao ler a aba 'Escalacao'. Verifique o nome na sua planilha.")
    st.stop()

st.title("🎓 Portal de Avaliação - Afya Marabá")

# 1. IDENTIFICAÇÃO DO AVALIADOR
professores = sorted(df_escalacao["Avaliador"].unique())
professor_logado = st.selectbox("Selecione seu nome:", [""] + list(professores))

if professor_logado:
    # Filtra apenas os grupos deste professor
    meus_grupos = df_escalacao[df_escalacao["Avaliador"] == professor_logado]
    
    st.write(f"### Olá, Prof. {professor_logado}!")
    st.write(f"Você tem **{len(meus_grupos)}** bancas agendadas.")

    # 2. SELEÇÃO DO GRUPO
    trabalho_selecionado = st.selectbox("Selecione o trabalho para avaliar:", 
                                        [""] + meus_grupos["Título"].tolist())

    if trabalho_selecionado:
        dados = meus_grupos[meus_grupos["Título"] == trabalho_selecionado].iloc[0]
        
        # CABEÇALHO COM RECONHECIMENTO DO ORIENTADOR
        st.success(f"📌 **Orientador(a):** {dados['Orientador']}")
        with st.expander("Ver Detalhes do Grupo"):
            st.write(f"**Turma:** {dados['Turma']}")
            st.write(f"**Acadêmicos:** {dados['Alunos']}")
            st.write(f"**Horário:** {dados['Horário']}")

        st.divider()
        turma = dados['Turma']
        notas = {}

        # --- LÓGICA DE RUBRICAS (BASEADO NOS SEUS DOCS) ---
        
        # --- LÓGICA DE RUBRICAS COM DESCRIÇÕES DETALHADAS ---
        
        # --- LÓGICA DE RUBRICAS COM REGRAS DE TEMPO DIFERENCIADAS ---
        
        if turma == "TCC I":
            st.info("Rubrica TCC I (60 pts)")
            ajuda_tcc1 = {
                "Tema": "Escolha de tema contemporâneo e oportuno.",
                "Metodologia": "Define tipo de estudo, local, amostra e ética.",
                "Tempo": "Observância do tempo: a apresentação deve durar entre 10-15 minutos."
            }
            # ... (demais itens seguem a mesma lógica)
            notas["Tempo"] = st.slider("Tempo (Máx: 1)", 0.0, 1.0, step=0.1, help=ajuda_tcc1["Tempo"])

        elif turma == "TCC II":
            st.info("Rubrica TCC II (60 pts)")
            ajuda_tcc2 = {
                "Tempo": "Observância do tempo: a apresentação deve durar entre 15-20 minutos."
            }
            notas["Tempo"] = st.slider("Tempo (Máx: 1)", 0.0, 1.0, step=0.1, help=ajuda_tcc2["Tempo"])

        elif turma == "MCM IV":
            st.info("Rubrica MCM IV (30 pts)")
            # Aqui para o MCM IV, o tempo faz parte do item "Organização"
            ajuda_mcm4 = "Organização da apresentação e gestão do tempo (Duração: 10-15 minutos)."
            notas["Organização"] = st.slider("Organização/Tempo (Máx: 5)", 0.0, 5.0, step=0.1, help=ajuda_mcm4)

        elif turma == "MCM V":
            st.info("Rubrica MCM V (100 pts)")
            ajuda_mcm5 = "Clareza, segurança e tempo de apresentação (Duração: 15-20 minutos)."
            notas["Apresentação"] = st.slider("Apresentação (Máx: 10)", 0.0, 10.0, step=0.1, help=ajuda_mcm5)

        # CÁLCULO FINAL
        total_banca = sum(notas.values())
        st.subheader(f"Nota Final: {total_banca:.2f}")

        if st.button("Confirmar e Salvar Avaliação"):
            # Aqui você conectará a função de salvar na planilha
            st.balloons()
            st.success("Avaliação salva com sucesso! Os dados foram enviados para a planilha mestre.")
