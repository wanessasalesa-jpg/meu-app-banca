import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

st.set_page_config(page_title="Avaliação Afya Marabá", layout="centered")

# --- CONEXÃO E FUNÇÕES (DEFINIDAS NO TOPO) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(aba):
    """Função para ler dados da planilha com cache zerado"""
    return conn.read(worksheet=aba, ttl=0)

# 1. CARREGAMENTO INICIAL
try:
    df_escalacao = get_data("Escalacao")
except Exception as e:
    st.error(f"Erro de conexão: {e}")
    st.stop()

st.title("🎓 Portal de Avaliação - Afya Marabá")

# --- LOGIN ---
email_input = st.text_input("Acesso restrito: Digite seu e-mail", placeholder="exemplo@afya.com.br").strip().lower()

if email_input:
    if email_input in df_escalacao['Email'].str.lower().unique():
        prof_dados = df_escalacao[df_escalacao['Email'].str.lower() == email_input].iloc[0]
        st.success(f"Bem-vindo(a), Prof(a). {prof_dados['Avaliador']}!")

        # 2. FILTRO DE TRABALHOS PENDENTES
        try:
            df_respostas = get_data("Respostas")
            feitos = df_respostas[df_respostas["Avaliador"] == email_input]["Alunos"].tolist()
        except:
            feitos = []

        meus_trabalhos = df_escalacao[df_escalacao['Email'].str.lower() == email_input]
        pendentes = meus_trabalhos[~meus_trabalhos["Alunos"].isin(feitos)]

        if pendentes.empty:
            st.info("🎉 Todas as avaliações foram concluídas!")
        else:
            aluno_selecionado = st.selectbox("Selecione o grupo de alunos:", [""] + pendentes["Alunos"].tolist())

            if aluno_selecionado:
                dados = pendentes[pendentes["Alunos"] == aluno_selecionado].iloc[0]
                turma_bruta = str(dados['Turma']).strip().upper()
                
                st.info(f"📚 **Título:** {dados['Titulo']}\n\n👤 **Orientador:** {dados['Orientador']}")

                # 3. RUBRICAS E PESOS (MCM V = 100 PTS)
                notas = {}
                
                if "TCC I" in turma_bruta and "TCC II" not in turma_bruta:
                    rubrica = {
                        "Tema Contemporâneo": (3, "Escolha de tema contemporâneo e de interesse acadêmico."),
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
                    nota_max = 60
                elif "TCC II" in turma_bruta:
                    rubrica = {
                        "Tema e Resumo": (4, "Contemporaneidade e uso correto de DECS."),
                        "Introdução": (5, "Justificativa e objetivos claros."),
                        "Metodologia": (5, "Rigor científico e ética."),
                        "Resultados": (5, "Descrição que responde aos objetivos."),
                        "Discussão e Conclusão": (10, "Análise crítica dos achados."),
                        "Referências": (1, "Fontes pertinentes."),
                        "Apresentação Oral": (10, "Domínio de palco e segurança."),
                        "Coerência": (10, "Lógica entre fala e texto."),
                        "Qualidade Visual": (9, "Slides organizados."),
                        "Tempo (15-20min)": (1, "Cumprimento do tempo.")
                    }
                    nota_max = 60
                elif "MCM V" in turma_bruta:
                    rubrica = {
                        "Resumo": (10, "Qualidade da síntese do trabalho."),
                        "Introdução": (10, "Fundamentação teórica e objetivos."),
                        "Metodologia": (10, "Desenho do estudo e descrição dos métodos."),
                        "Resultados": (20, "Apresentação e análise clara dos dados obtidos."),
                        "Discussão": (10, "Confronto crítico com a literatura."),
                        "Conclusão": (10, "Pertinência dos fechamentos aos resultados."),
                        "Redação/ABNT": (10, "Correção gramatical e normas técnicas."),
                        "Arguição": (10, "Autonomia e segurança nas respostas."),
                        "Apresentação": (10, "Fluidez, clareza e domínio (15-20 min).")
                    }
                    nota_max = 100
                else: # MCM IV ou Padrão
                    rubrica = {
                        "Domínio": (5, "Conhecimento e resposta à banca."),
                        "Coerência": (5, "Sintonia tema/apresentação."),
                        "Comunicação": (5, "Clareza e postura profissional."),
                        "Organização/Tempo": (5, "Gestão do tempo (10-15 min)."),
                        "Recursos Visuais": (5, "Qualidade do material."),
                        "Métodos": (5, "Adequação objetivos x métodos.")
                    }
                    nota_max = 30

                # AVISO DE NOTA MÁXIMA
                st.warning(f"⚠️ **Nota máxima para {turma_bruta}: {nota_max} pontos.**")

                for item, (p, help_t) in rubrica.items():
                    notas[item] = st.slider(f"{item} (Até {p})", 0, p, 1, help=help_t)

                total = sum(notas.values())
                st.markdown(f"### Nota Final: **{total}** / {nota_max}")

                # 4. SALVAMENTO
                if st.button("Confirmar e Gravar Avaliação"):
                    try:
                        nova_linha = pd.DataFrame([{
                            "Avaliador": email_input,
                            "Alunos": aluno_selecionado,
                            "Titulo": dados['Titulo'],
                            "Nota_Final": total
                        }])
                        
                        # Lê o estado atual, anexa e atualiza a planilha
                        df_atual = get_data("Respostas")
                        df_final = pd.concat([df_atual, nova_linha], ignore_index=True)
                        conn.update(worksheet="Respostas", data=df_final)
                        
                        st.balloons()
                        st.success("✅ AVALIAÇÃO GRAVADA COM SUCESSO!")
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
    else:
        st.error("E-mail não cadastrado.")
