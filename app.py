import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Avaliação Afya Marabá", layout="centered")

# Conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 1. LEITURA DOS DADOS ---
try:
    # ttl=0 garante que ele pegue os dados mais recentes sem cache
    df_escalacao = conn.read(worksheet="Escalacao", ttl=0)
except Exception as e:
    st.error(f"Erro ao ler a aba 'Escalacao'. Verifique o nome na sua planilha. Erro: {e}")
    st.stop()

st.title("🎓 Portal de Avaliação - Afya Marabá")

# --- 2. IDENTIFICAÇÃO DO AVALIADOR ---
professores = sorted(df_escalacao.iloc[:, 0].unique())
professor_logado = st.selectbox("Selecione seu nome:", [""] + list(professores))

if professor_logado:
    meus_grupos = df_escalacao[df_escalacao["Avaliador"] == professor_logado]
    st.write(f"### Olá, Prof. {professor_logado}!")
    
    trabalho_selecionado = st.selectbox("Selecione o trabalho para avaliar:", 
                                        [""] + meus_grupos["Título"].tolist())

    if trabalho_selecionado:
        # --- 3. TRAVA DE DUPLICIDADE ---
        ja_avaliado = False
        try:
            df_respostas = conn.read(worksheet="Respostas", ttl=0)
            if not df_respostas.empty:
                check = df_respostas[(df_respostas["Avaliador"] == professor_logado) & 
                                     (df_respostas["Trabalho"] == trabalho_selecionado)]
                ja_avaliado = not check.empty
        except:
            ja_avaliado = False

        if ja_avaliado:
            st.warning(f"✅ Você já enviou sua avaliação para o trabalho: **{trabalho_selecionado}**.")
            st.info("Para correções, entre em contato com a coordenação.")
        else:
            # --- 4. MOSTRAR DETALHES DO GRUPO ---
            dados = meus_grupos[meus_grupos["Título"] == trabalho_selecionado].iloc[0]
            st.success(f"📌 **Orientador(a):** {dados['Orientador']}")
            with st.expander("Ver Detalhes do Grupo"):
                st.write(f"**Turma:** {dados['Turma']}")
                st.write(f"**Acadêmicos:** {dados['Alunos']}")
                st.write(f"**Horário:** {dados['Horário']}")

            st.divider()
            turma = dados['Turma']
            notas = {}
            # Define o limite para os alertas visuais
            max_v = 60.0 if "TCC" in turma else (30.0 if "MCM IV" in turma else 100.0)
            
            # --- 5. RENDERIZAÇÃO DAS RUBRICAS (Suas descrições mantidas) ---
            if turma == "TCC I":
                st.info("Rubrica TCC I (Máx: 60 pontos)")
                itens = {
                    "Tema Contemporâneo": (3, "Escolha de tema contemporâneo e oportuno."),
                    "Resumo": (1, "Objetivos, conclusão e DECS."),
                    "Introdução": (5, "Clareza, justificativa e sequência."),
                    "Justificativa/Problema": (5, "Formatação ABNT e conteúdo."),
                    "Objetivos": (5, "Claros e exequíveis."),
                    "Metodologia": (10, "Tipo, população, análise e ética."),
                    "Referências": (1, "Fontes confiáveis."),
                    "Apresentação Oral": (10, "Segurança e domínio."),
                    "Coerência": (10, "Coerência fala/texto."),
                    "Qualidade do Material": (9, "Material estruturado."),
                    "Tempo": (1, "10 a 15 minutos.")
                }
                for k, (p, h) in itens.items():
                    notas[k] = st.slider(f"{k} (Máx: {p})", 0.0, float(p), step=0.1, help=h)

            elif turma == "TCC II":
                st.info("Rubrica TCC II (Máx: 60 pontos)")
                itens = {
                    "Tema e Resumo": (4, "Contemporaneidade e DECS."),
                    "Introdução": (5, "Justificativa e objetivo."),
                    "Metodologia": (5, "Rigor e ética."),
                    "Resultados": (5, "Responde ao objetivo."),
                    "Discussão e Conclusão": (10, "Comparação crítica."),
                    "Referências": (1, "Fontes listadas."),
                    "Apresentação Oral": (10, "Segurança e domínio."),
                    "Coerência": (10, "Fala coerente com texto."),
                    "Qualidade": (9, "Visual estruturado."),
                    "Tempo": (1, "15 a 20 minutos.")
                }
                for k, (p, h) in itens.items():
                    notas[k] = st.slider(f"{k} (Máx: {p})", 0.0, float(p), step=0.1, help=h)

            elif turma == "MCM IV":
                st.info("Rubrica MCM IV (Máx: 30 pontos)")
                crit = {"Domínio": 5.0, "Coerência": 5.0, "Comunicação": 5.0, "Organização": 5.0, "Recursos": 5.0, "Métodos": 5.0}
                for k, p in crit.items():
                    notas[k] = st.slider(f"{k} (Máx: {p})", 0.0, p, step=0.1)

            elif turma == "MCM V":
                st.info("Rubrica MCM V (Máx: 100 pontos)")
                itens = {"Resumo": 10.0, "Introdução": 10.0, "Metodologia": 10.0, "Resultados": 20.0, "Discussão": 10.0, "Conclusão": 10.0, "Redação": 10.0, "Arguição": 10.0, "Apresentação": 10.0}
                for k, p in itens.items():
                    notas[k] = st.slider(f"{k} (Máx: {p})", 0.0, p, step=0.1)

            # --- 6. CÁLCULO E SALVAMENTO ---
            total_banca = sum(notas.values())
            st.subheader(f"Nota Final: {total_banca:.2f}")

            # Alertas Visuais
            if total_banca < (max_v * 0.6):
                st.warning("⚠️ Nota abaixo da média (reprobatória).")
            
            if any(v == 0.0 for v in notas.values()):
                st.error("❗ Atenção: Há itens com nota zero. Verifique se avaliou tudo.")

            if st.button("Confirmar e Salvar Avaliação"):
                if total_banca > (max_v + 0.1):
                    st.error(f"Erro: A nota total ({total_banca}) excede o limite da turma!")
                else:
                    try:
                        # Prepara a linha de dados
                        nova_linha = pd.DataFrame([{
                            "Avaliador": professor_logado,
                            "Trabalho": trabalho_selecionado,
                            "Turma": turma,
                            "Nota_Final": total_banca
                        }])
                        # Salva na aba Respostas
                        conn.create(worksheet="Respostas", data=nova_linha)
                        st.balloons()
                        st.success("Avaliação salva com sucesso na planilha!")
                        st.info("Você já pode selecionar outro trabalho ou fechar o app.")
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}. Verifique se a aba 'Respostas' existe.")
