import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# Configuração da página com layout mais limpo
st.set_page_config(page_title="Avaliação Afya Marabá", layout="wide", initial_sidebar_state="expanded")

# --- CONEXÃO COM CACHE ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(aba, tempo_cache=120):
    return conn.read(worksheet=aba, ttl=tempo_cache)

# 1. CARREGAMENTO
try:
    df_escalacao = get_data("Escalacao", tempo_cache=300)
except Exception as e:
    st.error("O sistema está processando muitos acessos. Aguarde 30 segundos.")
    st.stop()

# --- BARRA LATERAL (Login e Status) ---
with st.sidebar:
    st.image("https://www.afya.com.br/hubfs/logo-afya.png", width=150) # Logo genérica da Afya
    st.title("Acesso")
    email_input = st.text_input("E-mail cadastrado:", placeholder="seu.email@afya.com.br").strip().lower()
    
    nome_avaliador = None
    if email_input:
        if email_input in df_escalacao['Email'].str.lower().unique():
            prof_dados = df_escalacao[df_escalacao['Email'].str.lower() == email_input].iloc[0]
            nome_avaliador = prof_dados['Avaliador']
            st.success(f"Logado: {nome_avaliador}")
            st.divider()
            st.info("💡 Lembre-se de conferir todos os critérios antes de salvar.")
        else:
            st.error("E-mail não encontrado.")

# --- CORPO PRINCIPAL ---
st.header("🎓 Sistema de Avaliação de Bancas")

if email_input and nome_avaliador:
    try:
        df_respostas = get_data("Respostas", tempo_cache=10)
        feitos = df_respostas[df_respostas["Email_Avaliador"] == email_input]["Alunos"].tolist()
    except:
        feitos = []

    pendentes = df_escalacao[(df_escalacao['Email'].str.lower() == email_input) & (~df_escalacao['Alunos'].isin(feitos))]

    if pendentes.empty:
        st.balloons()
        st.info("### 🎉 Excelente! Todas as suas avaliações foram concluídas.")
    else:
        # Lista suspensa estilizada
        lista_grupos = sorted(pendentes["Alunos"].tolist())
        aluno_selecionado = st.selectbox("🎯 Selecione o grupo para avaliar:", [""] + lista_grupos)

        if aluno_selecionado:
            dados = pendentes[pendentes["Alunos"] == aluno_selecionado].iloc[0]
            turma_bruta = str(dados['Turma']).strip().upper()
            
            # Organização em Abas para não poluir a tela
            tab1, tab2 = st.tabs(["📝 Ficha de Avaliação", "📖 Informações do Trabalho"])

            with tab2:
                st.subheader("Dados do Projeto")
                st.markdown(f"**Título:** {dados['Titulo']}")
                st.markdown(f"**Orientador:** {dados['Orientador']}")
                st.markdown(f"**Turma:** {turma_bruta}")

            with tab1:
                # --- DEFINIÇÃO DE RUBRICAS (INTOCADAS) ---
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
                        "Apresentação": (10, "Fluidez, clareza e domínio de palco (15-20 min).")
                    }
                    nota_max = 100
                else:
                    rubrica = {
                        "Domínio de Conteúdo": (5, "Conhecimento demonstrado e resposta à banca."),
                        "Coerência": (5, "Lógica entre o tema e a apresentação."),
                        "Comunicação": (5, "Clareza, tom de voz e postura profissional."),
                        "Organização/Tempo": (5, "Gestão do tempo de 10 a 15 minutos."),
                        "Recursos Visuais": (5, "Qualidade dos slides e apoio audiovisual."),
                        "Métodos": (5, "Adequação da metodologia aos objetivos propostos.")
                    }
                    nota_max = 30

                st.warning(f"🎯 **Nota máxima para {turma_bruta}: {nota_max} pontos.**")

                # Sliders estilizados
                for item, (p, help_t) in rubrica.items():
                    notas[item] = st.slider(f"**{item}** (0-{p})", 0, p, 0, help=help_t)

                total = sum(notas.values())
                
                # Visualização da nota final grande
                st.divider()
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"### Nota Final Calculada:")
                with col2:
                    st.subheader(f"{total} / {nota_max}")

                if st.button("🚀 Confirmar e Enviar Notas"):
                    with st.spinner("Gravando na planilha..."):
                        try:
                            nova_linha = pd.DataFrame([{
                                "Avaliador": nome_avaliador, 
                                "Email_Avaliador": email_input,
                                "Alunos": aluno_selecionado, 
                                "Titulo": dados['Titulo'], 
                                "Nota_Final": total,
                                "Data_Hora": datetime.now().strftime("%d/%m/%Y %H:%M")
                            }])
                            df_atual = conn.read(worksheet="Respostas", ttl=0)
                            df_final = pd.concat([df_atual, nova_linha], ignore_index=True)
                            conn.update(worksheet="Respostas", data=df_final)
                            st.balloons()
                            st.success("✅ AVALIAÇÃO GRAVADA COM SUCESSO!")
                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar: {e}")
else:
    st.info("👋 Por favor, insira seu e-mail na barra lateral para começar.")
