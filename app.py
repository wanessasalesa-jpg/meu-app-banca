import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta
import time
import pytz 

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CRIVO - Gestão Acadêmica", layout="centered")

# 2. FUSO HORÁRIO DE BRASÍLIA
fuso_bruta = pytz.timezone('America/Sao_Paulo')

def obter_agora():
    return datetime.now(fuso_bruta)

# FUNÇÃO PARA ENCURTAR NOMES NA EXIBIÇÃO DO APP
def tratar_nome_curto(nome_completo):
    if not nome_completo or pd.isna(nome_completo):
        return ""
    partes = str(nome_completo).strip().split()
    if len(partes) > 1:
        return f"{partes[0]} {partes[1]}"
    return partes[0]

# FUNÇÃO SEGURA PARA CHECAR E-MAIL LOWERCASE NA COLUNA (EVITA ATTRIBUTEERROR)
def checar_email_na_coluna(email, df, coluna):
    if coluna not in df.columns:
        return False
    return email in df[coluna].astype(str).str.strip().str.lower().unique()

# 3. CONEXÃO COM GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(aba, ttl_sec=2):
    return conn.read(worksheet=aba, ttl=ttl_sec)

try:
    df_escalacao = get_data("Escalacao", ttl_sec=300)
except:
    st.error("Conectando ao banco de dados... Aguarde.")
    time.sleep(1)
    st.rerun()

# --- TRAVA DE LOGOUT E IDENTIFICAÇÃO DE PAPEL ---
if 'email' not in st.session_state:
    if "user" in st.query_params:
        st.session_state.email = st.query_params["user"]

if 'email' not in st.session_state:
    st.title("🎓 CRIVO")
    st.subheader("Sistema de Gestão de Bancas Acadêmicas")
    st.caption("© 2026 Desenvolvido por Wanessa Sales de Almeida")
    st.divider()

    st.write("### Identificação do Docente")
    email_raw = st.text_input("Digite seu e-mail cadastrado:").strip()
    if st.button("Acessar Sistema"):
        if email_raw:
            email_limpo = email_raw.lower()
            
            # Validação blindada usando astype(str) para evitar o erro da imagem
            id_banca1 = checar_email_na_coluna(email_limpo, df_escalacao, 'Email_Avaliador_1')
            id_banca2 = checar_email_na_coluna(email_limpo, df_escalacao, 'Email_Avaliador_2')
            id_suplente = checar_email_na_coluna(email_limpo, df_escalacao, 'Email_suplente')
            id_orienta = checar_email_na_coluna(email_limpo, df_escalacao, 'Email_Orientador')
            
            if id_banca1 or id_banca2 or id_suplente or id_orienta:
                st.session_state.email = email_limpo
                st.query_params["user"] = email_limpo
                st.rerun()
            else:
                st.error("E-mail não autorizado ou não encontrado na escalação.")
    st.stop()

# --- DEFINIÇÃO DO PAPEL LOGADO ---
email_user = st.session_state.email
eh_orientador = False
eh_banca = False
nome_completo_docente = ""

# Identificação dinâmica do usuário logado
if checar_email_na_coluna(email_user, df_escalacao, 'Email_Orientador'):
    eh_orientador = True
    nome_completo_docente = df_escalacao[df_escalacao['Email_Orientador'].astype(str).str.lower() == email_user]['Orientador'].iloc[0]
elif checar_email_na_coluna(email_user, df_escalacao, 'Email_Avaliador_1'):
    eh_banca = True
    nome_completo_docente = df_escalacao[df_escalacao['Email_Avaliador_1'].astype(str).str.lower() == email_user]['Avaliador_1'].iloc[0]
elif checar_email_na_coluna(email_user, df_escalacao, 'Email_Avaliador_2'):
    eh_banca = True
    nome_completo_docente = df_escalacao[df_escalacao['Email_Avaliador_2'].astype(str).str.lower() == email_user]['Avaliador_2'].iloc[0]
elif checar_email_na_coluna(email_user, df_escalacao, 'Email_suplente'):
    eh_banca = True
    nome_completo_docente = df_escalacao[df_escalacao['Email_suplente'].astype(str).str.lower() == email_user]['Avaliador_Suplente'].iloc[0]

nome_exibicao = tratar_nome_curto(nome_completo_docente)

