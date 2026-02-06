import os
import argparse
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA

# --- Configuration ---
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3.2"

def query_rag(query_text):
    print(f"Querying: {query_text}")
    
    # Initialize embeddings and vectorstore
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
    
    # Initialize Local LLM via Ollama
    llm = ChatOllama(model=LLM_MODEL)
    
    # Create the RetrievalQA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever()
    )
    
    # Execute the query
    response = qa_chain.invoke(query_text)
    return response["result"]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query the local RAG pipeline.")
    parser.add_argument("query", type=str, help="The question to ask.")
    args = parser.parse_args()
    
    if not os.path.exists(DB_DIR):
        print("Vector database not found. Please run ingest.py first.")
    else:
        answer = query_rag(args.query)
        print("\n--- Answer ---")
        print(answer)
