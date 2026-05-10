import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Avaliação Afya Marabá", layout="centered")

# Conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df_escalacao = conn.read(worksheet="Escalacao")
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
        
        if turma == "TCC I":
            st.info("Rubrica TCC I (Máx: 60 pontos)")
            # Itens conforme seu documento "FICHA AVALIAÇÃO PROJETO BANCA TCC 1"
            itens = {
                "Tema Contemporâneo": 3, "Resumo": 1, "Introdução": 5,
                "Justificativa/Problema": 5, "Objetivos": 5, "Metodologia": 10,
                "Referências": 1, "Apresentação Oral": 10, "Coerência": 10,
                "Qualidade do Material": 9, "Tempo": 1
            }
            for item, peso in itens.items():
                val = st.select_slider(f"{item} (Peso {peso})", options=["Não", "Parcial", "Sim"])
                mult = 1.0 if val == "Sim" else (0.5 if val == "Parcial" else 0.0)
                notas[item] = mult * peso

        elif turma == "TCC II":
            st.info("Rubrica TCC II (Máx: 60 pontos)")
            # Itens conforme seu documento "FICHAS AVALIAÇÃO TCC 2"
            itens = {
                "Tema": 3, "Resumo": 1, "Introdução": 5, "Metodologia": 5,
                "Resultados": 5, "Discussão/Conclusão": 10, "Referências": 1,
                "Apresentação Oral": 10, "Coerência": 10, "Qualidade": 9, "Tempo": 1
            }
            for item, peso in itens.items():
                val = st.select_slider(f"{item} (Peso {peso})", options=["Não", "Parcial", "Sim"])
                mult = 1.0 if val == "Sim" else (0.5 if val == "Parcial" else 0.0)
                notas[item] = mult * peso

        elif turma == "MCM IV":
            st.info("Rubrica MCM IV (Máx: 30 pontos)")
            # Baseado no documento "FICHA DE AVALIAÇÃO DE APRESENTAÇÃO ORAL"
            crit = ["Domínio de Conteúdo", "Coerência com Tema", "Comunicação/Postura", 
                    "Organização/Tempo", "Recursos Visuais", "Adequação Métodos"]
            for c in crit:
                notas[c] = st.radio(f"{c}:", [5, 3, 0], horizontal=True, 
                                    format_func=lambda x: f"{x} pts")

        elif turma == "MCM V":
            st.info("Rubrica MCM V (Máx: 100 pontos)")
            # Baseado no documento "RUBRICA DE AVALIAÇÃO banca MCM 5"
            notas["Resumo"] = st.slider("Resumo", 0, 10)
            notas["Introdução"] = st.slider("Introdução", 0, 10)
            notas["Metodologia"] = st.slider("Metodologia", 0, 10)
            notas["Resultados"] = st.slider("Resultados", 0, 20)
            notas["Discussão"] = st.slider("Discussão", 0, 10)
            notas["Conclusão"] = st.slider("Conclusão", 0, 10)
            notas["Redação/ABNT"] = st.slider("Redação/ABNT", 0, 10)
            notas["Arguição"] = st.slider("Arguição", 0, 10)
            notas["Apresentação"] = st.slider("Apresentação", 0, 10)

        # CÁLCULO FINAL
        total_banca = sum(notas.values())
        st.subheader(f"Nota Final: {total_banca:.2f}")

        if st.button("Confirmar e Salvar Avaliação"):
            # Aqui você conectará a função de salvar na planilha
            st.balloons()
            st.success("Avaliação salva com sucesso! Os dados foram enviados para a planilha mestre.")
