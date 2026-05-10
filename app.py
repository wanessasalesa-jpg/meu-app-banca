import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="Avaliação Afya Marabá", layout="centered")

conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(aba):
    return conn.read(worksheet=aba, ttl=0)

# --- CARREGAMENTO INICIAL ---
try:
    df_escalacao = get_data("Escalacao")
except Exception as e:
    st.error("Erro: Não foi possível ler a aba 'Escalacao'. Verifique o link no Secrets e o nome da aba.")
    st.stop()

st.title("🎓 Portal de Avaliação - Afya Marabá")

# --- 1. LOGIN POR E-MAIL ---
email_input = st.text_input("Acesso restrito: Digite seu e-mail cadastrado", placeholder="exemplo@afya.com.br").strip().lower()

if email_input:
    if email_input in df_escalacao['Email'].str.lower().unique():
        prof_dados = df_escalacao[df_escalacao['Email'].str.lower() == email_input].iloc[0]
        prof_nome = prof_dados['Avaliador']
        st.success(f"Bem-vindo(a), Prof(a). {prof_nome}!")

        # --- 2. FILTRAR ALUNOS PENDENTES ---
        try:
            df_respostas = get_data("Respostas")
            # Filtra o que este professor já avaliou baseando-se no grupo de alunos
            avaliados = df_respostas[df_respostas["Avaliador"] == email_input]["Alunos"].tolist()
        except:
            avaliados = []

        meus_trabalhos = df_escalacao[df_escalacao['Email'].str.lower() == email_input]
        # Aqui a mágica: o seletor foca nos ALUNOS
        pendentes = meus_trabalhos[~meus_trabalhos["Alunos"].isin(avaliados)]

        if pendentes.empty:
            st.info("🎉 Você concluiu todas as suas avaliações!")
        else:
            aluno_selecionado = st.selectbox("Selecione o grupo de alunos para avaliar:", [""] + pendentes["Alunos"].tolist())

            if aluno_selecionado:
                dados = pendentes[pendentes["Alunos"] == aluno_selecionado].iloc[0]
                
                # --- 3. TRAVA DE DATA/HORÁRIO ---
                try:
                    agora = datetime.now()
                    data_banca = datetime.strptime(str(dados['Data']), '%d/%m/%Y').date()
                    hora_banca = datetime.strptime(str(dados['Horario']), '%H:%M').time()
                    inicio = datetime.combine(data_banca, hora_banca)
                    bloqueado = agora < inicio
                except:
                    bloqueado = False

                if bloqueado:
                    st.warning(f"⏳ Avaliação disponível em {dados['Data']} às {dados['Horario']}.")
                else:
                    st.info(f"📚 **Título:** {dados['Titulo']}")
                    st.write(f"📌 **Orientador(a):** {dados['Orientador']}")
                    
                    st.divider()
                    
                    # --- 4. AVALIAÇÃO (PASSO DE 1 PONTO) ---
                    turma = str(dados['Turma'])
                    notas = {}
                    
                    if "TCC" in turma:
                        pesos = {"Tema": 3, "Introdução": 5, "Metodologia": 10, "Apresentação": 10, "Coerência": 10, "Qualidade Visual": 10, "Tempo": 2}
                    elif "MCM IV" in turma:
                        pesos = {"Domínio": 5, "Coerência": 5, "Comunicação": 5, "Organização": 5, "Recursos": 5, "Métodos": 5}
                    else: # MCM V
                        pesos = {"Resumo": 10, "Introdução": 10, "Metodologia": 10, "Resultados": 20, "Discussão": 10, "Conclusão": 10, "Redação": 10, "Arguição": 10, "Apresentação": 10}

                    for item, p in pesos.items():
                        notas[item] = st.slider(f"{item} (Máx: {p})", 0, p, step=1)

                    total = sum(notas.values())
                    st.subheader(f"Nota Final: {total} pts")

                    if st.button("Finalizar e Gravar Avaliação"):
                        nova_resposta = pd.DataFrame([{
                            "Avaliador": email_input,
                            "Alunos": aluno_selecionado,
                            "Titulo": dados['Titulo'],
                            "Nota_Final": total
                        }])
                        
                        conn.create(worksheet="Respostas", data=nova_resposta)
                        st.balloons()
                        st.success("Avaliação gravada!")
                        st.rerun()
    else:
        st.error("E-mail não cadastrado.")
