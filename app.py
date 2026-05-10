# --- 5. RUBRICAS COM EXPLICAÇÕES (HELP) ---
turma = str(dados['Turma'])
notas = {}

# Dicionários com Item: (Peso, Explicação)
if "TCC" in turma:
    rubrica = {
        "Tema": (3, "Avalia a relevância e delimitação do tema."),
        "Introdução": (5, "Avalia a contextualização e o problema de pesquisa."),
        "Metodologia": (10, "Avalia o rigor científico e descrição dos métodos."),
        "Apresentação Oral": (10, "Avalia a postura, dicção e clareza do apresentador."),
        "Coerência": (10, "Avalia se o trabalho segue uma linha lógica do início ao fim."),
        "Qualidade Visual": (10, "Avalia a organização e design dos slides."),
        "Tempo": (2, "Pontuação máxima para quem respeita o limite de tempo.")
    }
elif "MCM IV" in turma:
    rubrica = {
        "Domínio de Conteúdo": (5, "Conhecimento demonstrado sobre o caso clínico."),
        "Coerência": (5, "Lógica entre diagnóstico e conduta."),
        "Comunicação": (5, "Clareza na exposição das ideias."),
        "Organização": (5, "Estrutura da apresentação."),
        "Recursos Visuais": (5, "Uso adequado de imagens e gráficos."),
        "Métodos": (5, "Explicação da abordagem utilizada.")
    }
else: # MCM V
    rubrica = {
        "Resumo": (10, "Qualidade da síntese do trabalho."),
        "Introdução": (10, "Fundamentação teórica."),
        "Metodologia": (10, "Desenho do estudo e análise."),
        "Resultados": (20, "Apresentação clara dos dados obtidos."),
        "Discussão": (10, "Confronto com a literatura."),
        "Conclusão": (10, "Fechamento adequado das questões."),
        "Redação/ABNT": (10, "Normatização e correção gramatical."),
        "Arguição": (10, "Capacidade de resposta aos questionamentos."),
        "Apresentação": (10, "Fluidez e domínio de palco.")
    }

st.write(f"### Avaliando Turma: {turma}")
for item, (p, help_text) in rubrica.items():
    # O help_text faz as informações explicativas voltarem!
    notas[item] = st.slider(f"{item} (Máx: {p})", 0, p, step=1, help=help_text)

total = sum(notas.values())
