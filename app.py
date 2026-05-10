import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="Avaliação Afya Marabá", layout="centered")

# --- TENTATIVA DE CONEXÃO DIRETA ---
try:
    # Se os Secrets estiverem funcionando, ele usa. 
    # Se não, ele tentará ler as chaves que você configurou.
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_escalacao = conn.read(worksheet="Escalacao", ttl=0)
except Exception as e:
    st.error(f"Erro de conexão detectado: {e}")
    st.info("💡 Verifique se o e-mail da 'Service Account' (client_email) foi adicionado à planilha como EDITOR.")
    st.stop()

st.title("🎓 Portal de Avaliação - Afya Marabá")

# --- 2. LOGIN ---
email_input = st.text_input("Digite seu e-mail cadastrado", placeholder="exemplo@afya.com.br").strip().lower()

if email_input:
    if email_input in df_escalacao['Email'].str.lower().unique():
        prof_dados = df_escalacao[df_escalacao['Email'].str.lower() == email_input].iloc[0]
        prof_nome = prof_dados['Avaliador']
        st.success(f"Olá, Prof. {prof_nome}!")

        # --- 3. FILTRO ---
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
                turma = str(dados['Turma']) # Definido aqui para evitar o NameError

                # --- 4. TRAVA DE TEMPO ---
                try:
                    agora = datetime.now()
                    dt_banca = datetime.strptime(str(dados['Data']), '%d/%m/%Y').date()
                    hr_banca = datetime.strptime(str(dados['Horario']), '%H:%M').time()
                    if agora < datetime.combine(dt_banca, hr_banca):
                        st.warning("⏳ Horário da banca ainda não atingido.")
                        st.stop()
                except:
                    pass

                st.info(f"📚 **Título:** {dados['Titulo']}")
                
                # --- 5. RUBRICAS COM EXPLICAÇÕES ---
                notas = {}
                if "TCC I" in turma and "TCC II" not in turma:
                    rubrica = {
                        "Tema": (3, "Tema contemporâneo e de interesse acadêmico."),
                        "Resumo": (1, "Autoexplicativo com DECS."),
                        "Introdução": (5, "Clareza e sequência lógica."),
                        "Metodologia": (10, "Rigor e ética."),
                        "Apresentação Oral": (10, "Segurança e domínio."),
                        "Coerência": (10, "Fala coerente com texto."),
                        "Qualidade Visual": (9, "Material estruturado."),
                        "Tempo (10-15min)": (12, "Observância do tempo.")
                    }
                elif "TCC II" in turma:
                    rubrica = {
                        "Resultados": (5, "Responde ao objetivo."),
                        "Discussão/Conclusão": (10, "Comparação crítica."),
                        "Apresentação Oral": (10, "Segurança e domínio."),
                        "Tempo (15-20min)": (35, "Observância do tempo total.")
                    }
                else: # MCM
                    rubrica = {"Domínio": (5, "Conhecimento do caso."), "Comunicação": (5, "Postura.")}

                for item, (p, help_t) in rubrica.items():
                    notas[item] = st.slider(f"{item} (Até {p})", 0, p, step=1, help=help_t)

                total = sum(notas.values())
                st.subheader(f"Nota Final: {total}")

                # --- 6. SALVAMENTO CORRIGIDO ---
                if st.button("Finalizar e Gravar"):
                    try:
                        nova_linha = pd.DataFrame([{
                            "Avaliador": email_input,
                            "Alunos": aluno_selecionado,
                            "Titulo": dados['Titulo'],
                            "Nota_Final": total
                        }])
                        
                        # Pegamos o que já existe e grudamos a nova linha
                        try:
                            df_atual = get_data("Respostas")
                            df_final = pd.concat([df_atual, nova_linha], ignore_index=True)
                        except:
                            df_final = nova_linha

                        conn.update(worksheet="Respostas", data=df_final)
                        st.balloons()
                        st.success("Gravado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
