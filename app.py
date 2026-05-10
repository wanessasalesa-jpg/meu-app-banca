import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Avaliação Afya Marabá", layout="centered")

conn = st.connection("gsheets", type=GSheetsConnection)

# --- LEITURA DA ESCALACAO ---
try:
    df_escalacao = conn.read(worksheet="Escalacao", ttl=0)
except Exception as e:
    st.error(f"Erro ao ler a aba 'Escalacao'. Verifique se o nome está correto na planilha. Erro: {e}")
    st.stop()

st.title("🎓 Portal de Avaliação - Afya Marabá")

# 1. IDENTIFICAÇÃO DO AVALIADOR
professores = sorted(df_escalacao.iloc[:, 0].unique())
professor_logado = st.selectbox("Selecione seu nome:", [""] + list(professores))

if professor_logado:
    meus_grupos = df_escalacao[df_escalacao["Avaliador"] == professor_logado]
    st.write(f"### Olá, Prof. {professor_logado}!")
    
    trabalho_selecionado = st.selectbox("Selecione o trabalho para avaliar:", 
                                        [""] + meus_grupos["Título"].tolist())

    if trabalho_selecionado:
        # --- TRAVA DE DUPLICIDADE (REFORMULADA PARA EVITAR ERRO 400) ---
        ja_avaliado = False
        try:
            # Tenta ler as respostas já enviadas com cache zero para ser tempo real
            df_respostas = conn.read(worksheet="Respostas", ttl=0)
            if not df_respostas.empty:
                check = df_respostas[(df_respostas["Avaliador"] == professor_logado) & 
                                     (df_respostas["Trabalho"] == trabalho_selecionado)]
                ja_avaliado = not check.empty
        except:
            # Se a aba 'Respostas' não existir ou estiver inacessível, 
            # o app apenas segue sem a trava para não dar erro 400.
            ja_avaliado = False

        if ja_avaliado:
            st.warning(f"✅ Você já enviou sua avaliação para: **{trabalho_selecionado}**.")
            st.info("Para correções, procure a coordenação.")
        else:
            # --- SEÇÃO DE AVALIAÇÃO ---
            dados = meus_grupos[meus_grupos["Título"] == trabalho_selecionado].iloc[0]
            st.success(f"📌 **Orientador(a):** {dados['Orientador']}")
            
            with st.expander("Ver Detalhes"):
                st.write(f"**Turma:** {dados['Turma']} | **Horário:** {dados['Horário']}")
                st.write(f"**Acadêmicos:** {dados['Alunos']}")

            st.divider()
            turma = str(dados['Turma'])
            notas = {}
            max_v = 60.0 if "TCC" in turma else (30.0 if "MCM IV" in turma else 100.0)

            # --- RENDERIZAÇÃO DAS RUBRICAS ---
            if "TCC I" in turma and "TCC II" not in turma:
                st.info("Rubrica TCC I (Máx: 60 pts)")
                # (Mantendo seus itens configurados anteriormente)
                itens_tcc1 = {"Tema": 3.0, "Resumo": 1.0, "Introdução": 5.0, "Metodologia": 10.0, "Objetivos": 5.0, "Apresentação": 10.0, "Coerência": 10.0, "Qualidade": 9.0, "Tempo (10-15min)": 7.0}
                for k, p in itens_tcc1.items():
                    h = "Duração: 10-15 min" if k == "Tempo (10-15min)" else ""
                    notas[k] = st.slider(f"{k} (Máx: {p})", 0.0, p, step=0.1, help=h)

            elif "TCC II" in turma:
                st.info("Rubrica TCC II (Máx: 60 pts)")
                itens_tcc2 = {"Tema/Resumo": 4.0, "Introdução": 5.0, "Metodologia": 5.0, "Resultados": 5.0, "Discussão": 10.0, "Apresentação": 10.0, "Coerência": 10.0, "Qualidade": 10.0, "Tempo (15-20min)": 1.0}
                for k, p in itens_tcc2.items():
                    h = "Duração: 15-20 min" if k == "Tempo (15-20min)" else ""
                    notas[k] = st.slider(f"{k} (Máx: {p})", 0.0, p, step=0.1, help=h)

            elif "MCM IV" in turma:
                st.info("Rubrica MCM IV (Máx: 30 pts)")
                crit_mcm4 = {"Domínio": 5.0, "Coerência": 5.0, "Comunicação": 5.0, "Organização (10-15min)": 5.0, "Recursos": 5.0, "Métodos": 5.0}
                for k, p in crit_mcm4.items():
                    notas[k] = st.slider(f"{k} (Máx: {p})", 0.0, p, step=0.1)

            elif "MCM V" in turma:
                st.info("Rubrica MCM V (Máx: 100 pts)")
                itens_m5 = {"Resumo": 10.0, "Introdução": 10.0, "Metodologia": 10.0, "Resultados": 20.0, "Discussão": 10.0, "Conclusão": 10.0, "Redação": 10.0, "Arguição": 10.0, "Apresentação (15-20min)": 10.0}
                for k, p in itens_m5.items():
                    notas[k] = st.slider(f"{k} (Máx: {p})", 0.0, p, step=0.1)

            st.divider()
            total_banca = sum(notas.values())
            st.subheader(f"Nota Final: {total_banca:.2f}")

            # ALERTAS VISUAIS
            if total_banca < (max_v * 0.6):
                st.warning("⚠️ Nota abaixo da média.")
            
            pode_salvar = True
            if total_banca > (max_v + 0.01): # Pequena margem para erro de arredondamento
                st.error(f"❌ A nota ({total_banca:.2f}) excede o limite de {max_v}!")
                pode_salvar = False

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
                    st.success("Avaliação salva com sucesso!")
                    st.info("Atualize a página para avaliar outro trabalho.")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}. Verifique se a aba 'Respostas' é editável.")
