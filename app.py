import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta
import time

# Configuração focada em mobile
st.set_page_config(page_title="Avaliação Afya", layout="centered")

# CSS para botões rápidos
st.markdown("""
    <style>
    .stButton button {
        width: 100%;
        border-radius: 10px;
        height: 3.5em;
        background-color: #007bff;
        color: white;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(aba, ttl_sec=2):
    return conn.read(worksheet=aba, ttl=ttl_sec)

# 1. CARREGAMENTO DOS DADOS
try:
    df_escalacao = get_data("Escalacao", ttl_sec=300)
except:
    st.error("Conectando ao servidor...")
    time.sleep(1)
    st.rerun()

st.title("🎓 Avaliação de Bancas")

# --- LÓGICA DE MEMÓRIA PERSISTENTE (URL) ---
# Verifica se já existe um e-mail salvo na sessão ou na URL
query_params = st.query_params
if "user" in query_params and "email" not in st.session_state:
    st.session_state.email = query_params["user"]

# --- TELA DE LOGIN (Só aparece se não houver e-mail na memória) ---
if 'email' not in st.session_state:
    st.write("### Identificação")
    email_raw = st.text_input("Digite seu e-mail cadastrado:").strip()
    if st.button("Acessar Sistema"):
        if email_raw:
            email_limpo = email_raw.lower()
            if email_limpo in df_escalacao['Email'].str.lower().unique():
                st.session_state.email = email_limpo
                # Grava o e-mail na URL para não perder no refresh
                st.query_params["user"] = email_limpo
                st.rerun()
            else:
                st.error("E-mail não encontrado.")
    st.stop()

# --- INTERFACE ---
# Se chegou aqui, ele já está logado
try:
    prof_dados = df_escalacao[df_escalacao['Email'].str.lower() == st.session_state.email].iloc[0]
    nome_avaliador = prof_dados['Avaliador']
except:
    # Caso o e-mail na URL seja inválido, reseta
    del st.session_state.email
    st.query_params.clear()
    st.rerun()

col_user, col_exit = st.columns([3, 1])
with col_user:
    st.write(f"Olá, Prof. {nome_avaliador}")
with col_exit:
    if st.button("Sair"):
        # Limpa tudo: sessão e URL
        del st.session_state.email
        st.query_params.clear()
        st.rerun()

st.divider()

# O restante do código de busca de pendentes, trava de horário e rubricas permanece exatamente o mesmo
# [O código continua com as rubricas TCC I, TCC II e MCM V sem alterações]

try:
    df_respostas = get_data("Respostas", ttl_sec=0)
    feitos = df_respostas[df_respostas["Email_Avaliador"] == st.session_state.email]["Alunos"].tolist()
except:
    feitos = []

agora = datetime.now()

def verificar_liberacao(linha):
    try:
        data_banca = pd.to_datetime(linha['Data'], dayfirst=True).date()
        hora_banca = pd.to_datetime(linha['Horario']).time()
        momento_banca = datetime.combine(data_banca, hora_banca)
        return agora >= (momento_banca - timedelta(minutes=15))
    except:
        return True

pendentes = df_escalacao[(df_escalacao['Email'].str.lower() == st.session_state.email) & (~df_escalacao['Alunos'].isin(feitos))].copy()

if pendentes.empty:
    st.balloons()
    st.success("🎉 Todas as suas bancas foram concluídas!")
else:
    pendentes['liberado'] = pendentes.apply(verificar_liberacao, axis=1)
    visiveis = pendentes[pendentes['liberado'] == True].copy()

    if visiveis.empty:
        st.warning("⏳ **Acesso bloqueado.**")
        st.info("Suas bancas serão liberadas automaticamente no horário previsto.")
    else:
        visiveis['ordem_tempo'] = pd.to_datetime(visiveis['Data'].astype(str) + ' ' + visiveis['Horario'].astype(str))
        visiveis = visiveis.sort_values(by='ordem_tempo')
        lista_grupos = visiveis["Alunos"].tolist()
        aluno_selecionado = st.selectbox("🎯 Escolha o Grupo:", [""] + lista_grupos)

        if aluno_selecionado:
            dados = visiveis[visiveis["Alunos"] == aluno_selecionado].iloc[0]
            turma_bruta = str(dados['Turma']).strip().upper()
            with st.expander("📖 Detalhes", expanded=True):
                st.write(f"**Trabalho:** {turma_bruta}")
                st.write(f"**Título:** {dados['Titulo']}")
                st.write(f"**Orientador:** {dados['Orientador']}")

            @st.fragment
            def formulario_avaliacao():
                st.write("### 📝 Critérios")
                notas = {}
                
                # Rubricas originais preservadas aqui (TCC I, II, MCM V)
                # ... [Mesmo bloco de rubricas anterior] ...
                if "TCC I" in turma_bruta and "TCC II" not in turma_bruta:
                    rubrica = {"Tema Contemporâneo": (3, "Escolha de tema contemporâneo, oportuno e de interesse acadêmico."), "Resumo": (1, "Autoexplicativo, objetivos e conclusão condizentes, uso de DECS."), "Introdução": (5, "Clareza, concisão e sequência lógica dos argumentos."), "Justificativa/Problema": (5, "Formatação ABNT e relevância do problema."), "Objetivos": (5, "Claros, exequíveis e condizentes com o tema."), "Metodologia": (10, "Tipo de estudo, população, local, ética e análise de dados."), "Referências": (1, "Fontes confiáveis, atuais e listadas corretamente."), "Apresentação Oral": (10, "Segurança, postura, dicção e domínio do conteúdo."), "Coerência": (10, "Conteúdo da fala em sintonia com o texto escrito."), "Qualidade Visual": (9, "Material visual de apoio bem estruturado e organizado."), "Tempo (10-15min)": (1, "Respeito ao limite de tempo regulamentar.")}
                    nota_max = 60
                elif "TCC II" in turma_bruta:
                    rubrica = {"Tema e Resumo": (4, "Contemporaneidade e uso correto de DECS."), "Introdução": (5, "Justificativa e objetivos claros e bem fundamentados."), "Metodologia": (5, "Rigor científico e observância aos preceitos éticos."), "Resultados": (5, "Descrição concisa que responde aos objetivos."), "Discussão e Conclusão": (10, "Análise crítica dos achados e limitações do estudo."), "Referências": (1, "Fontes bibliográficas pertinentes e atualizadas."), "Apresentação Oral": (10, "Domínio de palco, clareza e segurança."), "Coerência": (10, "Lógica entre a explanação oral e o trabalho escrito."), "Qualidade Visual": (9, "Slides organizados e de fácil leitura."), "Tempo (15-20min)": (1, "Cumprimento do tempo estipulado.")}
                    nota_max = 60
                elif "MCM V" in turma_bruta:
                    rubrica = {"Resumo": (10, "Qualidade da síntese do trabalho."), "Introdução": (10, "Fundamentação teórica e objetivos."), "Metodologia": (10, "Desenho do estudo e descrição dos métodos."), "Resultados": (20, "Apresentação e análise clara dos dados obtidos."), "Discussão": (10, "Confronto crítico com a literatura."), "Conclusão": (10, "Pertinência dos fechamentos aos resultados."), "Redação/ABNT": (10, "Correção gramatical e normas técnicas."), "Arguição": (10, "Autonomia e segurança nas respostas."), "Apresentação": (10, "Fluidez, clareza e domínio de palco (15-20 min).")}
                    nota_max = 100
                else:
                    rubrica = {"Domínio de Conteúdo": (5, "Conhecimento demonstrado."), "Coerência": (5, "Lógica."), "Comunicação": (5, "Postura."), "Organização/Tempo": (5, "Gestão."), "Recursos Visuais": (5, "Qualidade."), "Métodos": (5, "Adequação.")}
                    nota_max = 30

                st.warning(f"**Nota máxima: {nota_max} pts**")
                for item, (p, help_t) in rubrica.items():
                    notas[item] = st.slider(f"**{item}**", 0, p, 0, help=help_t, key=f"s_{item}")

                total = sum(notas.values())
                st.markdown(f"## Total: {total} / {nota_max}")

                if st.button("🚀 GRAVAR AVALIAÇÃO"):
                    sucesso = False
                    try:
                        df_at = conn.read(worksheet="Respostas", ttl=0)
                        nova_l = pd.DataFrame([{"Avaliador": nome_avaliador, "Email_Avaliador": st.session_state.email, "Alunos": aluno_selecionado, "Titulo": dados['Titulo'], "Nota_Final": total, "Data_Hora": datetime.now().strftime("%d/%m/%Y %H:%M")}])
                        df_f = pd.concat([df_at, nova_l], ignore_index=True)
                        conn.update(worksheet="Respostas", data=df_f)
                        sucesso = True
                    except Exception as e:
                        st.error(f"Erro na rede: {e}")
                    
                    if sucesso:
                        st.balloons()
                        st.success("✅ GRAVADO!")
                        time.sleep(2)
                        st.rerun()

            formulario_avaliacao()
