import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_cohere import CohereEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=_PROJECT_ROOT / ".env", override=True)

def build_vector_store():
    # 1. Load the patient data
    file_path = _PROJECT_ROOT / "data" / "patient_info.txt"
    print(f"Loading data from: {file_path}")
    
    loader = TextLoader(str(file_path))
    documents = loader.load()

    # 2. Chunk the text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=150,
        chunk_overlap=30
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} document(s) into {len(chunks)} chunks.")


    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing COHERE_API_KEY")

    embeddings = CohereEmbeddings(
        model="embed-multilingual-v3.0",
        cohere_api_key=api_key
    )

    persist_directory = str(_PROJECT_ROOT / "chroma_db")
    
   
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    
    print(f"Vector store successfully built at: {persist_directory}")

if __name__ == "__main__":
    build_vector_store()