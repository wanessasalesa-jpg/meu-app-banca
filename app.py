import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta
import time

# Configuração estável
st.set_page_config(page_title="Avaliação Afya", layout="centered")

# CSS para botões e layout
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

# 1. CARREGAMENTO
try:
    df_escalacao = get_data("Escalacao", ttl_sec=300)
except:
    st.error("Conectando ao banco de dados...")
    time.sleep(1)
    st.rerun()

st.title("🎓 Avaliação de Bancas")

# --- LOGIN ---
if 'email' not in st.session_state:
    st.write("### Identificação")
    email_raw = st.text_input("Digite seu e-mail cadastrado:").strip()
    if st.button("Acessar Sistema"):
        if email_raw:
            email_limpo = email_raw.lower()
            if email_limpo in df_escalacao['Email'].str.lower().unique():
                st.session_state.email = email_limpo
                st.rerun()
            else:
                st.error("E-mail não encontrado no cadastro.")
    st.stop()

# --- INTERFACE ---
prof_dados = df_escalacao[df_escalacao['Email'].str.lower() == st.session_state.email].iloc[0]
nome_avaliador = prof_dados['Avaliador']

col_user, col_exit = st.columns([3, 1])
with col_user:
    st.write(f"Olá, Prof. {nome_avaliador}")
with col_exit:
    if st.button("Sair"):
        del st.session_state.email
        st.rerun()

st.divider()

# BUSCA DE PENDENTES
try:
    df_respostas = get_data("Respostas", ttl_sec=0)
    feitos = df_respostas[df_respostas["Email_Avaliador"] == st.session_state.email]["Alunos"].tolist()
except:
    feitos = []

# --- LÓGICA DE TRAVA E ORDENAÇÃO ---
agora = datetime.now()

def verificar_liberacao(linha):
    try:
        # Tenta ler Data e Hora da planilha (Ex: Data: 2026-06-19, Hora: 08:00)
        data_banca = pd.to_datetime(linha['Data']).date()
        hora_banca = pd.to_datetime(linha['Hora']).time()
        momento_banca = datetime.combine(data_banca, hora_banca)
        
        # Libera 15 minutos antes do horário marcado
        return agora >= (momento_banca - timedelta(minutes=15))
    except:
        return True # Se não tiver data/hora, libera por padrão

# Filtra quem pertence ao professor e ainda não foi feito
pendentes = df_escalacao[(df_escalacao['Email'].str.lower() == st.session_state.email) & (~df_escalacao['Alunos'].isin(feitos))].copy()

# Aplica a trava de tempo
pendentes['liberado'] = pendentes.apply(verificar_liberacao, axis=1)
visiveis = pendentes[pendentes['liberado'] == True].copy()

# Ordena por Data e Hora (quem apresenta antes aparece primeiro)
if not visiveis.empty:
    visiveis['ordem_tempo'] = pd.to_datetime(visiveis['Data'].astype(str) + ' ' + visiveis['Hora'].astype(str))
    visiveis = visiveis.sort_values(by='ordem_tempo')

if visiveis.empty:
    proximas = pendentes[pendentes['liberado'] == False]
    if not proximas.empty:
        st.info("⏳ Você tem bancas agendadas, mas elas só serão liberadas no horário previsto.")
    else:
        st.balloons()
        st.success("🎉 Todas as suas bancas foram concluídas!")
else:
    lista_grupos = visiveis["Alunos"].tolist()
    aluno_selecionado = st.selectbox("🎯 Selecione o Grupo (Ordem de Apresentação):", [""] + lista_grupos)

    if aluno_selecionado:
        dados = visiveis[visiveis["Alunos"] == aluno_selecionado].iloc[0]
        turma_bruta = str(dados['Turma']).strip().upper()

        with st.expander("📖 Detalhes do Trabalho", expanded=True):
            st.write(f"**Trabalho:** {turma_bruta}")
            st.write(f"**Título:** {dados['Titulo']}")
            st.write(f"**Orientador:** {dados['Orientador']}")

        @st.fragment
        def formulario_avaliacao():
            st.write("### 📝 Critérios")
            notas = {}
            
            # (Aqui seguem as mesmas regras de rubrica TCC I, II, MCM V já validadas)
            if "TCC I" in turma_bruta and "TCC II" not in turma_bruta:
                rubrica = {"Tema Contemporâneo": (3, "Explicação..."), "Resumo": (1, "Explicação..."), "Introdução": (5, "Explicação..."), "Justificativa/Problema": (5, "Explicação..."), "Objetivos": (5, "Explicação..."), "Metodologia": (10, "Explicação..."), "Referências": (1, "Explicação..."), "Apresentação Oral": (10, "Explicação..."), "Coerência": (10, "Explicação..."), "Qualidade Visual": (9, "Explicação..."), "Tempo (10-15min)": (1, "Explicação...")}
                nota_max = 60
            elif "TCC II" in turma_bruta:
                rubrica = {"Tema e Resumo": (4, "Contemporaneidade..."), "Introdução": (5, "Justificativa..."), "Metodologia": (5, "Rigor..."), "Resultados": (5, "Descrição..."), "Discussão e Conclusão": (10, "Análise..."), "Referências": (1, "Fontes..."), "Apresentação Oral": (10, "Domínio..."), "Coerência": (10, "Lógica..."), "Qualidade Visual": (9, "Slides..."), "Tempo (15-20min)": (1, "Tempo...")}
                nota_max = 60
            elif "MCM V" in turma_bruta:
                rubrica = {"Resumo": (10, "Síntese"), "Introdução": (10, "Objetivos"), "Metodologia": (10, "Desenho"), "Resultados": (20, "Análise"), "Discussão": (10, "Crítica"), "Conclusão": (10, "Fechamento"), "Redação/ABNT": (10, "Normas"), "Arguição": (10, "Segurança"), "Apresentação": (10, "Domínio")}
                nota_max = 100
            else:
                rubrica = {"Domínio de Conteúdo": (5, "Resposta banca"), "Coerência": (5, "Lógica"), "Comunicação": (5, "Postura"), "Organização/Tempo": (5, "Gestão"), "Recursos Visuais": (5, "Qualidade"), "Métodos": (5, "Adequação")}
                nota_max = 30

            st.warning(f"**Nota máxima: {nota_max} pts**")
            for item, (p, help_t) in rubrica.items():
                notas[item] = st.slider(f"{item} (0-{p})", 0, p, 0, help=help_t, key=f"sld_{item}")

            total = sum(notas.values())
            st.markdown(f"## Total: {total} / {nota_max}")

            if st.button("🚀 GRAVAR AVALIAÇÃO"):
                try:
                    df_res_atual = conn.read(worksheet="Respostas", ttl=0)
                    nova_linha = pd.DataFrame([{"Avaliador": nome_avaliador, "Email_Avaliador": st.session_state.email, "Alunos": aluno_selecionado, "Titulo": dados['Titulo'], "Nota_Final": total, "Data_Hora": datetime.now().strftime("%d/%m/%Y %H:%M")}])
                    df_final = pd.concat([df_res_atual, nova_linha], ignore_index=True)
                    conn.update(worksheet="Respostas", data=df_final)
                    st.success("✅ GRAVADO!")
                    time.sleep(1.5)
                    st.rerun()
                except:
                    st.error("Erro ao gravar. Tente novamente.")

        formulario_avaliacao()
