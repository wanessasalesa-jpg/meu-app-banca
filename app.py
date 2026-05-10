import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Avaliação Afya Marabá", layout="centered")

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df_escalacao = conn.read(worksheet="Escalacao")
except Exception as e:
    st.error(f"Erro ao ler a aba 'Escalacao'. Erro: {e}")
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
        # --- TRAVA DE DUPLICIDADE ---
        try:
            # Tenta ler as respostas já enviadas
            df_respostas = conn.read(worksheet="Respostas")
            # Verifica se já existe uma entrada para este professor e este trabalho
            ja_avaliado = not df_respostas[(df_respostas["Avaliador"] == professor_logado) & 
                                          (df_respostas["Trabalho"] == trabalho_selecionado)].empty
        except:
            ja_avaliado = False # Caso a aba esteja vazia ou não exista ainda

        if ja_avaliado:
            st.warning(f"✅ Você já enviou sua avaliação para o trabalho: **{trabalho_selecionado}**.")
            st.info("Caso precise alterar a nota, entre em contato com a coordenação para editar a planilha.")
        else:
            # --- FLUXO NORMAL DE AVALIAÇÃO ---
            dados = meus_grupos[meus_grupos["Título"] == trabalho_selecionado].iloc[0]
            st.success(f"📌 **Orientador(a):** {dados['Orientador']}")
            
            with st.expander("Ver Detalhes"):
                st.write(f"**Turma:** {dados['Turma']} | **Horário:** {dados['Horário']}")
                st.write(f"**Acadêmicos:** {dados['Alunos']}")

            st.divider()
            turma = dados['Turma']
            notas = {}
            max_v = 60.0 if "TCC" in turma else (30.0 if "MCM IV" in turma else 100.0)

            # --- RUBRICAS (Resumo para o exemplo, mantenha as suas completas aqui) ---
            if turma == "TCC I":
                st.info("Rubrica TCC I (Máx: 60)")
                # Aqui você mantém todos os itens da rubrica que já configuramos
                itens_tcc1 = {"Tema": 3, "Resumo": 1, "Introdução": 5, "Metodologia": 10, "Apresentação": 10, "Coerência": 10, "Qualidade": 9, "Tempo (10-15min)": 2}
                for item, peso in itens_tcc1.items():
                    notas[item] = st.slider(f"{item} (Máx: {peso})", 0.0, float(peso), step=0.1)
            
            # ... (Repetir para TCC II, MCM IV e V como no código anterior)

            st.divider()
            total_banca = sum(notas.values())
            st.subheader(f"Nota Final: {total_banca:.2f}")

            # ALERTAS
            if total_banca < (max_v * 0.6):
                st.warning("⚠️ Nota abaixo da média.")
            if total_banca > max_v:
                st.error("❌ A nota excede o limite!")
                pode_salvar = False
            else:
                pode_salvar = True

            if st.button("Confirmar e Salvar Avaliação") and pode_salvar:
                nova_linha = pd.DataFrame([{
                    "Avaliador": professor_logado,
                    "Trabalho": trabalho_selecionado,
                    "Turma": turma,
                    "Nota_Final": total_banca
                }])
                conn.create(worksheet="Respostas", data=nova_linha)
                st.balloons()
                st.success("Avaliação salva com sucesso!")
