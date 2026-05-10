import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

st.set_page_config(page_title="Avaliação Afya Marabá", layout="centered")

# --- CONEXÃO E FUNÇÕES ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(aba):
    # ttl=0 é vital para ver as notas caindo na hora na planilha
    return conn.read(worksheet=aba, ttl=0)

# --- 1. CARREGAMENTO INICIAL ---
try:
    df_escalacao = get_data("Escalacao")
except Exception as e:
    st.error(f"Erro de conexão: {e}")
    st.stop()

st.title("🎓 Portal de Avaliação - Afya Marabá")

# --- 2. LOGIN ---
email_input = st.text_input("Acesso restrito: Digite seu e-mail", placeholder="exemplo@afya.com.br").strip().lower()

if email_input:
    if email_input in df_escalacao['Email'].str.lower().unique():
        prof_dados = df_escalacao[df_escalacao['Email'].str.lower() == email_input].iloc[0]
        st.success(f"Bem-vindo(a), Prof(a). {prof_dados['Avaliador']}!")

        # --- 3. FILTRO DE PENDENTES ---
        try:
            df_respostas = get_data("Respostas")
            # Verifica quem já foi avaliado por este professor
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
                # Localiza os dados exatos do grupo selecionado
                dados = pendentes[pendentes["Alunos"] == aluno_selecionado].iloc[0]
                turma = str(dados['Turma']).upper() # Padroniza para evitar erro de leitura
                
                # Exibição das informações que haviam sumido
                st.info(f"📚 **Título:** {dados['Titulo']}")
                st.write(f"👤 **Orientador(a):** {dados['Orientador']}")
                st.write(f"🏫 **Turma:** {turma}")

                st.divider()
                
                # --- 4. RUBRICAS DETALHADAS (HELP) ---
                notas = {}
                
                if "TCC I" in turma and "TCC II" not in turma:
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
                elif "TCC II" in turma:
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
                elif "MCM IV" in turma:
                    rubrica = {
                        "Domínio de Conteúdo": (5, "Conhecimento demonstrado e resposta aos questionamentos."),
                        "Coerência": (5, "Lógica entre o tema e a apresentação."),
                        "Comunicação": (5, "Clareza, tom de voz e postura profissional."),
                        "Organização/Tempo": (5, "Gestão do tempo de 10 a 15 minutos."),
                        "Recursos Visuais": (5, "Qualidade dos slides e apoio audiovisual."),
                        "Métodos": (5, "Adequação da metodologia aos objetivos propostos.")
                    }
                else: # MCM V ou Padrão
                    rubrica = {
                        "Resumo": (10, "Síntese do trabalho."), "Introdução": (10, "Objetivos."),
                        "Metodologia": (10, "Desenho."), "Resultados": (20, "Dados."),
                        "Discussão": (10, "Crítica."), "Conclusão": (10, "Pertinência."),
                        "Redação": (10, "ABNT."), "Arguição": (10, "Autonomia."),
                        "Apresentação": (10, "Domínio.")
                    }

                for item, (p, help_t) in rubrica.items():
                    notas[item] = st.slider(f"{item} (Máx: {p})", 0, p, step=1, help=help_t)

                total = sum(notas.values())
                st.markdown(f"### Nota Final: **{total}**")

                # --- 5. SALVAMENTO ---
                if st.button("Confirmar e Salvar Avaliação"):
                    try:
                        nova_linha = pd.DataFrame([{
                            "Avaliador": email_input,
                            "Alunos": aluno_selecionado,
                            "Titulo": dados['Titulo'],
                            "Nota_Final": total
                        }])
                        # Salva na planilha
                        conn.create(worksheet="Respostas", data=nova_linha)
                        
                        st.balloons()
                        st.success("✅ Avaliação salva! Voltando à tela inicial...")
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar na planilha: {e}")
    else:
        st.error("E-mail não encontrado na escala de avaliadores.")
