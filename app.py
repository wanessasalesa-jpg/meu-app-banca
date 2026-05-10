import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="Avaliação Afya Marabá", layout="centered")

# Conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(aba):
    # ttl=0 garante que os dados sejam lidos em tempo real (essencial para a trava de duplicidade)
    return conn.read(worksheet=aba, ttl=0)

# --- 1. CARREGAMENTO DOS DADOS ---
try:
    df_escalacao = conn.read(ttl=0)
except Exception as e:
    st.error("⚠️ Erro de Conexão: Não foi possível ler a aba 'Escalacao'.")
    st.info("Verifique se o link no Secrets foi atualizado para a nova planilha e se as permissões estão como 'Editor'.")
    st.stop()

st.title("🎓 Portal de Avaliação - Afya Marabá")

# --- 2. LOGIN POR E-MAIL ---
email_input = st.text_input("Acesso restrito: Digite seu e-mail cadastrado", placeholder="exemplo@afya.com.br").strip().lower()

if email_input:
    # Verifica se o e-mail consta na lista de avaliadores
    if email_input in df_escalacao['Email'].str.lower().unique():
        prof_dados = df_escalacao[df_escalacao['Email'].str.lower() == email_input].iloc[0]
        prof_nome = prof_dados['Avaliador']
        st.success(f"Bem-vindo(a), Prof(a). {prof_nome}!")

        # --- 3. FILTRO DE GRUPOS PENDENTES (TRAVA DE RE-AVALIAÇÃO) ---
        try:
            df_respostas = get_data("Respostas")
            # Identifica quais grupos de alunos este professor já avaliou
            avaliados = df_respostas[df_respostas["Avaliador"] == email_input]["Alunos"].tolist()
        except:
            avaliados = []

        # Filtra trabalhos atribuídos a este professor e remove os já avaliados
        meus_trabalhos = df_escalacao[df_escalacao['Email'].str.lower() == email_input]
        pendentes = meus_trabalhos[~meus_trabalhos["Alunos"].isin(avaliados)]

        if pendentes.empty:
            st.info("🎉 Excelente! Você concluiu todas as avaliações atribuídas a você.")
        else:
            # Seleção focada nos Alunos conforme solicitado
            aluno_selecionado = st.selectbox("Selecione o grupo de alunos para avaliar:", [""] + pendentes["Alunos"].tolist())

            if aluno_selecionado:
                dados = pendentes[pendentes["Alunos"] == aluno_selecionado].iloc[0]
                
                # --- 4. TRAVA DE DATA/HORÁRIO ---
                try:
                    agora = datetime.now()
                    data_banca = datetime.strptime(str(dados['Data']), '%d/%m/%Y').date()
                    hora_banca = datetime.strptime(str(dados['Horario']), '%H:%M').time()
                    inicio_previsto = datetime.combine(data_banca, hora_banca)
                    bloqueado = agora < inicio_previsto
                except:
                    bloqueado = False # Liberação de segurança caso o formato da data esteja errado

                if bloqueado:
                    st.warning(f"⏳ Esta avaliação só será liberada em {dados['Data']} às {dados['Horario']}.")
                else:
                    st.info(f"📚 **Título:** {dados['Titulo']}")
                    st.write(f"📌 **Orientador(a):** {dados['Orientador']}")
                    
                    st.divider()
                    
                    # --- 5. RUBRICAS (VARIAÇÃO DE 1 EM 1 PONTO) ---
                    turma = str(dados['Turma'])
                    notas = {}
                    
                    # Lógica de pesos por Turma
                    if "TCC" in turma:
                        pesos = {"Tema": 3, "Introdução": 5, "Metodologia": 10, "Apresentação Oral": 10, "Coerência": 10, "Qualidade Visual": 10, "Tempo": 2}
                    elif "MCM IV" in turma:
                        pesos = {"Domínio de Conteúdo": 5, "Coerência": 5, "Comunicação": 5, "Organização": 5, "Recursos Visuais": 5, "Métodos": 5}
                    else: # MCM V
                        pesos = {"Resumo": 10, "Introdução": 10, "Metodologia": 10, "Resultados": 20, "Discussão": 10, "Conclusão": 10, "Redação/ABNT": 10, "Arguição": 10, "Apresentação": 10}

                    st.write(f"### Avaliando Turma: {turma}")
                    for item, p in pesos.items():
                        notas[item] = st.slider(f"{item} (Máx: {p})", 0, p, step=1)

                    total = sum(notas.values())
                    st.subheader(f"Nota Total Atribuída: {total} pts")

                    # --- 6. BOTÃO DE SALVAMENTO E RESET ---
                    if st.button("Finalizar e Gravar Avaliação"):
                        # Organiza a linha para a aba 'Respostas'
                        nova_resposta = pd.DataFrame([{
                            "Avaliador": email_input,
                            "Alunos": aluno_selecionado,
                            "Titulo": dados['Titulo'],
                            "Nota_Final": total
                        }])
                        
                        try:
                            conn.create(worksheet="Respostas", data=nova_resposta)
                            st.balloons()
                            st.success("Sucesso! A avaliação foi gravada e a lista atualizada.")
                            st.rerun() # Reinicia para limpar sliders e remover o grupo da lista
                        except Exception as e:
                            st.error(f"Erro ao salvar: {e}. Verifique se a aba 'Respostas' permite escrita.")
    else:
        st.error("E-mail não autorizado. Verifique se é o mesmo cadastrado na escala.")
