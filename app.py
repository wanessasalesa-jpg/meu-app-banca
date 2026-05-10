import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta
import time

# Configuração estável e limpa
st.set_page_config(page_title="Avaliação Afya", layout="centered")

st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
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
    st.error("Sincronizando...")
    time.sleep(1)
    st.rerun()

st.title("🎓 Avaliação de Bancas")

# --- LÓGICA DE LOGIN PERSISTENTE ---
query_params = st.query_params
if "user" in query_params and "email" not in st.session_state:
    st.session_state.email = query_params["user"]

if 'email' not in st.session_state:
    st.write("### Identificação")
    email_raw = st.text_input("Digite seu e-mail cadastrado:").strip()
    if st.button("Acessar Sistema"):
        if email_raw:
            email_limpo = email_raw.lower()
            if email_limpo in df_escalacao['Email'].str.lower().unique():
                st.session_state.email = email_limpo
                st.query_params["user"] = email_limpo
                st.rerun()
            else:
                st.error("E-mail não encontrado.")
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
        st.query_params.clear()
        st.rerun()

st.divider()

# BUSCA DE PENDENTES
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
                
                # Rubricas originais (TCC I, II, MCM V)
                if "TCC I" in turma_bruta and "TCC II" not in turma_bruta:
                    rubrica = {"Tema Contemporâneo": (3, "Escolha de tema contemporâneo..."), "Resumo": (1, "Autoexplicativo..."), "Introdução": (5, "Clareza..."), "Justificativa/Problema": (5, "Formatação..."), "Objetivos": (5, "Claros..."), "Metodologia": (10, "Tipo de estudo..."), "Referências": (1, "Fontes..."), "Apresentação Oral": (10, "Segurança..."), "Coerência": (10, "Sintonia..."), "Qualidade Visual": (9, "Material..."), "Tempo (10-15min)": (1, "Respeito...")}
                    nota_max = 60
                elif "TCC II" in turma_bruta:
                    rubrica = {"Tema e Resumo": (4, "Contemporaneidade..."), "Introdução": (5, "Justificativa..."), "Metodologia": (5, "Rigor..."), "Resultados": (5, "Concisão..."), "Discussão e Conclusão": (10, "Análise..."), "Referências": (1, "Fontes..."), "Apresentação Oral": (10, "Domínio..."), "Coerência": (10, "Lógica..."), "Qualidade Visual": (9, "Slides..."), "Tempo (15-20min)": (1, "Cumprimento...")}
                    nota_max = 60
                elif "MCM V" in turma_bruta:
                    rubrica = {"Resumo": (10, "Síntese"), "Introdução": (10, "Objetivos"), "Metodologia": (10, "Desenho"), "Resultados": (20, "Análise"), "Discussão": (10, "Crítica"), "Conclusão": (10, "Fechamento"), "Redação/ABNT": (10, "Normas"), "Arguição": (10, "Segurança"), "Apresentação": (10, "Domínio")}
                    nota_max = 100
                else:
                    rubrica = {"Domínio de Conteúdo": (5, "Conhecimento."), "Coerência": (5, "Lógica."), "Comunicação": (5, "Postura."), "Organização/Tempo": (5, "Gestão."), "Recursos Visuais": (5, "Qualidade."), "Métodos": (5, "Adequação.")}
                    nota_max = 30

                st.warning(f"**Nota máxima: {nota_max} pts**")
                for item, (p, help_t) in rubrica.items():
                    notas[item] = st.slider(f"**{item}**", 0, p, 0, help=help_t, key=f"s_{item}")

                total = sum(notas.values())
                st.markdown(f"## Total: {total} / {nota_max}")

                # --- NOVA TRAVA DE SEGURANÇA ---
                tem_zero = any(v == 0 for v in notas.values())
                
                if tem_zero:
                    st.error("⚠️ Atenção: Existem critérios com nota ZERO.")
                    confirmar_zero = st.checkbox("Confirmo que as notas zero são intencionais.")
                else:
                    confirmar_zero = True

                if st.button("🚀 GRAVAR AVALIAÇÃO"):
                    if not confirmar_zero:
                        st.warning("Por favor, revise os critérios ou marque a caixa de confirmação para notas zero.")
                    else:
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
                            st.success("✅ GRAVADO COM SUCESSO!")
                            time.sleep(2)
                            st.rerun()

            formulario_avaliacao()
