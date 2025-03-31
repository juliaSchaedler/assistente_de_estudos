import os
import tempfile
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
import hashlib

load_dotenv()

def process_large_pdf(uploaded_file):
    """Processamento otimizado para Windows com tratamento de arquivos temporários"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY não encontrada no .env")

    # Cria diretório temporário seguro
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, uploaded_file.name)
    
    try:
        # Salva o arquivo carregado no temporário
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        # Processamento do PDF
        loader = PyPDFLoader(temp_file_path)
        pages = loader.load_and_split()
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=300,
            separators=["\n\n", "\n", " ", ""]
        )
        docs = splitter.split_documents(pages)

        # Embeddings
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=api_key,
            batch_size=20
        )
        
        # Database com hash único
        file_hash = hashlib.md5(uploaded_file.getvalue()).hexdigest()
        persist_dir = f"./db_{file_hash}"
        
        db = Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            persist_directory=persist_dir
        )
        db.persist()
        
        return db
        
    finally:
        # Limpeza garantida
        try:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except Exception as e:
            print(f"Aviso: Erro na limpeza temporária - {str(e)}")
