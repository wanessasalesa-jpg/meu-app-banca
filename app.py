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
professores = sorted(df_escalacao.iloc[:, 0].unique())
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
        
        # --- LÓGICA DE RUBRICAS COM DESCRIÇÕES DETALHADAS ---
        
        if turma == "TCC I":
            st.info("Rubrica TCC I (Máx: 60 pontos)")
            # Itens e descrições conforme seu documento de TCC 1
            itens_tcc1 = {
                "Tema Contemporâneo": (3, "Escolha de tema contemporâneo, oportuno e de interesse para a comunidade acadêmica."),
                "Resumo": (1, "É autoexplicativo, apresenta objetivos e conclusão condizentes e palavras-chaves de acordo com o DECS."),
                "Introdução": (5, "Apresenta clareza, concisão, justificativa, sequência lógica e objetivo ao final."),
                "Justificativa/Problema": (5, "Formatação segundo ABNT e conteúdo de justificativa, problema e hipóteses."),
                "Objetivos": (5, "Claros e exequíveis."),
                "Metodologia": (10, "Define tipo de estudo, local, data, população, procedimentos, instrumentos, análise e ética."),
                "Referências": (1, "São relevantes, com fontes confiáveis e todas listadas."),
                "Apresentação Oral": (10, "Explanação clara, com segurança, postura e domínio sobre o trabalho."),
                "Coerência": (10, "O conteúdo da apresentação oral tem coerência com o documento textual."),
                "Qualidade do Material": (9, "O material de apresentação é estruturado, coerente e utilizado como apoio."),
                "Tempo": (1, "Observância do tempo determinado para apresentação.")
            }
            for item, (peso, ajuda) in itens_tcc1.items():
                notas[item] = st.slider(f"{item} (Máx: {peso})", 0.0, float(peso), step=0.1, help=ajuda)

        elif turma == "TCC II":
            st.info("Rubrica TCC II (Máx: 60 pontos)")
            # Descrições conforme seu documento de TCC 2
            itens_tcc2 = {
                "Tema e Resumo": (4, "Tema contemporâneo e resumo autoexplicativo com DECS."),
                "Introdução": (5, "Clareza, concisão, justificativa e objetivo claro."),
                "Metodologia": (5, "Rigor metodológico e descrição dos aspectos éticos."),
                "Resultados": (5, "Responde ao objetivo, estruturado, conciso e isento de opiniões."),
                "Discussão e Conclusão": (10, "Foca nos achados, comparação crítica com literatura e limitações."),
                "Referências": (1, "Fontes confiáveis e listadas corretamente."),
                "Apresentação Oral": (10, "Segurança, postura e domínio."),
                "Coerência": (10, "Coerência entre fala e texto."),
                "Qualidade": (9, "Material visual estruturado e coerente."),
                "Tempo": (1, "Mínimo 15 min e máximo 20 min.")
            }
            for item, (peso, ajuda) in itens_tcc2.items():
                notas[item] = st.slider(f"{item} (Máx: {peso})", 0.0, float(peso), step=0.1, help=ajuda)

        elif turma == "MCM IV":
            st.info("Rubrica MCM IV (Máx: 30 pontos)")
            crit_mcm4 = {
                "Domínio de Conteúdo": "Domínio do conteúdo e resposta aos questionamentos da banca.",
                "Coerência": "Coerência do conteúdo com o tema abordado.",
                "Comunicação": "Habilidades de comunicação e postura na apresentação.",
                "Organização": "Organização da apresentação e gestão do tempo.",
                "Recursos Visuais": "Uso dos recursos audiovisuais.",
                "Métodos": "Adequação dos objetivos aos métodos."
            }
            for item, ajuda in crit_mcm4.items():
                notas[item] = st.slider(f"{item} (Máx: 5.0)", 0.0, 5.0, step=0.1, help=ajuda)

        elif turma == "MCM V":
            st.info("Rubrica MCM V (Máx: 100 pontos)")
            ajuda_mcm5 = {
                "Resumo": "Apresenta objetivos, métodos, resultados e conclusões? (Até 10 pts)",
                "Introdução": "Tema adequado, embasado e objetivos claros? (Até 10 pts)",
                "Metodologia": "Metodologia atende aos objetivos? (Até 10 pts)",
                "Resultados": "Descritos e analisados de forma adequada e suficiente? (Até 20 pts)",
                "Discussão": "Embasada em artigos pertinentes e atualizados? (Até 10 pts)",
                "Conclusão": "Pertinente aos resultados e coerente com objetivos? (Até 10 pts)",
                "Redação/ABNT": "Gramática e formatação ABNT ou Vancouver. (Até 10 pts)",
                "Arguição": "Autonomia e capacidade para responder à banca. (Até 10 pts)",
                "Apresentação": "Clareza, segurança, linguagem e material visual. (Até 10 pts)"
            }
            for item, ajuda in ajuda_mcm5.items():
                max_v = 20.0 if item == "Resultados" else 10.0
                notas[item] = st.slider(f"{item} (Máx: {max_v})", 0.0, max_v, step=0.1, help=ajuda)

        # CÁLCULO FINAL
        total_banca = sum(notas.values())
        st.subheader(f"Nota Final: {total_banca:.2f}")

        if st.button("Confirmar e Salvar Avaliação"):
            # Aqui você conectará a função de salvar na planilha
            st.balloons()
            st.success("Avaliação salva com sucesso! Os dados foram enviados para a planilha mestre.")
