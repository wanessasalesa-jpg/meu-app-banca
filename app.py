import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta
import time
import pytz 

# Configuração de página
st.set_page_config(page_title="CRIVO - Gestão Acadêmica", layout="centered")

# Fuso horário oficial de Brasília para escala nacional
fuso_bruta = pytz.timezone('America/Sao_Paulo')

# CSS para esconder menus e deixar o visual limpo e profissional
st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stButton button {
        width: 100%;
        border-radius: 10px;
        height: 3.5em;
        background-color: #002147;
        color: white;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CABEÇALHO APENAS TEXTO (Sem risco de erro de imagem) ---
st.title("🎓 CRIVO")
st.subheader("Sistema de Gestão de Bancas Acadêmicas")
st.caption("© 2026 Desenvolvido por Wanessa Sales de Almeida")
st.divider()

# Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(aba, ttl_sec=2):
    return conn.read(worksheet=aba, ttl=ttl_sec)

# 1. CARREGAMENTO DOS DADOS
try:
    df_escalacao = get_data("Escalacao", ttl_sec=300)
except:
    st.error("Sincronizando com o banco de dados... Aguarde.")
    time.sleep(1)
    st.rerun()

# --- SISTEMA DE LOGIN ---
query_params = st.query_params
if "user" in query_params and "email" not in st.session_state:
    st.session_state.email = query_params["user"]

if 'email' not in st.session_state:
    st.write("### Identificação de Avaliador")
    email_raw = st.text_input("Digite seu e-mail cadastrado:").strip()
    if st.button("Acessar Sistema"):
        if email_raw:
            email_limpo = email_raw.lower()
            if email_limpo in df_escalacao['Email'].str.lower().unique():
                st.session_state.email = email_limpo
                st.query_params["user"] = email_limpo
                st.rerun()
            else:
                st.error("E-mail não autorizado ou não encontrado.")
    st.stop()

# --- AMBIENTE DO PROFESSOR ---
prof_dados = df_escalacao[df_escalacao['Email'].str.lower() == st.session_state.email].iloc[0]
nome_avaliador = prof_dados['Avaliador']

col_user, col_exit = st.columns([3, 1])
with col_user:
    st.write(f"**Avaliador:** {nome_avaliador}")
with col_exit:
    if st.button("Sair"):
        del st.session_state.email
        st.query_params.clear()
        st.rerun()

# Busca de trabalhos pendentes
try:
    df_respostas = get_data("Respostas", ttl_sec=0)
    feitos = df_respostas[df_respostas["Email_Avaliador"] == st.session_state.email]["Alunos"].tolist()
except:
    feitos = []

# Lógica de liberação de banca (Fuso Brasília)
agora_local = datetime.now(fuso_bruta).replace(tzinfo=None)

def verificar_liberacao(linha):
    try:
        data_banca = pd.to_datetime(linha['Data'], dayfirst=True).date()
        hora_banca = pd.to_datetime(linha['Horario']).time()
        momento_banca = datetime.combine(data_banca, hora_banca)
        # Libera para preenchimento 15 minutos antes da hora marcada
        return agora_local >= (momento_banca - timedelta(minutes=15))
    except:
        return True

pendentes = df_escalacao[(df_escalacao['Email'].str.lower() == st.session_state.email) & (~df_escalacao['Alunos'].isin(feitos))].copy()

if pendentes.empty:
    st.balloons()
    st.success("🎉 Todas as suas avaliações foram enviadas com sucesso!")
else:
    pendentes['liberado'] = pendentes.apply(verificar_liberacao, axis=1)
    visiveis = pendentes[pendentes['liberado'] == True].copy()

    if visiveis.empty:
        st.warning("⏳ **Aguardando liberação das bancas.**")
        st.info("As fichas de avaliação serão liberadas automaticamente conforme o cronograma.")
    else:
        # Ordenar por horário
        visiveis['ordem_tempo'] = pd.to_datetime(visiveis['Data'].astype(str) + ' ' + visiveis['Horario'].astype(str))
        visiveis = visiveis.sort_values(by='ordem_tempo')
        
        lista_grupos = visiveis["Alunos"].tolist()
        aluno_selecionado = st.selectbox("🎯 Escolha o Grupo para Avaliar:", [""] + lista_grupos)

        if aluno_selecionado:
            dados = visiveis[visiveis["Alunos"] == aluno_selecionado].iloc[0]
            turma_bruta = str(dados['Turma']).strip().upper()
            
            with st.expander("📖 Informações do Trabalho", expanded=True):
                st.write(f"**Grupo:** {aluno_selecionado}")
                st.write(f"**Título:** {dados['Titulo']}")
                st.write(f"**Orientador:** {dados['Orientador']}")

            @st.fragment
            def formulario_avaliacao():
                st.write("### 📝 Critérios de Avaliação")
                notas = {}
                
                # Definição das Rubricas por Turma
                if "TCC I" in turma_bruta and "TCC II" not in turma_bruta:
                    rubrica = {"Tema": (3, "Atualidade."), "Resumo": (1, "Estrutura."), "Introdução": (5, "Lógica."), "Justificativa": (5, "Relevância."), "Objetivos": (5, "Clareza."), "Metodologia": (10, "Rigor."), "Referências": (1, "Atualidade."), "Apresentação Oral": (10, "Domínio."), "Coerência": (10, "Falla/Escrita."), "Qualidade Visual": (9, "Slides."), "Tempo": (1, "Respeito ao limite.")}
                elif "TCC II" in turma_bruta:
                    rubrica = {"Tema/Resumo": (4, "Qualidade."), "Introdução": (5, "Contexto."), "Metodologia": (5, "Rigor."), "Resultados": (5, "Análise."), "Discussão": (10, "Crítica."), "Referências": (1, "Normas."), "Apresentação Oral": (10, "Domínio."), "Coerência": (10, "Lógica."), "Qualidade Visual": (9, "Design."), "Tempo": (1, "Limite.")}
                elif "MCM V" in turma_bruta:
                    rubrica = {"Resumo": (10, "Síntese."), "Introdução": (10, "Fundamentação."), "Metodologia": (10, "Métodos."), "Resultados": (20, "Dados."), "Discussão": (10, "Confronto."), "Conclusão": (10, "Pertinência."), "Redação/ABNT": (10, "Gramática."), "Arguição": (10, "Segurança."), "Apresentação": (10, "Domínio.")}
                else:
                    rubrica = {"Domínio": (10, "Conhecimento."), "Argumentação": (10, "Defesa."), "Organização": (10, "Estrutura.")}

                for item, (p, help_t) in rubrica.items():
                    notas[item] = st.slider(f"**{item} ({p} pts)**", 0, p, 0, help=help_t, key=f"s_{item}")

                total = sum(notas.values())
                st.markdown(f"## Nota Final: {total}")

                tem_zero = any(v == 0 for v in notas.values())
                conf_zero = True
                if tem_zero:
                    st.error("⚠️ Existem critérios com nota zero.")
                    conf_zero = st.checkbox("Confirmo que as notas zero são intencionais.")

                if st.button("🚀 GRAVAR AVALIAÇÃO NO SISTEMA"):
                    if tem_zero and not conf_zero:
                        st.warning("Confirme o checkbox acima para validar as notas zero.")
                    else:
                        try:
                            df_at = conn.read(worksheet="Respostas", ttl=0)
                            nova_l = pd.DataFrame([{
                                "Avaliador": nome_avaliador, 
                                "Email_Avaliador": st.session_state.email, 
                                "Alunos": aluno_selecionado, 
                                "Nota_Final": total, 
                                "Data_Hora": datetime.now(fuso_bruta).strftime("%d/%m/%Y %H:%M")
                            }])
                            df_f = pd.concat([df_at, nova_l], ignore_index=True)
                            conn.update(worksheet="Respostas", data=df_f)
                            st.balloons()
                            st.success("Avaliação salva com sucesso!")
                            time.sleep(2)
                            st.rerun()
                        except:
                            st.error("Erro de conexão. Tente novamente em instantes.")

            formulario_avaliacao()
