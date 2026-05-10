import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Avaliação Afya Marabá", layout="centered")

# Conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Lendo a aba de Escalação
    df_escalacao = conn.read(worksheet="Escalacao")
except Exception as e:
    st.error(f"Erro ao ler a aba 'Escalacao'. Verifique se o nome está correto. Erro: {e}")
    st.stop()

st.title("🎓 Portal de Avaliação - Afya Marabá")

# 1. IDENTIFICAÇÃO DO AVALIADOR
professores = sorted(df_escalacao.iloc[:, 0].unique())
professor_logado = st.selectbox("Selecione seu nome:", [""] + list(professores))

if professor_logado:
    # Filtra grupos do professor (Coluna 0 é Avaliador)
    meus_grupos = df_escalacao[df_escalacao.iloc[:, 0] == professor_logado]
    st.write(f"### Olá, Prof. {professor_logado}!")
    
    # Seleção do Trabalho (Coluna 4 é Título)
    trabalho_selecionado = st.selectbox("Selecione o trabalho para avaliar:", [""] + meus_grupos.iloc[:, 4].tolist())

    if trabalho_selecionado:
        # Puxa dados do trabalho selecionado
        dados = meus_grupos[meus_grupos.iloc[:, 4] == trabalho_selecionado].iloc[0]
        st.success(f"📌 **Orientador(a):** {dados.iloc[1]}")
        
        with st.expander("Ver Detalhes do Grupo"):
            st.write(f"**Turma:** {dados.iloc[2]}")
            st.write(f"**Acadêmicos:** {dados.iloc[3]}")

        st.divider()
        turma = str(dados.iloc[2]).upper()
        notas = {}

        # --- LÓGICA DE RUBRICAS ---
        if "TCC I" in turma and "TCC II" not in turma:
            st.info("Rubrica TCC I (Máx: 60 pts)")
            max_v = 60.0
            itens = {
                "Tema": (3.0, "Tema contemporâneo e oportuno."),
                "Resumo": (1.0, "Objetivos, conclusão e DECS."),
                "Introdução": (5.0, "Clareza e justificativa."),
                "Justificativa/Problema": (5.0, "Formatação ABNT e conteúdo."),
                "Objetivos": (5.0, "Claros e exequíveis."),
                "Metodologia": (10.0, "Tipo de estudo, amostra e ética."),
                "Referências": (1.0, "Fontes confiáveis."),
                "Apresentação Oral": (10.0, "Segurança e domínio."),
                "Coerência": (10.0, "Coerência fala/texto."),
                "Qualidade Visual": (9.0, "Material estruturado."),
                "Tempo": (1.0, "Duração: 10-15 minutos.")
            }
            for k, (p, h) in itens.items():
                notas[k] = st.slider(f"{k} (Máx: {p})", 0.0, float(p), step=0.1, help=h)

        elif "TCC II" in turma:
            st.info("Rubrica TCC II (Máx: 60 pts)")
            max_v = 60.0
            itens = {
                "Tema/Resumo": (4.0, "Contemporaneidade e DECS."),
                "Introdução": (5.0, "Clareza e objetivo."),
                "Metodologia": (5.0, "Rigor e ética."),
                "Resultados": (5.0, "Responde ao objetivo."),
                "Discussão/Conclusão": (10.0, "Comparação crítica."),
                "Referências": (1.0, "Fontes listadas."),
                "Apresentação Oral": (10.0, "Segurança e domínio."),
                "Coerência": (10.0, "Fala coerente com texto."),
                "Qualidade Visual": (9.0, "Material estruturado."),
                "Tempo": (1.0, "Duração: 15-20 minutos.")
            }
            for k, (p, h) in itens.items():
                notas[k] = st.slider(f"{k} (Máx: {p})", 0.0, float(p), step=0.1, help=h)

        elif "MCM IV" in turma:
            st.info("Rubrica MCM IV (Máx: 30 pts)")
            max_v = 30.0
            crit = {
                "Domínio": (5.0, "Resposta à banca."),
                "Coerência": (5.0, "Coerência com o tema."),
                "Comunicação": (5.0, "Postura e fala."),
                "Organização/Tempo": (5.0, "Duração: 10-15 min."),
                "Recursos": (5.0, "Audiovisuais."),
                "Métodos": (5.0, "Objetivos x Métodos.")
            }
            for k, (p, h) in crit.items():
                notas[k] = st.slider(f"{k} (Máx: {p})", 0.0, float(p), step=0.1, help=h)

        elif "MCM V" in turma:
            st.info("Rubrica MCM V (Máx: 100 pts)")
            max_v = 100.0
            itens = {
                "Resumo": 10.0, "Introdução": 10.0, "Metodologia": 10.0, 
                "Resultados": 20.0, "Discussão": 10.0, "Conclusão": 10.0, 
                "Redação": 10.0, "Arguição": 10.0, "Apresentação": 10.0
            }
            for k, p in itens.items():
                h = "Duração: 15-20 minutos." if k == "Apresentação" else ""
                notas[k] = st.slider(f"{k} (Máx: {p})", 0.0, float(p), step=0.1, help=h)

        st.divider()
        
        # --- CÁLCULO E AVISOS ---
        total_banca = sum(notas.values())
        st.subheader(f"Nota Final: {total_banca:.2f} / {max_v}")

        if total_banca < (max_v * 0.6):
            st.warning("⚠️ Nota reprobatória (abaixo de 60%).")
        
        if any(v == 0.0 for v in notas.values()):
            st.error("❗ Atenção: Há itens com nota ZERO. Verifique se avaliou tudo.")

        if total_banca > max_v:
            st.error(f"❌ A nota ({total_banca:.2f}) excede o máximo ({max_v})!")
            pode_salvar = False
        else:
            pode_salvar = True

        # --- BOTÃO SALVAR ---
        if st.button("Confirmar e Salvar Avaliação") and pode_salvar:
            try:
                nova_linha = pd.DataFrame([{
                    "Avaliador": professor_logado,
                    "Trabalho": trabalho_selecionado,
                    "Turma": turma,
                    "Nota_Final": total_banca
                }])
                conn.create(worksheet="Respostas", data=nova_linha)
                st.balloons()
                st.success("Avaliação salva na aba 'Respostas'!")
            except Exception as e:
                st.error(f"Erro ao salvar. Verifique se a aba 'Respostas' existe. Erro: {e}")
