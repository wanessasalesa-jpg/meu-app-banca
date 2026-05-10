import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Avaliação de TCC", layout="centered")

st.title("🎓 Sistema de Avaliação de TCC")
st.subheader("Painel do Avaliador")

# 1. Cadastro do Trabalho
with st.expander("1. Informações do Trabalho"):
    nome_aluno = st.text_input("Nome do Aluno")
    titulo_tcc = st.text_input("Título do Trabalho")
    orientador = st.text_input("Professor Orientador")

# 2. Critérios de Avaliação
st.write("### 📝 Notas (0 a 10)")
col1, col2 = st.columns(2)

with col1:
    nota_escrita = st.slider("Qualidade da Escrita/ABNT", 0.0, 10.0, 5.0)
    nota_metodologia = st.slider("Rigor Metodológico", 0.0, 10.0, 5.0)

with col2:
    nota_apresentacao = st.slider("Domínio do Conteúdo (Oral)", 0.0, 10.0, 5.0)
    nota_inovacao = st.slider("Originalidade/Inovação", 0.0, 10.0, 5.0)

comentarios = st.text_area("Comentários e Observações")

# 3. Cálculos
media_final = (nota_escrita + nota_metodologia + nota_apresentacao + nota_inovacao) / 4

# 4. Resultado Final
st.divider()
st.write(f"### Média Final: **{media_final:.2f}**")

if media_final >= 7.0:
    st.success("✅ APROVADO")
else:
    st.error("❌ REPROVADO / REVISÃO")

# Botão para simular salvamento
if st.button("Gerar Resumo da Avaliação"):
    resumo = {
        "Aluno": [nome_aluno],
        "TCC": [titulo_tcc],
        "Média": [media_final],
        "Status": ["Aprovado" if media_final >= 7.0 else "Reprovado"]
    }
    df = pd.DataFrame(resumo)
    st.table(df)
    st.info("Dica: Você pode copiar esses dados para uma planilha!")
