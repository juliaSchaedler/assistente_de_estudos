import os
import json
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do modelo Gemini
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro-latest",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.5,
    top_k=40,
    top_p=0.9,
    request_timeout=45
)

def extract_deep_context(db, topic: str, k: int = 5) -> Tuple[List[Dict], str]:
    """Extrai contexto aprofundado do banco vetorial"""
    try:
        docs = db.similarity_search(topic, k=k)
        
        context_data = []
        for doc in docs:
            context_data.append({
                "content": doc.page_content,
                "page": doc.metadata.get("page", "N/A"),
                "source": doc.metadata.get("source", "Documento")
            })
        
        formatted_context = "\n\n".join(
            f"---\nTrecho {i+1} (Página {doc['page']}):\n{doc['content']}\n---"
            for i, doc in enumerate(context_data)
        )
        
        return context_data, formatted_context
        
    except Exception as e:
        raise Exception(f"Erro na extração de contexto: {str(e)}")

def generate_document_summary(db, topic: str, depth: str = "detailed") -> str:
    """Gera resumo com diferentes níveis de profundidade"""
    try:
        _, context = extract_deep_context(db, topic)
        
        prompt_template = """
        Com base EXCLUSIVAMENTE nestes trechos, gere um resumo {depth} sobre '{topic}':
        
        {context}
        
        FORMATO EXIGIDO:
        - Título Principal: [Título]
        - Pontos Chave (3-5):
          1. [Ponto 1] (Ref: Página X)
          2. [Ponto 2] (Ref: Página Y)
        - Aplicações Práticas: [2-3 exemplos]
        - Conexões com Outros Conceitos: [1-2 conexões]
        """
        
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = (
            {"topic": RunnablePassthrough(), 
             "context": RunnablePassthrough(),
             "depth": RunnablePassthrough()}
            | prompt
            | llm
        )
        
        return chain.invoke({
            "topic": topic,
            "context": context,
            "depth": "detalhado" if depth == "detailed" else "básico"
        }).content
        
    except Exception as e:
        return f"⚠️ Erro ao gerar resumo: {str(e)}"

def generate_interactive_quiz(db, topic: str, num_questions: int = 5) -> List[Dict]:
    """Gera questionário interativo com estrutura JSON"""
    try:
        _, context = extract_deep_context(db, topic)
        
        prompt = ChatPromptTemplate.from_template("""
        Gere {num_questions} perguntas de múltipla escolha sobre '{topic}' baseadas nestes trechos:
        
        {context}
        
        FORMATO EXIGIDO (lista JSON):
        [
            {{
                "question": "Texto completo da pergunta",
                "options": [
                    "A) Opção 1",
                    "B) Opção 2", 
                    "C) Opção 3",
                    "D) Opção 4"
                ],
                "correct_answer": "Letra completa da opção correta (ex: 'A) Opção 1')",
                "explanation": "Explicação detalhada com referência ao trecho X"
            }}
        ]
        """)
        
        chain = prompt | llm
        response = chain.invoke({
            "topic": topic,
            "context": context,
            "num_questions": num_questions
        }).content
        
        # Extrai o JSON da resposta
        try:
            start = response.find('[')
            end = response.rfind(']') + 1
            return json.loads(response[start:end])
        except json.JSONDecodeError:
            raise Exception(f"Resposta inválida do modelo: {response}")
            
    except Exception as e:
        raise Exception(f"Erro ao gerar questionário: {str(e)}")

def generate_flashcards_data(db, topic: str, num_flashcards: int = 10) -> List[Dict]:
    """Gera flashcards em formato estruturado"""
    try:
        context_data, _ = extract_deep_context(db, topic, k=7)
        
        prompt = ChatPromptTemplate.from_template("""
        Crie {num_flashcards} flashcards sobre '{topic}' baseados nestes trechos:
        
        {context}
        
        FORMATO EXIGIDO (lista JSON):
        [
            {{
                "frente": "Pergunta ou conceito",
                "verso": "Resposta completa",
                "fonte": "Página X"
            }}
        ]
        """)
        
        chain = prompt | llm
        response = chain.invoke({
            "topic": topic,
            "context": "\n".join(
                f"Trecho {i+1} (Página {doc['page']}): {doc['content']}"
                for i, doc in enumerate(context_data)
            ),
            "num_flashcards": num_flashcards
        }).content
        
        # Processa a resposta JSON
        try:
            start = response.find('[')
            end = response.rfind(']') + 1
            return json.loads(response[start:end])
        except json.JSONDecodeError:
            raise Exception(f"Resposta inválida do modelo: {response}")
            
    except Exception as e:
        raise Exception(f"Erro ao gerar flashcards: {str(e)}")

def answer_question(db, question: str, context_topic: str = "") -> str:
    """Responde perguntas sobre o conteúdo do documento"""
    try:
        _, context = extract_deep_context(db, context_topic or question, k=5)
        
        prompt = ChatPromptTemplate.from_template("""
        Responda à pergunta baseando-se EXCLUSIVAMENTE no documento abaixo:
        
        Contexto:
        {context}
        
        Pergunta: {question}
        
        Regras:
        1. Seja preciso e cite trechos específicos
        2. Formato: "Segundo a página X... [resposta]"
        3. Se não souber: "Não encontrei essa informação no documento"
        """)
        
        chain = prompt | llm
        return chain.invoke({
            "question": question,
            "context": context
        }).content
        
    except Exception as e:
        return f"⚠️ Erro ao responder: {str(e)}"
