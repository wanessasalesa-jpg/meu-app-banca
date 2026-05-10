import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

st.set_page_config(page_title="Avaliação Afya Marabá", layout="centered")

conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(aba):
    return conn.read(worksheet=aba, ttl=0)

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

        try:
            df_respostas = get_data("Respostas")
            feitos = df_respostas[df_respostas["Avaliador"] == email_input]["Alunos"].tolist()
        except:
            feitos = []

        meus_trabalhos = df_escalacao[df_escalacao['Email'].str.lower() == email_input]
        pendentes = meus_trabalhos[~meus_trabalhos["Alunos"].isin(feitos)]

        if pendentes.empty:
            st.info("🎉 Todas as avaliações concluídas!")
        else:
            aluno_selecionado = st.selectbox("Selecione o grupo de alunos:", [""] + pendentes["Alunos"].tolist())

            if aluno_selecionado:
                dados = pendentes[pendentes["Alunos"] == aluno_selecionado].iloc[0]
                # .strip() remove espaços invisíveis que quebram o código
                turma_bruta = str(dados['Turma']).strip().upper()
                
                st.info(f"📚 **Título:** {dados['Titulo']}")
                st.write(f"👤 **Orientador(a):** {dados['Orientador']}")
                st.write(f"🏫 **Turma identificada:** {turma_bruta}")

                st.divider()
                
                # --- DEFINIÇÃO DAS RUBRICAS (CORREÇÃO DE PESOS E HELPS) ---
                notas = {}
                
                # Usamos "in" para garantir que pegue mesmo se o nome na planilha for longo
                if "TCC I" in turma_bruta and "TCC II" not in turma_bruta:
                    rubrica = {
                        "Tema Contemporâneo": (3, "Escolha de tema contemporâneo, oportuno e de interesse acadêmico."),
                        "Resumo": (1, "Autoexplicativo, objetivos e conclusão condizentes, uso de DECS."),
                        "Introdução": (5, "Clareza, concisão e sequência lógica."),
                        "Justificativa/Problema": (5, "Formatação ABNT e relevância."),
                        "Objetivos": (5, "Claros e exequíveis."),
                        "Metodologia": (10, "Tipo de estudo, local, ética e análise."),
                        "Referências": (1, "Fontes confiáveis e listadas."),
                        "Apresentação Oral": (10, "Segurança, postura e domínio."),
                        "Coerência": (10, "Sintonia fala/texto."),
                        "Qualidade Visual": (9, "Material estruturado."),
                        "Tempo (10-15min)": (1, "Respeito ao limite de tempo.")
                    }
                    nota_maxima_prova = 60
                elif "TCC II" in turma_bruta:
                    rubrica = {
                        "Tema e Resumo": (4, "Contemporaneidade e DECS."),
                        "Introdução": (5, "Objetivos claros."),
                        "Metodologia": (5, "Rigor e ética."),
                        "Resultados": (5, "Responde ao objetivo."),
                        "Discussão e Conclusão": (10, "Análise crítica."),
                        "Referências": (1, "Fontes listadas."),
                        "Apresentação Oral": (10, "Segurança e domínio."),
                        "Coerência": (10, "Lógica fala/texto."),
                        "Qualidade Visual": (9, "Material estruturado."),
                        "Tempo (15-20min)": (1, "Respeito ao limite de tempo.")
                    }
                    nota_maxima_prova = 60
                elif "MCM IV" in turma_bruta:
                    rubrica = {
                        "Domínio": (5, "Resposta à banca."), "Coerência": (5, "Lógica."),
                        "Comunicação": (5, "Clareza."), "Organização/Tempo": (5, "10-15 min."),
                        "Recursos": (5, "Audiovisuais."), "Métodos": (5, "Objetivos x Métodos.")
                    }
                    nota_maxima_prova = 30
                else: # MCM V ou outros
                    rubrica = {
                        "Resumo": (10, "Síntese."), "Introdução": (10, "Objetivos."),
                        "Metodologia": (10, "Desenho."), "Resultados": (20, "Dados."),
                        "Discussão": (10, "Crítica."), "Conclusão": (10, "Pertinência."),
                        "Redação": (10, "ABNT."), "Arguição": (10, "Autonomia."),
                        "Apresentação": (10, "Domínio (15-20 min).")
                    }
                    nota_maxima_prova = 100

                st.warning(f"⚠️ Nota máxima possível para esta turma: {nota_maxima_prova} pontos.")

                for item, (p, help_text) in rubrica.items():
                    # O segredo é o label_visibility para garantir que o texto apareça
                    notas[item] = st.slider(f"{item} (Valor: {p})", 0, p, step=1, help=help_text)

                total = sum(notas.values())
                
                # Regra de reprovação (Menos de 70% da nota máxima)
                status_cor = "red" if total < (nota_maxima_prova * 0.7) else "green"
                st.markdown(f"### Nota Final: <span style='color:{status_cor}'>{total}</span> / {nota_maxima_prova}", unsafe_allow_html=True)
                
                if total < (nota_maxima_prova * 0.7):
                    st.error("❗ Atenção: Esta nota é considerada reprovatória (abaixo de 70%).")

                if st.button("Confirmar e Gravar Avaliação"):
                    try:
                        nova_linha = pd.DataFrame([{
                            "Avaliador": email_input,
                            "Alunos": aluno_selecionado,
                            "Titulo": dados['Titulo'],
                            "Nota_Final": total
                        }])
                        
                        # Salvamento com tentativa dupla
                        conn.create(worksheet="Respostas", data=nova_linha)
                        
                        st.balloons()
                        st.success("✅ AVALIAÇÃO GRAVADA COM SUCESSO!")
                        time.sleep(3) # Tempo aumentado para ver os balões
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
    else:
        st.error("E-mail não cadastrado.")