# --- DEFINIÇÃO DINÂMICA DE CORES (CSS) ---
cor_primaria = "#002147" if not eh_orientador else "#1b4d3e"
st.markdown(f"""
    <style>
    header {{visibility: hidden;}}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    .stButton button {{
        width: 100%;
        border-radius: 10px;
        height: 3.5em;
        background-color: {cor_primaria};
        color: white;
        font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

# CABEÇALHO DO APP APÓS LOGIN
st.title("🎓 CRIVO")
st.subheader("Sistema de Gestão de Bancas Acadêmicas" if not eh_orientador else "Sistema de Gestão de Orientações")
st.caption("© 2026 Desenvolvido por Wanessa Sales de Almeida")
st.divider()

# --- AMBIENTE VISUAL DO DOCENTE ---
col_user, col_exit = st.columns([3, 1])
with col_user:
    st.write(f"**Docente:** {nome_exibicao} ({'Orientador' if eh_orientador else 'Banca Examinadora'})")
with col_exit:
    if st.button("Sair"):
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()

# Filtragem de pendentes baseada no papel
try:
    df_respostas = get_data("Respostas", ttl_sec=0)
    feitos = df_respostas[(df_respostas["Email_Avaliador"] == email_user) & (df_respostas["Papel"] == ("Orientador" if eh_orientador else "Banca"))]["Alunos"].tolist()
except:
    feitos = []

if eh_orientador:
    pendentes = df_escalacao[(df_escalacao['Email_Orientador'].astype(str).str.lower() == email_user) & (~df_escalacao['Alunos'].isin(feitos))].copy()
else:
    cond_banca = (
        (df_escalacao['Email_Avaliador_1'].astype(str).str.lower() == email_user) | 
        (df_escalacao['Email_Avaliador_2'].astype(str).str.lower() == email_user) | 
        (df_escalacao['Email_suplente'].astype(str).str.lower() == email_user)
    )
    pendentes = df_escalacao[cond_banca & (~df_escalacao['Alunos'].isin(feitos))].copy()

if pendentes.empty:
    st.balloons()
    st.success("🎉 Todas as suas avaliações pendentes foram concluídas!")
else:
    pendentes['Alunos_Curto'] = pendentes['Alunos'].apply(lambda x: ", ".join([tratar_nome_curto(n) for n in str(x).split(",")]))
    lista_grupos_display = pendentes["Alunos_Curto"].tolist()
    lista_grupos_reais = pendentes["Alunos"].tolist()
    
    grupo_map = dict(zip(lista_grupos_display, lista_grupos_reais))
    selecionado_display = st.selectbox("🎯 Escolha o Grupo para Avaliar:", [""] + lista_grupos_display)

    if selecionado_display and selecionado_display != "":
        aluno_selecionado = grupo_map[selecionado_display]
        dados = pendentes[pendentes["Alunos"] == aluno_selecionado].iloc[0]
        turma_bruta = str(dados['Turma']).strip().upper()
        
        # --- TRAVA DE HORÁRIO RÍGIDA (5 MINUTOS ANTES) ---
        banca_liberada = True
        msg_trava = ""
        try:
            data_banca = datetime.strptime(str(dados['Data']).strip(), "%d/%m/%Y").date()
            horario_banca = datetime.strptime(str(dados['Horario']).strip(), "%H:%M").time()
            dt_banca_completa = fuso_bruta.localize(datetime.combine(data_banca, horario_banca))
            
            agora = obter_agora()
            limite_liberacao = dt_banca_completa - timedelta(minutes=5)
            
            if agora < limite_liberacao:
                banca_liberada = False
                msg_trava = f"⏳ Esta avaliação só estará disponível a partir das {limite_liberacao.strftime('%H:%M')} do dia {data_banca.strftime('%d/%m/%Y')}."
        except:
            pass

        with st.expander("📖 Informações do Trabalho", expanded=True):
            st.write(f"**Turma:** {turma_bruta}")
            st.write(f"**Título:** {dados['Titulo']}")
            st.write(f"**Orientador:** {tratar_nome_curto(dados['Orientador'])}")
            st.write(f"**Integrantes:** {aluno_selecionado}")
            st.write(f"**Data/Horário Cadastrado:** {dados['Data']} às {dados['Horario']}")

        if not banca_liberada:
            st.warning(msg_trava)
        else:
            @st.fragment
            def formulario_avaliacao():
                rubrica = {}
                
                # --- FLUXO 1: VISÃO DO ORIENTADOR ---
                if eh_orientador:
                    st.info("🌱 Você está visualizando a Rubrica de Orientação Oficial.")
                    
                    if "MCM IV" in turma_bruta or "MCM 4" in turma_bruta:
                        rubrica = {
                            "Desenv. - Envolvimento e Responsabilidade": (5, "Participação proativa, demonstrando alta responsabilidade e comprometimento."),
                            "Desenv. - Relação com Orientador / Diálogo": (5, "Relação colaborativa, com boa abertura ao diálogo e aceitação de sugestões."),
                            "Desenv. - Desempenho e Cumprimento de Tarefas": (5, "Desempenho satisfatório, com atividades realizadas de forma competente e engajada."),
                            "Desenv. - Pontualidade e Compromisso": (5, "Pontualidade é mantida consistentemente, demonstrando compromisso com o processo."),
                            "Desenv. - Resp. com Processo de Aprendizagem": (5, "Responsabilidade evidente em buscar ativamente oportunidades de aprimoramento."),
                            "Texto - Justificativa do Estudo": (6, "Apresenta com clareza a relevância científica, social ou profissional vinculada ao problema."),
                            "Texto - Objetivo Geral e Específicos": (6, "Objetivo geral claro e coerente com a justificativa; específicos bem articulados."),
                            "Texto - Fundamentação Teórica / Referências": (6, "Referencial teórico relevante, atualizado (últimos 5 anos em sua maioria) e articulado."),
                            "Texto - Metodologia Proposta": (6, "Método bem descrito, adequado aos objetivos, com definição de tipo de estudo, população e análise."),
                            "Texto - Cronograma de Execução": (3, "Cronograma bem estruturado, com etapas claras e prazos viáveis."),
                            "Texto - Estrutura, Linguagem e Formatação": (3, "Texto bem escrito, estruturado, seguindo as normas (ABNT ou Vancouver).")
                        }
                    elif "TCC I" in turma_bruta or "TCC 1" in turma_bruta:
                        rubrica = {
                            "Discente - Envolvimento e Responsabilidade": (5, "Participação proativa, com alta responsabilidade e comprometimento na elaboração do projeto."),
                            "Discente - Relação com Orientador / Diálogo": (5, "Relação colaborativa, com boa abertura ao diálogo e aceitação de sugestões."),
                            "Discente - Desempenho / Cumprimento de Tarefas": (4, "Desempenho satisfatório, com atividades de forma competente e engajada."),
                            "Discente - Pontualidade e Compromisso": (3, "Pontualidade é mantida consistentemente, demonstrando compromisso com os prazos."),
                            "Discente - Resp. com Aprendizagem": (3, "Responsabilidade evidente em buscar ativamente oportunidades de aprimoramento."),
                            "Projeto - Formulação do Problema e Justificativa": (5, "Problema excepcionalmente formulado e justificativa altamente persuasiva, atualizada e relevante."),
                            "Projeto - Objetivos e Hipóteses": (4, "Objetivos bem formulados e alinhados, e hipóteses pertinentes e testáveis."),
                            "Projeto - Revisão de Literatura": (4, "Revisão abrangente, crítica e que identifica claramente a relevância do estudo."),
                            "Projeto - Metodologia e ABNT": (4, "Metodologia detalhada e abrangente; projeto formatado estritamente conforme norma ABNT."),
                            "Projeto - Considerações Éticas e Viabilidade": (3, "Considerações éticas discutidas apropriadamente e viabilidade do estudo bem abordada.")
                        }
                    elif "TCC II" in turma_bruta or "TCC 2" in turma_bruta:
                        rubrica = {
                            "Discente - Envolvimento e Responsabilidade": (5, "Participação proativa, com alta responsabilidade e comprometimento na elaboração do artigo."),
                            "Discente - Relação com Orientador / Diálogo": (5, "Relação colaborativa, com boa abertura ao diálogo e aceitação de sugestões."),
                            "Discente - Desempenho / Cumprimento de Tarefas": (4, "Desempenho satisfatório, com atividades realizadas de forma competente e engajada."),
                            "Discente - Pontualidade e Compromisso": (3, "Pontualidade mantida consistentemente, demonstrando compromisso com o processo."),
                            "Discente - Resp. com Aprendizagem": (3, "Responsabilidade evidente em buscar ativamente oportunidades de aprimoramento."),
                            "Artigo - Estruturação e Escrita Científica": (5, "Estrutura adequada, com fluidez, concisão e excelência na redação científica."),
                            "Artigo - Fundamentação e Atualização Bibliográfica": (4, "Fundamentação crítica, bem estruturada e com autores atuais e pertinentes à área médica."),
                            "Artigo - Apresentação e Discussão dos Resultados": (4, "Resultados apresentados com clareza, com discussão crítica e integração à literatura."),
                            "Artigo - Rigor Metodológico": (4, "Métodos bem descritos, compatíveis com o delineamento e objetivos do estudo."),
                            "Artigo - Conclusão e Relevância Científica": (3, "Conclusão clara, alinhada aos objetivos, com destaque à relevância e aplicabilidade prática.")
                        }
                
                # --- FLUXO 2: VISÃO DA BANCA AVALIADORA ---
                else:
                    st.info("🎓 Você está visualizando a Rubrica de Avaliação da Banca.")
                    if "TCC I" in turma_bruta or "TCC 1" in turma_bruta or "MCM IV" in turma_bruta or "MCM 4" in turma_bruta:
                        rubrica = {
                            "Tema": (3, "Clareza, delimitação e a atualidade do tema proposto."),
                            "Resumo": (1, "Objetivo, método, resultados esperados e palavras-chave."),
                            "Introdução": (5, "Contextualização do tema e problema de pesquisa."),
                            "Justificativa": (5, "Importância do trabalho e contribuição científica."),
                            "Objetivos": (5, "Objetivo geral e específicos mensuráveis."),
                            "Metodologia": (10, "Desenho do estudo, critérios e ética."),
                            "Referências": (1, "Uso de normas ABNT/Vancouver."),
                            "Apresentação Oral": (10, "Domínio de conteúdo, postura e clareza."),
                            "Coerência": (10, "Lógica entre introdução, objetivos e métodos."),
                            "Qualidade Visual": (9, "Organização dos slides e recursos."),
                            "Tempo": (1, "Intervalo de 10 a 15 minutos de apresentação.")
                        }
                    elif "TCC II" in turma_bruta or "TCC 2" in turma_bruta or "MCM V" in turma_bruta or "MCM 5" in turma_bruta:
                        rubrica = {
                            "Tema/Resumo": (4, "Qualidade técnica do resumo e aderência ao tema."),
                            "Introdução": (5, "Fundamentação teórica sólida e revisão."),
                            "Metodologia": (5, "Execução real do método proposto."),
                            "Resultados": (5, "Apresentação clara dos dados obtidos."),
                            "Discussão": (10, "Capacidade crítica de comparar resultados."),
                            "Referências": (1, "Rigor técnico nas citações e bibliografia."),
                            "Apresentação Oral": (10, "Segurança na defesa dos resultados."),
                            "Coerência": (10, "União lógica de todas as partes do trabalho."),
                            "Qualidade Visual": (9, "Profissionalismo na apresentação visual."),
                            "Tempo": (1, "Intervalo de 15 a 20 minutos de apresentação.")
                        }

                if not rubrica:
                    st.error("Nenhuma rubrica correspondente encontrada para esta turma.")
                    return

                v_max = sum(p for p, h in rubrica.values())
                st.write(f"### 📝 Critérios (Máximo: {v_max} pontos)")
                
                notas = {}
                for item, (p, help_t) in rubrica.items():
                    notas[item] = st.slider(f"**{item} ({p} pts)**", 0, p, 0, help=help_t, key=f"s_{item}")

                total = sum(notas.values())
                st.markdown(f"## Nota Atribuída: {total} / {v_max}")

                tem_zero = any(v == 0 for v in notas.values())
                conf_zero = True
                if tem_zero:
                    st.error("⚠️ Existem critérios com nota zero.")
                    conf_zero = st.checkbox("Confirmo que as notas zero são intencionais.")

                if st.button("🚀 GRAVAR AVALIAÇÃO NO SISTEMA"):
                    if tem_zero and not conf_zero:
                        st.warning("Confirme as notas zero antes de gravar.")
                    else:
                        placeholder = st.empty()
                        with placeholder.container():
                            try:
                                df_at = conn.read(worksheet="Respostas", ttl=0)
                                nova_l = pd.DataFrame([{
                                    "Avaliador": nome_completo_docente, 
                                    "Email_Avaliador": email_user, 
                                    "Alunos": aluno_selecionado, 
                                    "Nota_Final": total, 
                                    "Papel": "Orientador" if eh_orientador else "Banca",
                                    "Data_Hora": obter_agora().strftime("%d/%m/%Y %H:%M")
                                }])
                                df_f = pd.concat([df_at, nova_l], ignore_index=True)
                                conn.update(worksheet="Respostas", data=df_f)
                                
                                st.balloons()
                                st.success("✅ Avaliação gravada com sucesso! Atualizando listagem...")
                                time.sleep(3)
                                st.rerun()
                            except:
                                st.error("Erro ao conectar com a planilha. Tente novamente.")

            formulario_avaliacao()
