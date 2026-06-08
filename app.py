import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta
import time
import pytz 
import random

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CRIVO - Gestão Acadêmica", layout="centered")

# INJEÇÃO DE CSS ORIGINAL: Oculta elementos estruturais e fixa o design profissional do botão azul clássico
st.markdown("""
    <style>
    header {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden;}
    
    .stException, .stDetails, div[data-testid="stNotification"] code, pre, code {
        display: none !important;
        visibility: hidden !important;
    }
    
    .stButton button {
        width: 100% !important;
        border-radius: 10px !important;
        height: 3.5em !important;
        background-color: #002147 !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Força a limpeza do cache local para sincronização imediata
st.cache_data.clear()

# 2. FUSO HORÁRIO DE BRASÍLIA
fuso_bruta = pytz.timezone('America/Sao_Paulo')

def obter_agora():
    return datetime.now(fuso_bruta)

def tratar_nome_curto(nome_completo):
    if not nome_completo or pd.isna(nome_completo):
        return ""
    partes = str(nome_completo).strip().split()
    if len(partes) > 1:
        return f"{partes[0]} {partes[1]}"
    return partes[0]

# 3. CONEXÃO COM GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data_forced(aba):
    try:
        return conn.read(worksheet=aba, ttl=0, cache_id=str(random.randint(1, 100000)))
    except:
        return pd.DataFrame()

df_escalacao = get_data_forced("Escalacao")

if df_escalacao.empty:
    st.error("Conectando ao banco de dados... Por favor, aguarde um instante.")
    time.sleep(1)
    st.rerun()

# Limpeza e padronização rigorosa das colunas
df_escalacao = df_escalacao.dropna(how='all')
if 'Turma' in df_escalacao.columns:
    df_escalacao = df_escalacao[df_escalacao['Turma'].astype(str).str.strip().replace('nan', '') != '']

for col in df_escalacao.columns:
    col_limpa = str(col).strip().lower()
    if col_limpa in ['aptidão defesa', 'assinatura orientador', 'email_orientador']:
        df_escalacao[col] = df_escalacao[col].fillna('').astype(str).str.strip()

# --- MAPEAMENTO DAS COLUNAS DA ESCALAÇÃO ---
colunas_reais = {str(col).strip().lower(): col for col in df_escalacao.columns}

c_av1_email = colunas_reais.get('email_avaliador_1')
c_av1_nome = colunas_reais.get('avaliador_1')
c_av2_email = colunas_reais.get('email_avaliador_2')
c_av2_nome = colunas_reais.get('avaliador_2')
c_sup_email = colunas_reais.get('email_suplente')
c_sup_nome = colunas_reais.get('avaliador_suplente')
c_ori_email = colunas_reais.get('email_orientador')
c_ori_nome = colunas_reais.get('orientador')
c_turma = colunas_reais.get('turma')
c_titulo = colunas_reais.get('titulo')
c_data = colunas_reais.get('data')
c_horario = colunas_reais.get('horario')

c_aptidao_col = colunas_reais.get('aptidão defesa')
c_assinatura_col = colunas_reais.get('assinatura orientador')

c_aluno1 = colunas_reais.get('aluno_1')
c_aluno2 = colunas_reais.get('aluno_2')
c_aluno3 = colunas_reais.get('aluno_3')
c_aluno4 = colunas_reais.get('aluno_4')
c_aluno5 = colunas_reais.get('aluno_5')

def verificar_presenca_email(email, coluna_real):
    if not coluna_real or df_escalacao.empty:
        return False
    return email in df_escalacao[coluna_real].astype(str).str.strip().str.lower().unique()

df_respostas = get_data_forced("Respostas")
colunas_respostas_obrigatorias = ["Avaliador", "Email_Avaliador", "Alunos", "Nota_Final", "Papel", "Data_Hora"]
if df_respostas.empty or not all(col in df_respostas.columns for col in colunas_respostas_obrigatorias):
    df_respostas = pd.DataFrame(columns=colunas_respostas_obrigatorias)

# --- SISTEMA DE ACESSO ---
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
            if verificar_presenca_email(email_limpo, c_av1_email) or verificar_presenca_email(email_limpo, c_av2_email) or verificar_presenca_email(email_limpo, c_sup_email) or verificar_presenca_email(email_limpo, c_ori_email):
                st.session_state.email = email_limpo
                st.query_params["user"] = email_limpo
                st.rerun()
            else:
                st.error("E-mail não autorizado ou não encontrado na escalação ativa.")
    st.stop()

email_user = st.session_state.email
eh_orientador = False
nome_completo_docente = ""

if verificar_presenca_email(email_user, c_ori_email):
    eh_orientador = True
    nome_completo_docente = df_escalacao[df_escalacao[c_ori_email].astype(str).str.lower() == email_user][c_ori_nome].iloc[0]
elif verificar_presenca_email(email_user, c_av1_email):
    nome_completo_docente = df_escalacao[df_escalacao[c_av1_email].astype(str).str.lower() == email_user][c_av1_nome].iloc[0]
elif verificar_presenca_email(email_user, c_av2_email):
    nome_completo_docente = df_escalacao[df_escalacao[c_av2_email].astype(str).str.lower() == email_user][c_av2_nome].iloc[0]
elif verificar_presenca_email(email_user, c_sup_email):
    nome_completo_docente = df_escalacao[df_escalacao[c_sup_email].astype(str).str.lower() == email_user][c_sup_nome].iloc[0]

nome_exibicao = tratar_nome_curto(nome_completo_docente)
cor_primaria = "#002147" if not eh_orientador else "#FF1493"

st.markdown(f"""
    <style>
    .bloco-cabecalho {{
        background-color: {cor_primaria} !important;
        padding: 25px !important;
        border-radius: 12px !important;
        color: white !important;
        margin-bottom: 25px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

sub_titulo_texto = "Sistema de Gestão de Bancas Acadêmicas" if not eh_orientador else "Sistema de Gestão de Orientações"
st.markdown(f"""
    <div class="bloco-cabecalho">
        <h1>🎓 CRIVO</h1>
        <h3>{sub_titulo_texto}</h3>
        <p style="font-size: 0.85em; opacity: 0.8;">© 2026 Desenvolvido por Wanessa Sales de Almeida</p>
    </div>
    """, unsafe_allow_html=True)

def obter_lista_alunos_linha(row):
    lista = []
    for col_aluno in [c_aluno1, c_aluno2, c_aluno3, c_aluno4, c_aluno5]:
        if col_aluno and col_aluno in row and pd.notna(row[col_aluno]):
            nome = str(row[col_aluno]).strip()
            if nome and nome.lower() != "nan" and nome != "":
                lista.append(nome)
    return lista

# --- PROCESSAMENTO SEGURO DE FILTRAGEM ---
pendentes = pd.DataFrame()
total_pendencias_contador = 0

if not df_escalacao.empty:
    if eh_orientador:
        possiveis = df_escalacao[df_escalacao[c_ori_email].astype(str).str.lower() == email_user].copy()
        linhas_pendentes = []
        for idx, row in possiveis.iterrows():
            turma_check = str(row[c_turma]).strip().upper() if c_turma else ""
            if "MCM V" in turma_check or "MCM 5" in turma_check or "TCC I" in turma_check or "TCC 1" in turma_check:
                continue
                
            val_assinatura_real = str(row.get(c_assinatura_col)).strip().replace('nan', '') if c_assinatura_col else ""
            
            if val_assinatura_real == "" or val_assinatura_real.lower() == "none":
                alunos_grupo = obter_lista_alunos_linha(row)
                df_filtrado_user = df_respostas[(df_respostas["Email_Avaliador"].astype(str).str.lower() == email_user) & (df_respostas["Papel"] == "Orientador")]
                avaliados = df_filtrado_user["Alunos"].astype(str).str.strip().tolist()
                alunos_restantes = [a for a in alunos_grupo if a not in avaliados]
                
                linhas_pendentes.append(row)
                total_pendencias_contador += len(alunos_restantes) if alunos_restantes else 1
        if linhas_pendentes:
            pendentes = pd.DataFrame(linhas_pendentes)
    else:
        cond_banca = pd.Series(False, index=df_escalacao.index)
        if c_av1_email: cond_banca |= (df_escalacao[c_av1_email].astype(str).str.lower() == email_user)
        if c_av2_email: cond_banca |= (df_escalacao[c_av2_email].astype(str).str.lower() == email_user)
        if c_sup_email: cond_banca |= (df_escalacao[c_sup_email].astype(str).str.lower() == email_user)
            
        possiveis = df_escalacao[cond_banca].copy()
        linhas_pendentes = []
        for idx, row in possiveis.iterrows():
            alunos_grupo = obter_lista_alunos_linha(row)
            string_grupo_banca = ", ".join(alunos_grupo)
            ja_avaliou = df_respostas[(df_respostas["Email_Avaliador"].astype(str).str.lower() == email_user) & (df_respostas["Papel"] == "Banca") & (df_respostas["Alunos"].astype(str).str.strip() == string_grupo_banca.strip())]
            if ja_avaliou.empty and alunos_grupo:
                linhas_pendentes.append(row)
                total_pendencias_contador += 1
        if linhas_pendentes:
            pendentes = pd.DataFrame(linhas_pendentes)

# --- AMBIENTE VISUAL DO DOCENTE COM TRAVA DE SAÍDA RESTAURADA ---
col_user, col_exit = st.columns([3, 1])
with col_user:
    st.write(f"**Docente:** {nome_exibicao} ({'Orientador' if eh_orientador else 'Banca Examinadora'})")
with col_exit:
    if st.button("Sair"):
        if total_pendencias_contador > 0:
            st.session_state.tentou_sair_com_pendencia = True
        else:
            st.session_state.clear()
            st.query_params.clear()
            st.rerun()

# TRAVA DE SAÍDA ATIVA
if st.session_state.get("tentou_sair_com_pendencia", False):
    st.warning(f"⚠️ **Atenção:** Ainda possui **{total_pendencias_contador}** avaliações pendentes registradas no seu nome!")
    col_cancela, col_confirma = st.columns(2)
    with col_cancela:
        if st.button("🔄 Voltar e Avaliar"):
            st.session_state.tentou_sair_com_pendencia = False
            st.rerun()
    with col_confirma:
        if st.button("🏃 Sair Mesmo Assim"):
            st.session_state.clear()
            st.query_params.clear()
            st.rerun()
    st.stop()

if pendentes.empty:
    st.balloons()
    st.success("🎉 Todas as suas avaliações pendentes foram concluídas!")
    if "grupo_selecionado" in st.session_state:
        del st.session_state["grupo_selecionado"]
else:
    def gerar_display_grupo(row):
        alunos = obter_lista_alunos_linha(row)
        return ", ".join([tratar_nome_curto(n) for n in alunos])
        
    pendentes['Display_Grupo'] = pendentes.apply(gerar_display_grupo, axis=1)
    lista_grupos_display = pendentes["Display_Grupo"].tolist()
    
    if "grupo_selecionado" not in st.session_state or st.session_state["grupo_selecionado"] not in lista_grupos_display:
        st.session_state["grupo_selecionado"] = ""

    idx_selecao = 0
    if st.session_state["grupo_selecionado"] in lista_grupos_display:
        idx_selecao = lista_grupos_display.index(st.session_state["grupo_selecionado"]) + 1

    selecionado_display = st.selectbox("🎯 Escolha o Grupo para Avaliar:", [""] + lista_grupos_display, index=idx_selecao)
    st.session_state["grupo_selecionado"] = selecionado_display

    if selecionado_display and selecionado_display != "":
        dados = pendentes[pendentes["Display_Grupo"] == selecionado_display].iloc[0]
        turma_bruta = str(dados[c_turma]).strip().upper() if c_turma else ""
        alunos_reais_lista = obter_lista_alunos_linha(dados)
        string_grupo_completo = ", ".join(alunos_reais_lista)
        linha_index_planilha = dados.name + 2 

        with st.expander("📖 Informações do Trabalho", expanded=True):
            st.write(f"**Turma:** {turma_bruta}")
            st.write(f"**Título:** {dados[c_titulo] if c_titulo else ''}")
            st.write(f"**Orientador:** {tratar_nome_curto(dados[c_ori_nome]) if c_ori_nome else ''}")
            st.write(f"**Integrantes do Grupo:** {string_grupo_completo}")

        aluno_alvo_final = string_grupo_completo
        exibir_formulario_notas = True
        exibir_tela_aptidao_final = False

        if eh_orientador:
            df_filtrado_user = df_respostas[(df_respostas["Email_Avaliador"].astype(str).str.lower() == email_user) & (df_respostas["Papel"] == "Orientador")]
            avaliados_na_aba = df_filtrado_user["Alunos"].astype(str).str.strip().tolist()
            lista_alunos_individuais = [a for a in alunos_reais_lista if a not in avaliados_na_aba]
            
            if lista_alunos_individuais:
                aluno_alvo_final = st.selectbox("👤 Selecione o Aluno para atribuir a nota individual:", lista_alunos_individuais)
            else:
                exibir_formulario_notas = False
                if "TCC II" in turma_bruta or "TCC 2" in turma_bruta:
                    exibir_tela_aptidao_final = True
                else:
                    st.success("Todos os alunos deste grupo já foram avaliados!")
                    try:
                        st.cache_data.clear()
                        df_auto = conn.read(worksheet="Escalacao", ttl=0, cache_id=str(random.randint(1,999)))
                        df_auto.loc[linha_index_planilha - 2, c_assinatura_col] = "CONCLUÍDO VIA APP"
                        conn.update(worksheet="Escalacao", data=df_auto)
                        st.session_state["grupo_selecionado"] = ""
                        time.sleep(0.5)
                        st.rerun()
                    except:
                        pass

        # --- TELA 2: FICHA DE APTIDÃO ---
        if eh_orientador and exibir_tela_aptidao_final:
            st.markdown("---")
            st.subheader("📋 TELA 2: Ficha de Aptidão de Defesa (Exclusivo TCC II)")
            
            with st.form("form_aptidao_tcc2"):
                resposta_aptidao = st.radio(
                    "**O projeto de Trabalho de Conclusão de Curso (TCC II) entregue pelo grupo encontra-se:**",
                    ["", "APTO para apresentação", "INAPTO para apresentação"], index=0
                )
                assinatura_texto = st.text_input("**Assinatura Digital (Digite seu Nome Completo para assinar):**").strip()
                
                if st.form_submit_button("🚀 ENVIAR PARECER E CONCLUIR BANCA"):
                    if resposta_aptidao == "" or assinatura_texto == "":
                        st.error("Preencha todos os campos obrigatórios.")
                    else:
                        with st.spinner("Gravando parecer..."):
                            try:
                                st.cache_data.clear()
                                df_atualizar_linha = conn.read(worksheet="Escalacao", ttl=0, cache_id=str(random.randint(1,999)))
                                df_atualizar_linha[c_aptidao_col] = df_atualizar_linha[c_aptidao_col].fillna('').astype(str)
                                df_atualizar_linha[c_assinatura_col] = df_atualizar_linha[c_assinatura_col].fillna('').astype(str)
                                
                                df_atualizar_linha.loc[linha_index_planilha - 2, c_aptidao_col] = str(resposta_aptidao)
                                df_atualizar_linha.loc[linha_index_planilha - 2, c_assinatura_col] = str(assinatura_texto)
                                
                                conn.update(worksheet="Escalacao", data=df_atualizar_linha)
                                st.balloons()
                                st.success("🎉 Concluído com sucesso!")
                                st.session_state["grupo_selecionado"] = ""
                                time.sleep(1)
                                st.rerun()
                            except:
                                st.error("Erro ao salvar. Tente novamente.")

        # --- TELA 1: FORMULÁRIO DE NOTAS INDIVIDUAIS ---
        elif exibir_formulario_notas:
            rubrica = {}
            if eh_orientador:
                st.info(f"🌱 Avaliando individualmente o discente: **{aluno_alvo_final}**")
                if "MCM IV" in turma_bruta or "MCM 4" in turma_bruta:
                    rubrica = {
                        "Desenv. - Envolvimento e Responsabilidade": (5, "Participação proativa."),
                        "Desenv. - Relação com Orientador / Diálogo": (5, "Relação colaborativa."),
                        "Desenv. - Desempenho e Cumprimento de Tarefas": (5, "Desempenho satisfatório."),
                        "Desenv. - Pontualidade e Compromisso": (5, "Pontualidade mantida."),
                        "Responsabilidade com a Aprendizagem": (5, "Responsabilidade evidente."),
                        "Texto - Justificativa do Estudo": (6, "Clareza na relevância."),
                        "Texto - Objetivo Geral e Específicos": (6, "Objetivos bem formulados."),
                        "Texto - Fundamentação Teórica / Referências": (6, "Referencial teórico relevante."),
                        "Texto - Metodologia Proposta": (6, "Método bem descrito."),
                        "Texto - Cronograma de Execução": (3, "Cronograma estruturado."),
                        "Texto - Estrutura, Linguagem e Formatação": (3, "Segue as normas."),
                        "Relatório - Relatório de Pesquisa": (10, "Apreciação técnica final.")
                    }
                elif "TCC II" in turma_bruta or "TCC 2" in turma_bruta:
                    rubrica = {
                        "Discente - Envolvimento e Responsabilidade": (5, "Participação proativa."),
                        "Discente - Relação com Orientador / Diálogo": (5, "Relação colaborativa."),
                        "Discente - Desempenho / Cumprimento de Tarefas": (4, "Desempenho satisfatório."),
                        "Discente - Pontualidade e Compromisso": (3, "Pontualidade mantida."),
                        "Responsabilidade com a Aprendizagem": (3, "Responsabilidade evidente."),
                        "Artigo - Estruturação e Escrita Científica": (5, "Fluidez e concisão."),
                        "Artigo - Fundamentação e Atualização Bibliográfica": (4, "Fundamentação crítica."),
                        "Artigo - Apresentação e Discussão dos Resultados": (4, "Discussão crítica."),
                        "Artigo - Rigor Metodológico": (4, "Métodos bem descritos."),
                        "Artigo - Conclusão e Relevância Científica": (3, "Conclusão clara.")
                    }
            else:
                st.info("🎓 Rubrica de Avaliação da Banca (Nota para o Grupo todo).")
                if "MCM IV" in turma_bruta or "MCM 4" in turma_bruta:
                    rubrica = {
                        "Delineamento - Rigor Científico e Metodologia": (10, "Procedimentos propostos."),
                        "Apresentação Oral - Clareza e Domínio": (10, "Domínio conceitual."),
                        "Coerência - Estrutura Geral do Projeto": (10, "Lógica interna.")
                    }
                elif "TCC I" in turma_bruta or "TCC 1" in turma_bruta:
                    rubrica = {
                        "Tema": (3, "Clareza tema."), "Resumo": (1, "Qualidade resumo."), "Introdução": (5, "Contextualização."),
                        "Justificativa": (5, "Relevância."), "Objetivos": (5, "Mensuráveis."), "Metodologia": (10, "Desenho estudo."),
                        "Referências": (1, "Normas."), "Apresentação Oral": (10, "Domínio."), "Coerência": (10, "Lógica interna."),
                        "Qualidade Visual": (9, "Slides."), "Tempo": (1, "Tempo regulamentar.")
                    }
                elif "TCC II" in turma_bruta or "TCC 2" in turma_bruta or "MCM V" in turma_bruta or "MCM 5" in turma_bruta:
                    rubrica = {
                        "Tema/Resumo": (4, "Qualidade técnica."), "Introdução": (5, "Fundamentação."), "Metodologia": (5, "Execução método."),
                        "Resultados": (5, "Clareza dados."), "Discussão": (10, "Capacidade crítica."), "Referências": (1, "Rigor técnico."),
                        "Apresentação Oral": (10, "Segurança."), "Coerência": (10, "União lógica."), "Qualidade Visual": (9, "Slides."),
                        "Tempo": (1, "Tempo regulamentar.")
                    }

            if rubrica:
                v_max = sum(p for p, h in rubrica.values())
                st.write(f"### 📝 Critérios (Máximo: {v_max} pontos)")
                
                notas = {}
                for item, (p, help_t) in rubrica.items():
                    passo_slider = 0.5 if p == 1 else 1
                    valor_padrao = 0.0 if p == 1 else 0
                    notas[item] = st.slider(f"**{item} ({p} pts)**", min_value=valor_padrao, max_value=float(p), value=valor_padrao, step=passo_slider, key=f"s_{item}_{aluno_alvo_final}")

                total = sum(notas.values())
                st.markdown(f"## Nota Atribuída: {total} / {v_max}")

                if st.button("🚀 GRAVAR AVALIAÇÃO NO SISTEMA", key=f"btn_save_{aluno_alvo_final}"):
                    with st.spinner("Gravando notas..."):
                        try:
                            st.cache_data.clear()
                            df_at = conn.read(worksheet="Respostas", ttl=0, cache_id=str(random.randint(1,999)))
                            if df_at.empty or not all(col in df_at.columns for col in colunas_respostas_obrigatorias):
                                df_at = pd.DataFrame(columns=colunas_respostas_obrigatorias)
                            
                            nova_l = pd.DataFrame([{
                                "Avaliador": nome_completo_docente, 
                                "Email_Avaliador": email_user, 
                                "Alunos": aluno_alvo_final, 
                                "Nota_Final": total, 
                                "Papel": "Orientador" if eh_orientador else "Banca",
                                "Data_Hora": obter_agora().strftime("%d/%m/%Y %H:%M")
                            }])
                            df_f = pd.concat([df_at, nova_l], ignore_index=True)
                            conn.update(worksheet="Respostas", data=df_f)
                            
                            st.success("✅ Avaliação gravada com sucesso!")
                            time.sleep(0.5)
                            st.rerun()
                        except:
                            st.error("Erro na sincronização. Tente gravar novamente.")
