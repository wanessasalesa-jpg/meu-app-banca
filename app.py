import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

st.set_page_config(page_title="Avaliação Afya Marabá", layout="centered")

# --- CONEXÃO COM CACHE INTELIGENTE (Para evitar erro 429) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(aba, tempo_cache=120):
    """Lê os dados e guarda na memória por 2 min para economizar cota do Google"""
    return conn.read(worksheet=aba, ttl=tempo_cache)

# 1. CARREGAMENTO INICIAL
try:
    # Escalacao pode ter um cache maior (não muda toda hora)
    df_escalacao = get_data("Escalacao", tempo_cache=300)
except Exception as e:
    if "429" in str(e):
        st.error("🚫 O Google pediu uma pausa. Aguarde 1 minuto e recarregue a página.")
    else:
        st.error(f"Erro de conexão: {e}")
    st.stop()

st.title("🎓 Portal de Avaliação - Afya Marabá")

# --- LOGIN ---
email_input = st.text_input("Acesso restrito: Digite seu e-mail", placeholder="exemplo@afya.com.br").strip().lower()

if email_input:
    if email_input in df_escalacao['Email'].str.lower().unique():
        prof_dados = df_escalacao[df_escalacao['Email'].str.lower() == email_input].iloc[0]
        st.success(f"Bem-vindo(a), Prof(a). {prof_dados['Avaliador']}!")

        # 2. FILTRO DE TRABALHOS PENDENTES (Cache menor para atualizar rápido)
        try:
            df_respostas = get_data("Respostas", tempo_cache=10)
            feitos = df_respostas[df_respostas["Avaliador"] == email_input]["Alunos"].tolist()
        except:
            feitos = []

        meus_trabalhos = df_escalacao[df_escalacao['Email'].str.lower() == email_input]
        pendentes = meus_trabalhos[~meus_trabalhos["Alunos"].isin(feitos)]

        if pendentes.empty:
            st.info("🎉 Todas as avaliações foram concluídas!")
        else:
            aluno_selecionado = st.selectbox("Selecione o grupo de alunos:", [""] + pendentes["Alunos"].tolist())

            if aluno_selecionado:
                dados = pendentes[pendentes["Alunos"] == aluno_selecionado].iloc[0]
                turma_bruta = str(dados['Turma']).strip().upper()
                
                # Aviso de Nota Máxima (RETORNOU!)
                nota_max = 100 if "MCM V" in turma_bruta else (60 if "TCC" in turma_bruta else 30)
                st.warning(f"⚠️ **Nota máxima para {turma_bruta}: {nota_max} pontos.**")
                st.info(f"📚 **Título:** {dados['Titulo']}\n\n👤 **Orientador:** {dados['Orientador']}")

                # 3. RUBRICAS
                notas = {}
                # (Mantendo aqui as rubricas detalhadas que você aprovou anteriormente)
                if "TCC I" in turma_bruta and "TCC II" not in turma_bruta:
                    rubrica = {"Tema": (3, "Contexto."), "Resumo": (1, "DECS."), "Introdução": (5, "Lógica."), "Justificativa": (5, "ABNT."), "Objetivos": (5, "Claros."), "Metodologia": (10, "Rigor."), "Referências": (1, "Fontes."), "Apresentação": (10, "Postura."), "Coerência": (10, "Texto/Fala."), "Qualidade": (9, "Visual."), "Tempo (10-15min)": (1, "Tempo.")}
                elif "TCC II" in turma_bruta:
                    rubrica = {"Tema/Resumo": (4, "DECS."), "Introdução": (5, "Objetivos."), "Metodologia": (5, "Rigor."), "Resultados": (5, "Dados."), "Discussão": (10, "Crítica."), "Referências": (1, "Fontes."), "Apresentação": (10, "Postura."), "Coerência": (10, "Texto/Fala."), "Qualidade": (9, "Visual."), "Tempo (15-20min)": (1, "Tempo.")}
                elif "MCM V" in turma_bruta:
                    rubrica = {"Resumo": (10, "Síntese."), "Introdução": (10, "Objetivos."), "Metodologia": (10, "Desenho."), "Resultados": (20, "Dados."), "Discussão": (10, "Crítica."), "Conclusão": (10, "Lógica."), "Redação": (10, "ABNT."), "Arguição": (10, "Respostas."), "Apresentação": (10, "Domínio.")}
                else:
                    rubrica = {"Domínio": (5, "Resposta."), "Coerência": (5, "Lógica."), "Comunicação": (5, "Postura."), "Organização": (5, "Tempo."), "Recursos": (5, "Slides."), "Métodos": (5, "Adequação.")}

                for item, (p, help_t) in rubrica.items():
                    notas[item] = st.slider(f"{item} (Até {p})", 0, p, 1, help=help_t)

                total = sum(notas.values())
                st.markdown(f"### Nota Final: **{total}** / {nota_max}")

                # 4. SALVAMENTO (Correção do erro de 'Aba já existe')
                if st.button("Confirmar e Salvar Avaliação"):
                    try:
                        nova_linha = pd.DataFrame([{
                            "Avaliador": email_input,
                            "Alunos": aluno_selecionado,
                            "Titulo": dados['Titulo'],
                            "Nota_Final": total
                        }])
                        
                        # IMPORTANTE: Usamos update para não tentar 'criar' a aba de novo
                        # ttl=0 aqui é para ler o dado mais atual antes de salvar
                        df_atual = conn.read(worksheet="Respostas", ttl=0)
                        df_final = pd.concat([df_atual, nova_linha], ignore_index=True)
                        conn.update(worksheet="Respostas", data=df_final)
                        
                        st.balloons()
                        st.success("✅ GRAVADO COM SUCESSO!")
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
    else:
        st.error("E-mail não cadastrado.")
