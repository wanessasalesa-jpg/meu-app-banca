import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Avaliação Afya Marabá", layout="centered")

# Conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Lê a planilha (ajustado para ser o mais flexível possível)
    df_escalacao = conn.read()
except:
    st.error("Erro ao ler a planilha. Verifique os Secrets e se o compartilhamento está como 'Qualquer pessoa com o link'.")
    st.stop()

st.title("🎓 Portal de Avaliação - Afya Marabá")

# 1. IDENTIFICAÇÃO DO AVALIADOR
professores = sorted(df_escalacao.iloc[:, 0].unique())
professor_logado = st.selectbox("Selecione seu nome:", [""] + list(professores))

if professor_logado:
    meus_grupos = df_escalacao[df_escalacao.iloc[:, 0] == professor_logado]
    st.write(f"### Olá, Prof. {professor_logado}!")
    
    trabalho_selecionado = st.selectbox("Selecione o trabalho:", [""] + meus_grupos.iloc[:, 4].tolist())

    if trabalho_selecionado:
        dados = meus_grupos[meus_grupos.iloc[:, 4] == trabalho_selecionado].iloc[0]
        st.success(f"📌 **Orientador(a):** {dados.iloc[1]}")
        
        with st.expander("Detalhes do Grupo"):
            st.write(f"**Turma:** {dados.iloc[2]} | **Acadêmicos:** {dados.iloc[3]}")

        st.divider()
        turma = str(dados.iloc[2]).upper()
        notas = {}

        # --- LÓGICA DAS RUBRICAS ---
        
        # TCC I
        if "TCC I" in turma and "TCC II" not in turma:
            st.info("Rubrica TCC I (Máx: 60 pontos)")
            itens = {
                "Tema Contemporâneo": (3.0, "Escolha de tema contemporâneo e oportuno."),
                "Resumo": (1.0, "Autoexplicativo, objetivos/conclusão condizentes, DECS."),
                "Introdução": (5.0, "Clareza, concisão e justificativa."),
                "Justificativa/Problema": (5.0, "Formatação ABNT e conteúdo."),
                "Objetivos": (5.0, "Claros e exequíveis."),
                "Metodologia": (10.0, "Tipo de estudo, amostra e ética."),
                "Referências": (1.0, "Fontes confiáveis."),
                "Apresentação Oral": (10.0, "Segurança e domínio."),
                "Coerência": (10.0, "Fala coerente com o texto."),
                "Qualidade Visual": (9.0, "Material de apoio estruturado."),
                "Tempo": (1.0, "Duração: 10-15 minutos.")
            }
            for k, (p, h) in itens.items():
                notas[k] = st.slider(f"{k} (Máx: {p})", 0.0, float(p), step=0.1, help=h)

        # TCC II
        elif "TCC II" in turma:
            st.info("Rubrica TCC II (Máx: 60 pontos)")
            itens = {
                "Tema e Resumo": (4.0, "Contemporaneidade e DECS."),
                "Introdução": (5.0, "Clareza e objetivo."),
                "Metodologia": (5.0, "Rigor e ética."),
                "Resultados": (5.0, "Responde ao objetivo e sem opiniões."),
                "Discussão/Conclusão": (10.0, "Comparação crítica e limitações."),
                "Referências": (1.0, "Fontes listadas."),
                "Apresentação Oral": (10.0, "Domínio e postura."),
                "Coerência": (10.0, "Coerência fala/texto."),
                "Qualidade Visual": (9.0, "Material estruturado."),
                "Tempo": (1.0, "Duração: 15-20 minutos.")
            }
            for k, (p, h) in itens.items():
                notas[k] = st.slider(f"{k} (Máx: {p})", 0.0, float(p), step=0.1, help=h)

        # MCM IV
        elif "MCM IV" in turma:
            st.info("Rubrica MCM IV (Máx: 30 pontos)")
            crit = {
                "Domínio": (5.0, "Resposta aos questionamentos."),
                "Coerência": (5.0, "Coerência com o tema."),
                "Comunicação": (5.0, "Postura e fala."),
                "Organização/Tempo": (5.0, "Gestão do tempo (10-15 min)."),
                "Recursos": (5.0, "Audiovisuais."),
                "Métodos": (5.0, "Objetivos x Métodos.")
            }
            for k, (p, h) in crit.items():
                notas[k] = st.slider(f"{k} (Máx: {p})", 0.0, float(p), step=0.1, help=h)

        # MCM V
        elif "MCM V" in turma:
            st.info("Rubrica MCM V (Máx: 100 pontos)")
            itens = {
                "Resumo": 10.0, "Introdução": 10.0, "Metodologia": 10.0, 
                "Resultados": 20.0, "Discussão": 10.0, "Conclusão": 10.0, 
                "Redação": 10.0, "Arguição": 10.0, "Apresentação": 10.0
            }
            for k, p in itens.items():
                h = "Duração: 15-20 minutos." if k == "Apresentação" else ""
                notas[k] = st.slider(f"{k} (Máx: {p})", 0.0, float(p), step=0.1, help=h)

        # --- FINALIZAÇÃO ---
        total = sum(notas.values())
        st.subheader(f"Nota Final: {total:.2f}")
        
        if st.button("Confirmar Avaliação"):
            st.balloons()
            st.success("Avaliação enviada com sucesso!")
