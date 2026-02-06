import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

# --- Configuration ---
DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "rag_docs")
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
EMBEDDING_MODEL = "nomic-embed-text"

def main():
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)
        print(f"Created {DOCS_DIR}. Please add some .txt files there.")
        return

    print(f"Loading documents from {DOCS_DIR}...")
    loader = DirectoryLoader(DOCS_DIR, glob="**/*.txt", loader_cls=TextLoader)
    documents = loader.load()
    
    if not documents:
        print("No documents found to ingest.")
        return

    print(f"Splitting {len(documents)} documents...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    splits = text_splitter.split_documents(documents)

    print(f"Creating embeddings and storing in {DB_DIR}...")
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    
    # Initialize Chroma vectorstore
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=DB_DIR
    )
    
    print("Ingestion complete. Database persisted.")

if __name__ == "__main__":
    main()
