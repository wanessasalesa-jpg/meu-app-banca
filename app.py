import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Avaliação Afya Marabá", layout="centered")

# Conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Lê a primeira aba da planilha independentemente do nome
    df_escalacao = conn.read()
except:
    st.error("Erro ao ler a planilha. Verifique os Secrets e se o compartilhamento está como 'Qualquer pessoa com o link'.")
    st.stop()

st.title("🎓 Portal de Avaliação - Afya Marabá")

# 1. IDENTIFICAÇÃO DO AVALIADOR (Coluna 0)
professores = sorted(df_escalacao.iloc[:, 0].unique())
professor_logado = st.selectbox("Selecione seu nome:", [""] + list(professores))

if professor_logado:
    meus_grupos = df_escalacao[df_escalacao.iloc[:, 0] == professor_logado]
    st.write(f"### Olá, Prof. {professor_logado}!")
    
    # Seleção do Trabalho (Coluna 4)
    trabalho_selecionado = st.selectbox("Selecione o trabalho para avaliar:", [""] + meus_grupos.iloc[:, 4].tolist())

    if trabalho_selecionado:
        dados = meus_grupos[meus_grupos.iloc[:, 4] == trabalho_selecionado].iloc[0]
        
        # Exibe o Orientador (Coluna 1)
        st.success(f"📌 **Orientador(a):** {dados.iloc[1]}")
        with st.expander("Ver Detalhes do Grupo"):
            st.write(f"**Turma:** {dados.iloc[2]}")
            st.write(f"**Acadêmicos:** {dados.iloc[3]}")

        st.divider()
        turma = str(dados.iloc[2])
        notas = {}

        # --- RUBRICA TCC I ---
        if "TCC I" in turma and "TCC II" not in turma:
            st.info("Rubrica TCC I (Máx: 60 pontos)")
            itens = {
                "Tema Contemporâneo": (3.0, "Escolha de tema contemporâneo, oportuno e de interesse."),
                "Resumo": (1.0, "Autoexplicativo, objetivos e conclusão condizentes, palavras-chaves DECS."),
                "Introdução": (5.0, "Clareza, concisão, justificativa e sequência lógica."),
                "Justificativa/Problema": (5.0, "Formatação ABNT e conteúdo de justificativa/hipóteses."),
                "Objetivos": (5.0, "Claros e exequíveis."),
                "Metodologia": (10.0, "Tipo de estudo, local, data, amostra, procedimentos e ética."),
                "Referências": (1.0, "Fontes confiáveis e listadas."),
                "Apresentação Oral": (10.0, "Segurança, postura e domínio."),
                "Coerência": (10.0, "Conteúdo oral coerente com o texto."),
                "Qualidade Visual": (9.0, "Material de apoio estruturado."),
                "Tempo": (1.0, "Duração permitida: entre 10 e 15 minutos.")
            }
            for k, (p, h) in itens.items():
                notas[k] = st.slider(f"{k} (Máx: {p})", 0.0, p, step=0.1, help=h)

        # --- RUBRICA TCC II ---
        elif "TCC II" in turma:
            st.info("Rubrica TCC II (Máx: 60 pontos)")
            itens = {
                "Tema e Resumo": (4.0, "Tema contemporâneo e resumo com DECS."),
                "Introdução": (5.0, "Clareza, concisão e objetivo claro."),
                "Metodologia": (5.0, "Rigor metodológico e descrição ética."),
                "Resultados": (5.0, "Responde ao objetivo, estruturado e isento de opiniões."),
                "Discussão e Conclusão": (10.0, "Interpretação, comparação crítica e limitações."),
                "Referências": (1.0, "Fontes confiáveis e relevantes."),
                "Apresentação Oral": (10.0, "Segurança, postura e domínio."),
                "Coerência": (10.0, "Coerência entre fala e documento."),
                "Qualidade Visual": (9.0, "Material estruturado e coerente."),
                "Tempo": (1.0, "Duração permitida: entre 15 e 20 minutos.")
            }
            for k, (p, h) in itens.items():
                notas[k] = st.slider(f"{k} (Máx: {p})", 0.0, p, step=0.1, help=h)

        # --- RUBRICA MCM IV ---
        elif "MCM IV" in turma:
            st.info("Rubrica MCM IV (Máx: 30 pontos)")
            crit = {
                "Domínio de Conteúdo": (5.0, "Domínio e resposta aos questionamentos da banca."),
                "Coerência": (5.0, "Coerência com o tema abordado."),
                "Comunicação": (5.0, "Habilidades de comunicação e postura."),
                "Organização e Tempo": (5.0, "Gestão da apresentação. Duração: 10-15 minutos."),
                "Recursos Visuais": (5.0, "Uso de audiovisuais."),
                "Adequação Métodos": (5.0, "Objetivos adequados aos métodos.")
            }
            for k, (p, h) in crit.items():
                notas[k] = st.slider(f"{k} (Máx: {p})", 0.0, p, step=0.1, help=h)

        # --- RUBRICA MCM V ---
        elif "MCM V" in turma:
            st.info("Rubrica MCM V (Máx: 100 pontos)")
            itens_m5 = {
                "Resumo": (10.0, "Objetivos, métodos, resultados e conclusões presentes?"),
                "Introdução": (10.0, "Tema embasado e objetivos claros?"),
                "Metodologia": (10.0, "Metodologia atende aos objetivos?"),
                "Resultados": (20.0, "Descritos e analisados de forma suficiente?"),
                "Discussão": (10.0, "Embasada em artigos atualizados?"),
                "Conclusão": (10.0, "Coerente com os objetivos e resultados?"),
                "Redação/ABNT": (10.0, "Gramática e formatação ABNT/Vancouver."),
                "Arguição": (10.0, "Capacidade de responder à banca."),
                "Apresentação/Tempo": (10.0, "Clareza e segurança. Duração: 15-20 minutos.")
            }
            for k, (p, h) in itens_m5.items():
                notas[k] = st.slider(f"{k} (Máx: {p})", 0.0, p, step=0.1, help=h)

        # --- CÁLCULO FINAL ---
        total = sum(notas.values())
        st.subheader(f"Nota Final: {total:.2f}")
        
        if st.button("Confirmar Avaliação"):
            st.balloons()
            st.success(f"Avaliação registrada com sucesso!")
