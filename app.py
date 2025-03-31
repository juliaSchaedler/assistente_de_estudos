import streamlit as st
from rag_processor import process_large_pdf
from features import (
    generate_document_summary,
    generate_interactive_quiz,
    generate_flashcards_data,
    answer_question
)
import time
import json
from typing import List, Dict

# Configuração da página
st.set_page_config(
    page_title="Assistente de Estudos Avançado",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização do estado
if 'db' not in st.session_state:
    st.session_state.db = None
if 'last_topic' not in st.session_state:
    st.session_state.last_topic = ""
if 'flashcards' not in st.session_state:
    st.session_state.flashcards = []
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = []
if 'current_flashcard' not in st.session_state:
    st.session_state.current_flashcard = 0
if 'quiz_answers' not in st.session_state:
    st.session_state.quiz_answers = {}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Sidebar - Upload e configurações
with st.sidebar:
    st.header("📂 Gerenciamento de Documentos")
    uploaded_file = st.file_uploader("Carregar arquivo PDF", type="pdf")
    
    if uploaded_file:
        with st.spinner("Processando documento..."):
            try:
                st.session_state.db = process_large_pdf(uploaded_file)
                st.success("Documento carregado com sucesso!")
                st.session_state.last_topic = ""
                st.session_state.flashcards = []
                st.session_state.quiz_data = []
                st.session_state.chat_history = []
            except Exception as e:
                st.error(f"Erro: {str(e)}")
    
    if st.session_state.db:
        st.divider()
        st.header("⚙️ Configurações")
        st.session_state.last_topic = st.text_input(
            "🔍 Tópico para estudo:",
            value=st.session_state.last_topic,
            placeholder="Ex: Teorema de Pitágoras"
        )

# Área principal
st.title("📚 Assistente de Estudos Interativo")

if st.session_state.db:
    # Abas principais
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📝 Resumo", "❓ Questionário", "🃏 Flashcards"])
    
    # Tab 1: Chat Interativo
    with tab1:
        st.header("Chat sobre o Documento")
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        if prompt := st.chat_input("Faça uma pergunta sobre o documento"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.spinner("Pensando..."):
                try:
                    response = answer_question(
                        st.session_state.db,
                        prompt,
                        st.session_state.last_topic
                    )
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    with st.chat_message("assistant"):
                        st.markdown(response)
                except Exception as e:
                    st.error(f"Erro ao responder: {str(e)}")
    
    # Tab 2: Resumo
    with tab2:
        st.header("Resumo Detalhado")
        if st.button("▶️ Gerar Resumo Completo"):
            if st.session_state.last_topic:
                with st.spinner("Analisando conteúdo profundamente..."):
                    start_time = time.time()
                    result = generate_document_summary(
                        st.session_state.db,
                        st.session_state.last_topic,
                        depth="detailed"
                    )
                    st.markdown(result)
                    st.caption(f"Gerado em {time.time()-start_time:.1f}s | Análise profunda ativada")
            else:
                st.warning("Defina um tópico na barra lateral")
    
    # Tab 3: Questionário Interativo
    with tab3:
        st.header("Questionário Interativo")
        
        if st.button("🔄 Gerar Novo Questionário"):
            if st.session_state.last_topic:
                with st.spinner("Criando perguntas personalizadas..."):
                    st.session_state.quiz_data = generate_interactive_quiz(
                        st.session_state.db,
                        st.session_state.last_topic,
                        num_questions=5
                    )
                    st.session_state.quiz_answers = {}
                    st.rerun()
            else:
                st.warning("Defina um tópico primeiro")
        
        if st.session_state.quiz_data:
            st.divider()
            for i, question in enumerate(st.session_state.quiz_data):
                st.subheader(f"Pergunta {i+1}")
                st.markdown(question["question"])
                
                options = question["options"]
                user_answer = st.radio(
                    f"Selecione uma opção para Pergunta {i+1}",
                    options,
                    key=f"quiz_q_{i}",
                    index=None
                )
                
                if user_answer:
                    st.session_state.quiz_answers[i] = user_answer
                
                if st.session_state.quiz_answers.get(i) == question["correct_answer"]:
                    st.success("✅ Resposta correta!")
                elif st.session_state.quiz_answers.get(i):
                    st.error(f"❌ Resposta incorreta. A correta é: {question['correct_answer']}")
    
    # Tab 4: Flashcards Interativos
    with tab4:
        st.header("Flashcards Interativos")
        
        if st.button("✨ Gerar Novos Flashcards"):
            if st.session_state.last_topic:
                with st.spinner("Criando flashcards personalizados..."):
                    st.session_state.flashcards = generate_flashcards_data(
                        st.session_state.db,
                        st.session_state.last_topic,
                        num_flashcards=10
                    )
                    st.session_state.current_flashcard = 0
                    st.rerun()
            else:
                st.warning("Defina um tópico primeiro")
        
        if st.session_state.flashcards:
            col1, col2 = st.columns([3,1])
            with col1:
                card = st.session_state.flashcards[st.session_state.current_flashcard]
                st.markdown(
                    f"""
                    <div style='border: 2px solid #4e79a7; border-radius: 10px; 
                    padding: 20px; min-height: 200px; margin: 10px 0;'>
                    <h3>{card['frente']}</h3>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                if st.checkbox("Mostrar resposta", key=f"show_answer_{st.session_state.current_flashcard}"):
                    st.markdown(
                        f"""
                        <div style='border: 2px solid #2e7d32; border-radius: 10px; 
                        padding: 20px; min-height: 100px; margin: 10px 0; background-color: #e8f5e9;'>
                        <p><strong>Resposta:</strong> {card['verso']}</p>
                        <p><em>Fonte: {card.get('fonte', 'Documento')}</em></p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            
            with col2:
                st.write("Navegação")
                if st.button("⏮️ Anterior"):
                    if st.session_state.current_flashcard > 0:
                        st.session_state.current_flashcard -= 1
                        st.rerun()
                
                st.write(f"Card {st.session_state.current_flashcard + 1}/{len(st.session_state.flashcards)}")
                
                if st.button("⏭️ Próximo"):
                    if st.session_state.current_flashcard < len(st.session_state.flashcards) - 1:
                        st.session_state.current_flashcard += 1
                        st.rerun()
                
                if st.button("🎯 Aleatório"):
                    import random
                    st.session_state.current_flashcard = random.randint(0, len(st.session_state.flashcards)-1)
                    st.rerun()

else:
    st.info("""
    ## 👋 Bem-vindo ao Assistente de Estudos Interativo!
    
    **Como começar:**
    1. Carregue um documento PDF na barra lateral ➡️
    2. Defina um tópico específico
    3. Explore as ferramentas:
       - 💬 Chat inteligente sobre o conteúdo
       - 📝 Resumos detalhados
       - ❓ Questionários com correção automática
       - 🃏 Flashcards interativos
    """)
    #st.image("https://i.imgur.com/JtQJbZg.png", width=300)

# Rodapé
st.divider()
st.caption("Assistente de Estudos Interativo v3.0 | © 2024")
