import os

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


# Store everything relative to the project directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CHROMA_DIR = os.path.join(BASE_DIR, "vector_db")
COLLECTION_NAME = "meeting_transcript"

# Stable 384-dimensional embedding model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def build_vector_store(transcript: str) -> Chroma:
    print("Building vector store...")

    if not transcript or not transcript.strip():
        raise ValueError("Transcript is empty. Cannot build vector store.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )

    chunks = splitter.split_text(transcript)

    if not chunks:
        raise ValueError("No text chunks were created from the transcript.")

    docs = [
        Document(
            page_content=chunk,
            metadata={"chunk_index": i},
        )
        for i, chunk in enumerate(chunks)
    ]

    print(f"Created {len(docs)} document chunks.")
    print(f"Loading embedding model: {EMBEDDING_MODEL}")

    embeddings = get_embeddings()

    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DIR,
    )

    print("Vector store created successfully.")

    return vector_store


def load_vector_store() -> Chroma:
    embeddings = get_embeddings()

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )

    return vector_store


def get_retriever(vector_store: Chroma, k: int = 4):
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )