import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

st.set_page_config(page_title="Avaliação Afya Marabá", layout="centered")

# Conexão com cache zerado para garantir dados novos
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(aba):
    return conn.read(worksheet=aba, ttl=0)

# 1. CARREGAMENTO
try:
    df_escalacao = get_data("Escalacao")
except Exception as e:
    st.error(f"Erro de conexão: {e}")
    st.stop()

st.title("🎓 Portal de Avaliação - Afya Marabá")

email_input = st.text_input("Acesso restrito: Digite seu e-mail", placeholder="exemplo@afya.com.br").strip().lower()

if email_input:
    if email_input in df_escalacao['Email'].str.lower().unique():
        prof_dados = df_escalacao[df_escalacao['Email'].str.lower() == email_input].iloc[0]
        st.success(f"Bem-vindo(a), Prof(a). {prof_dados['Avaliador']}!")

        # 2. FILTRO DE PENDENTES
        try:
            df_respostas = get_data("Respostas")
            feitos = df_respostas[df_respostas["Avaliador"] == email_input]["Alunos"].tolist()
        except:
            feitos = []

        meus_trabalhos = df_escalacao[df_escalacao['Email'].str.lower() == email_input]
        pendentes = meus_trabalhos[~meus_trabalhos["Alunos"].isin(feitos)]

        if pendentes.empty:
            st.info("🎉 Você concluiu todas as suas avaliações!")
        else:
            aluno_selecionado = st.selectbox("Selecione o grupo de alunos:", [""] + pendentes["Alunos"].tolist())

            if aluno_selecionado:
                dados = pendentes[pendentes["Alunos"] == aluno_selecionado].iloc[0]
                turma_bruta = str(dados['Turma']).strip().upper()
                
                st.info(f"📚 **Título:** {dados['Titulo']}\n\n👤 **Orientador:** {dados['Orientador']}")

                # 3. RUBRICAS COMPLETAS (TEXTO INTEGRAL)
                notas = {}
                if "TCC I" in turma_bruta and "TCC II" not in turma_bruta:
                    rubrica = {
                        "Tema Contemporâneo": (3, "Escolha de tema contemporâneo, oportuno e de interesse acadêmico."),
                        "Resumo": (1, "Autoexplicativo, objetivos e conclusão condizentes, uso de DECS."),
                        "Introdução": (5, "Clareza, concisão e sequência lógica dos argumentos."),
                        "Justificativa/Problema": (5, "Formatação ABNT e relevância do problema."),
                        "Objetivos": (5, "Claros, exequíveis e condizentes com o tema."),
                        "Metodologia": (10, "Tipo de estudo, população, local, ética e análise de dados."),
                        "Referências": (1, "Fontes confiáveis, atuais e listadas corretamente."),
                        "Apresentação Oral": (10, "Segurança, postura, dicção e domínio do conteúdo."),
                        "Coerência": (10, "Conteúdo da fala em sintonia com o texto escrito."),
                        "Qualidade Visual": (9, "Material visual de apoio bem estruturado e organizado."),
                        "Tempo (10-15min)": (1, "Respeito ao limite de tempo regulamentar.")
                    }
                    nota_max = 60
                elif "TCC II" in turma_bruta:
                    rubrica = {
                        "Tema e Resumo": (4, "Contemporaneidade e uso correto de DECS."),
                        "Introdução": (5, "Justificativa e objetivos claros e bem fundamentados."),
                        "Metodologia": (5, "Rigor científico e observância aos preceitos éticos."),
                        "Resultados": (5, "Descrição concisa que responde aos objetivos."),
                        "Discussão e Conclusão": (10, "Análise crítica dos achados e limitações do estudo."),
                        "Referências": (1, "Fontes bibliográficas pertinentes e atualizadas."),
                        "Apresentação Oral": (10, "Domínio de palco, clareza e segurança."),
                        "Coerência": (10, "Lógica entre a explanação oral e o trabalho escrito."),
                        "Qualidade Visual": (9, "Slides organizados e de fácil leitura."),
                        "Tempo (15-20min)": (1, "Cumprimento do tempo estipulado.")
                    }
                    nota_max = 60
                else: # MCM
                    rubrica = {
                        "Domínio de Conteúdo": (5, "Conhecimento demonstrado e resposta aos questionamentos."),
                        "Coerência": (5, "Lógica entre o tema e a apresentação."),
                        "Comunicação": (5, "Clareza, tom de voz e postura profissional."),
                        "Organização/Tempo": (5, "Gestão do tempo de 10 a 15 minutos."),
                        "Recursos Visuais": (5, "Qualidade dos slides e apoio audiovisual."),
                        "Métodos": (5, "Adequação da metodologia aos objetivos propostos.")
                    }
                    nota_max = 30

                st.subheader(f"Avaliação: {turma_bruta} (Máx: {nota_max})")
                for item, (p, help_t) in rubrica.items():
                    notas[item] = st.slider(f"{item} (Até {p})", 0, p, 1, help=help_t)

                total = sum(notas.values())
                st.markdown(f"### Nota Total: **{total}** / {nota_max}")

                # 4. SALVAMENTO ROBUSTO
                if st.button("Confirmar e Gravar Avaliação"):
                    try:
                        nova_linha = pd.DataFrame([{
                            "Avaliador": email_input,
                            "Alunos": aluno_selecionado,
                            "Titulo": dados['Titulo'],
                            "Nota_Final": total
                        }])
                        
                        # Estratégia de Atualização: Lê tudo -> Adiciona -> Salva tudo
                        try:
                            atual_df = get_data("Respostas")
                            final_df = pd.concat([atual_df, nova_linha], ignore_index=True)
                        except:
                            final_df = nova_linha
                            
                        conn.update(worksheet="Respostas", data=final_df)
                        
                        st.balloons()
                        st.success("✅ GRAVADO COM SUCESSO! Voltando...")
                        time.sleep(3)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
    else:
        st.error("E-mail não cadastrado.")
