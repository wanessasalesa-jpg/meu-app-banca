import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

st.set_page_config(page_title="Avaliação Afya Marabá", layout="centered")

# --- CONEXÃO DIRETA E PROTEGIDA ---
# O parâmetro ttl=0 evita que o app use dados antigos em cache
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_escalacao = conn.read(worksheet="Escalacao", ttl=0)
except Exception as e:
    st.error(f"Erro de conexão: {e}")
    st.info("Verifique se as chaves JSON estão nos Secrets e se o e-mail da Service Account é EDITOR na planilha.")
    st.stop()

st.title("🎓 Portal de Avaliação - Afya Marabá")

# --- LOGIN ---
email_input = st.text_input("Acesso restrito: Digite seu e-mail", placeholder="exemplo@afya.com.br").strip().lower()

if email_input:
    if email_input in df_escalacao['Email'].str.lower().unique():
        prof_dados = df_escalacao[df_escalacao['Email'].str.lower() == email_input].iloc[0]
        st.success(f"Bem-vindo(a), Prof(a). {prof_dados['Avaliador']}!")

        # --- FILTRO DE PENDENTES ---
        try:
            df_respostas = get_data("Respostas")
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
                dados = pendentes[pendentes["Alunos"] == aluno_selecionado].iloc[0]
                turma = str(dados['Turma'])
                
                # --- TRAVA DE HORÁRIO ---
                try:
                    agora = datetime.now()
                    dt_banca = datetime.strptime(str(dados['Data']), '%d/%m/%Y').date()
                    hr_banca = datetime.strptime(str(dados['Horario']), '%H:%M').time()
                    if agora < datetime.combine(dt_banca, hr_banca):
                        st.warning(f"⏳ Disponível apenas em {dados['Data']} às {dados['Horario']}.")
                        st.stop()
                except:
                    pass

                st.info(f"📚 **Título:** {dados['Titulo']}")
                
                # --- RUBRICAS OFICIAIS ---
                notas = {}
                if "TCC I" in turma and "TCC II" not in turma:
                    rubrica = {
                        "Tema Contemporâneo": (3, "Escolha de tema contemporâneo."),
                        "Resumo": (1, "Autoexplicativo, objetivos e DECS."),
                        "Introdução": (5, "Clareza e sequência lógica."),
                        "Justificativa/Problema": (5, "Formatação e conteúdo."),
                        "Objetivos": (5, "Claros e exequíveis."),
                        "Metodologia": (10, "Rigor científico e ética."),
                        "Referências": (1, "Fontes confiáveis."),
                        "Apresentação Oral": (10, "Segurança e domínio."),
                        "Coerência": (10, "Sintonia fala/texto."),
                        "Qualidade Visual": (9, "Material estruturado."),
                        "Tempo (10-15min)": (1, "Respeito ao tempo.")
                    }
                elif "TCC II" in turma:
                    rubrica = {
                        "Tema e Resumo": (4, "Resumo e DECS."),
                        "Introdução": (5, "Objetivos claros."),
                        "Metodologia": (5, "Rigor e ética."),
                        "Resultados": (5, "Responde ao objetivo."),
                        "Discussão/Conclusão": (10, "Análise crítica."),
                        "Referências": (1, "Fontes listadas."),
                        "Apresentação Oral": (10, "Postura e domínio."),
                        "Coerência": (10, "Sintonia fala/texto."),
                        "Qualidade Visual": (9, "Material estruturado."),
                        "Tempo (15-20min)": (1, "Respeito ao tempo.")
                    }
                elif "MCM IV" in turma:
                    rubrica = {
                        "Domínio": (5, "Conhecimento."), "Coerência": (5, "Lógica."),
                        "Comunicação": (5, "Clareza."), "Organização/Tempo": (5, "Gestão."),
                        "Recursos": (5, "Audiovisual."), "Métodos": (5, "Adequação.")
                    }
                else: # MCM V
                    rubrica = {
                        "Resumo": (10, "Síntese."), "Introdução": (10, "Objetivos."),
                        "Metodologia": (10, "Desenho."), "Resultados": (20, "Dados."),
                        "Discussão": (10, "Crítica."), "Conclusão": (10, "Pertinência."),
                        "Redação": (10, "ABNT."), "Arguição": (10, "Autonomia."),
                        "Apresentação": (10, "Domínio.")
                    }

                for item, (p, help_t) in rubrica.items():
                    notas[item] = st.slider(f"{item} (Máx: {p})", 0, p, step=1, help=help_t)

                total = sum(notas.values())
                st.markdown(f"### Nota Final: **{total}**")

                # --- SALVAMENTO ---
                if st.button("Confirmar e Salvar"):
                    try:
                        nova_linha = pd.DataFrame([{
                            "Avaliador": email_input,
                            "Alunos": aluno_selecionado,
                            "Titulo": dados['Titulo'],
                            "Nota_Final": total
                        }])
                        conn.create(worksheet="Respostas", data=nova_linha)
                        
                        st.balloons()
                        st.success("✅ Gravado! Redirecionando...")
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
    else:
        st.error("E-mail não cadastrado.")
