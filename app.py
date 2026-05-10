import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Avaliação Afya Marabá", layout="centered")

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df_escalacao = conn.read(worksheet="Escalacao")
except:
    st.error("Erro ao ler a aba 'Escalacao'. Verifique o nome na planilha.")
    st.stop()

st.title("🎓 Portal de Avaliação - Afya Marabá")

# IDENTIFICAÇÃO
professores = sorted(df_escalacao.iloc[:, 0].unique())
professor_logado = st.selectbox("Selecione seu nome:", [""] + list(professores))

if professor_logado:
    meus_grupos = df_escalacao[df_escalacao["Avaliador"] == professor_logado]
    st.write(f"### Olá, Prof. {professor_logado}!")
    
    trabalho_selecionado = st.selectbox("Selecione o trabalho:", [""] + meus_grupos["Título"].tolist())

    if trabalho_selecionado:
        dados = meus_grupos[meus_grupos["Título"] == trabalho_selecionado].iloc[0]
        st.success(f"📌 **Orientador(a):** {dados['Orientador']}")
        
        turma = dados['Turma']
        notas = {}
        
        # --- DEFINIÇÃO DE LIMITES ---
        max_v = 60.0 if "TCC" in turma else (30.0 if "MCM IV" in turma else 100.0)
        
        # --- RENDERIZAÇÃO DAS RUBRICAS (Resumo do seu código anterior) ---
        # (O código aqui mantém suas rubricas de TCC I, II, MCM IV e V com os tempos de 10-15 e 15-20 min)
        
        if turma == "TCC I":
            st.info("Rubrica TCC I (Máx: 60)")
            itens = {"Tema": 3, "Resumo": 1, "Introdução": 5, "Metodologia": 10, "Apresentação": 10, "Coerência": 10, "Qualidade": 9, "Tempo (10-15min)": 12} # Ajuste os pesos conforme sua ficha
            # Exemplo simplificado para o loop:
            for k, p in itens.items():
                notas[k] = st.slider(f"{k} (Máx: {p})", 0.0, float(p), step=0.1)

        # ... (Repetir lógica para TCC II, MCM IV e V conforme código anterior)

        st.divider()
        
        # --- CÁLCULO E ALERTAS VISUAIS ---
        total_banca = sum(notas.values())
        
        # 1. Alerta de Nota Baixa (Reprobatória < 60%)
        if total_banca < (max_v * 0.6):
            st.warning(f"⚠️ Nota Baixa: {total_banca:.2f}. Esta nota é considerada reprobatória.")
        else:
            st.info(f"✅ Nota atual: {total_banca:.2f}")

        # 2. Verificação de Itens Zerados
        if any(v == 0.0 for v in notas.values()):
            st.error("❗ Existem critérios com nota 0.0. Certifique-se de que avaliou todos os itens.")

        # 3. Trava de Segurança
        if total_banca > max_v:
            st.error(f"❌ ERRO: A soma ({total_banca:.2f}) ultrapassa o limite da turma ({max_v})!")
            pode_salvar = False
        else:
            pode_salvar = True

        # --- BOTÃO SALVAR ---
        if st.button("Confirmar e Salvar Avaliação") and pode_salvar:
            nova_linha = pd.DataFrame([{
                "Avaliador": professor_logado,
                "Trabalho": trabalho_selecionado,
                "Turma": turma,
                "Nota_Final": total_banca
            }])
            # Salva na aba 'Respostas'
            df_escalacao = conn.read(worksheet="Consolidacao") 
except Exception as e:
    st.error(f"Erro ao ler a aba: {e}. Verifique se o nome está correto na planilha.")
    st.stop()
            st.success("Avaliação enviada com sucesso!")
