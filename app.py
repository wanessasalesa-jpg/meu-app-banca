import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="Avaliação Afya Marabá", layout="centered")

conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNÇÃO DE LIMPEZA DE CACHE PARA ATUALIZAÇÃO EM TEMPO REAL ---
def atualizar_dados():
    try:
        return conn.read(worksheet="Escalacao", ttl=0)
    except:
        st.error("Erro ao acessar a planilha principal.")
        st.stop()

df_escalacao = atualizar_dados()

st.title("🎓 Portal de Avaliação - Afya Marabá")

# --- 1. SEGURANÇA: LOGIN POR E-MAIL ---
email_input = st.text_input("Acesso restrito: Digite seu e-mail cadastrado", placeholder="exemplo@afya.com.br").strip().lower()

if email_input:
    # Verifica se o e-mail consta na coluna de avaliadores (ou coluna específica de e-mail)
    # Supondo que a Coluna 0 agora seja o E-mail para segurança
    if email_input in df_escalacao.iloc[:, 0].str.lower().unique():
        
        prof_nome = df_escalacao[df_escalacao.iloc[:, 0].str.lower() == email_input].iloc[0, 1] # Pega o Nome na Coluna B
        st.success(f"Bem-vindo(a), Prof(a). {prof_nome}!")

        # --- 2. FILTRO DE TRABALHOS PENDENTES ---
        try:
            df_respostas = conn.read(worksheet="Respostas", ttl=0)
            trabalhos_feitos = df_respostas[df_respostas["Avaliador"] == email_input]["Trabalho"].tolist()
        except:
            trabalhos_feitos = []

        # Filtra trabalhos do professor que ainda não foram avaliados
        meus_trabalhos = df_escalacao[df_escalacao.iloc[:, 0].str.lower() == email_input]
        trabalhos_pendentes = meus_trabalhos[~meus_trabalhos["Título"].isin(trabalhos_feitos)]

        if trabalhos_pendentes.empty:
            st.info("🎉 Todas as suas bancas foram avaliadas com sucesso!")
        else:
            trabalho_selecionado = st.selectbox("Selecione o trabalho pendente:", [""] + trabalhos_pendentes["Título"].tolist())

            if trabalho_selecionado:
                dados = trabalhos_pendentes[trabalhos_pendentes["Título"] == trabalho_selecionado].iloc[0]
                
                # --- 3. TRAVA DE DATA E HORÁRIO ---
                agora = datetime.now()
                # Formato esperado na planilha: DD/MM/YYYY e HH:MM
                data_banca = datetime.strptime(dados['Data'], '%d/%m/%Y').date()
                hora_banca = datetime.strptime(dados['Horário'], '%H:%M').time()
                inicio_banca = datetime.combine(data_banca, hora_banca)

                if agora < inicio_banca:
                    st.warning(f"⏳ Este trabalho estará disponível para avaliação em {dados['Data']} às {dados['Horário']}.")
                else:
                    # --- 4. EXIBIÇÃO ORGANIZADA (ORDEM ALFABÉTICA) ---
                    st.success(f"📌 **Orientador(a):** {dados['Orientador']}")
                    
                    with st.expander("Ver Acadêmicos do Grupo"):
                        # Separa nomes por vírgula, limpa espaços e ordena
                        lista_alunos = sorted([a.strip() for a in str(dados['Alunos']).split(',')])
                        for i, aluno in enumerate(lista_alunos, 1):
                            st.write(f"{i}. {aluno}")

                    st.divider()
                    turma = dados['Turma']
                    notas = {}
                    
                    # --- 5. RUBRICAS COM STEP DE 1 PONTO ---
                    st.info(f"Rubrica {turma}")
                    # Exemplo de loop para TCC I (aplique para as outras conforme antes)
                    if "TCC I" in turma:
                        pesos = {"Tema": 3, "Resumo": 1, "Introdução": 5, "Metodologia": 10, "Apresentação": 10, "Coerência": 10, "Qualidade": 9, "Tempo (10-15min)": 2}
                        for item, p in pesos.items():
                            # Step=1.0 garante variação de 1 em 1 ponto
                            notas[item] = st.slider(f"{item} (Até {p} pts)", 0, p, step=1, help="Avaliação em escala inteira.")

                    # --- 6. FINALIZAÇÃO E RESET AUTOMÁTICO ---
                    total = sum(notas.values())
                    st.subheader(f"Nota Final: {total}")

                    if st.button("Finalizar e Enviar Avaliação"):
                        nova_linha = pd.DataFrame([{
                            "Avaliador": email_input,
                            "Trabalho": trabalho_selecionado,
                            "Turma": turma,
                            "Nota_Final": total
                        }])
                        conn.create(worksheet="Respostas", data=nova_linha)
                        st.balloons()
                        st.success("Avaliação salva! Atualizando lista...")
                        st.rerun() # Volta para o início mantendo o login
    else:
        st.error("E-mail não autorizado. Por favor, verifique se digitou corretamente ou contate a coordenação.")
