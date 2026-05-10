import streamlit as st

st.set_page_config(page_title="Avaliação Acadêmica Afya", layout="wide")

st.title("📋 Sistema Digital de Avaliação de Bancas")
st.info("Unidade: Marabá - PA")

# --- SELEÇÃO DA TURMA ---
turma = st.selectbox("Selecione o Módulo/Turma:", 
                     ["TCC I", "TCC II", "MCM IV (Projeto)", "MCM V (Final)"])

# --- CADASTRO DINÂMICO DE ALUNOS ---
st.subheader("👥 Identificação do Grupo")
titulo_trabalho = st.text_input("Título do Trabalho")
orientador = st.text_input("Professor(a) Orientador(a)")

# Ajusta limite de alunos conforme a turma
limite_alunos = 5 if "MCM" in turma else 3
num_alunos = st.number_input("Quantidade de alunos no grupo:", min_value=1, max_value=limite_alunos, value=1)

nomes_alunos = []
for i in range(int(num_alunos)):
    nome = st.text_input(f"Nome do Acadêmico {i+1}")
    nomes_alunos.append(nome)

st.divider()

# --- FORMULÁRIO DE NOTAS BASEADO NA RUBRICA ---
st.subheader(f"📝 Rubrica de Avaliação: {turma}")
notas = {}

if turma in ["TCC I", "TCC II"]:
    st.write("Critérios (Sim = 100%, Parcial = 50%, Não = 0%)")
    # Exemplo de itens da sua rubrica de TCC
    itens = ["Tema e Contemporaneidade", "Resumo e Descritores", "Introdução/Justificativa", 
             "Metodologia", "Referências", "Apresentação Oral", "Coerência e Qualidade", "Tempo"]
    
    # Pesos específicos conforme documento [cite: 1, 2]
    pesos = [3, 1, 5, 10, 1, 10, 10, 20] # Simplificado para soma 60
    
    for item in itens:
        notas[item] = st.select_slider(f"Nota para: {item}", options=[0.0, 0.5, 1.0]) # Multiplicador

    total = sum([n * p for n, p in zip(notas.values(), pesos)])
    max_pontos = 60

elif turma == "MCM IV (Projeto)":
    # Itens específicos da rubrica MCM IV 
    itens_mcm4 = ["Domínio do conteúdo", "Coerência com o tema", "Habilidades de comunicação", 
                  "Organização/Tempo", "Recursos audiovisuais", "Adequação objetivos/métodos"]
    
    for item in itens_mcm4:
        notas[item] = st.radio(f"{item}:", [5, 3, 0], horizontal=True, help="5: Pleno, 3: Parcial, 0: Não atende")
    
    total = sum(notas.values())
    max_pontos = 30

elif turma == "MCM V (Final)":
    # Itens específicos da rubrica MCM V 
    notas["Resumo"] = st.slider("Resumo (0-10)", 0, 10)
    notas["Introdução"] = st.slider("Introdução (0-10)", 0, 10)
    notas["Metodologia"] = st.slider("Metodologia (0-10)", 0, 10)
    notas["Resultados"] = st.slider("Resultados e Análise (0-20)", 0, 20)
    notas["Discussão"] = st.slider("Discussão (0-10)", 0, 10)
    notas["Conclusão"] = st.slider("Conclusão (0-10)", 0, 10)
    notas["Redação/ABNT"] = st.slider("Redação/ABNT (0-10)", 0, 10)
    notas["Arguição"] = st.slider("Arguição (0-10)", 0, 10)
    notas["Apresentação"] = st.slider("Apresentação Visual/Oral (0-10)", 0, 10)
    
    total = sum(notas.values())
    max_pontos = 100

# --- RESULTADO FINAL ---
st.divider()
col_result, col_status = st.columns(2)

with col_result:
    st.metric("Nota Final da Banca", f"{total:.2f} / {max_pontos}")

with col_status:
    percentual = (total / max_pontos) * 100
    if percentual >= 70:
        st.success("SITUAÇÃO: APROVADO")
    else:
        st.warning("SITUAÇÃO: REVISÃO / REPROVADO")

if st.button("Finalizar e Gerar Comprovante"):
    st.balloons()
    st.write("### Resumo para Assinatura:")
    st.write(f"**Trabalho:** {titulo_trabalho}")
    st.write(f"**Grupo:** {', '.join(nomes_alunos)}")
    st.write(f"**Nota:** {total}")
    st.write(f"Marabá, 2026")
