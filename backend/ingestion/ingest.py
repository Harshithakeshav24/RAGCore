from .document_loader import load_pdf
from .chunker import chunk_documents
from backend.retrieval.embeddings import EmbeddingModel
from backend.retrieval.vector_store import VectorStore


PDF_PATH = "data/documents/ragcore_test.pdf"


def ingest_document():
    print("Loading PDF...")

    documents = load_pdf(PDF_PATH)

    print(f"Pages loaded: {len(documents)}")

    print("Creating chunks...")

    chunks = chunk_documents(documents)

    print(f"Chunks created: {len(chunks)}")

    print("Creating embeddings...")

    embedding_model = EmbeddingModel()

    texts = [chunk["text"] for chunk in chunks]

    embeddings = embedding_model.encode(texts)

    print(f"Embeddings created: {embeddings.shape}")

    print("Storing vectors in ChromaDB...")

    vector_store = VectorStore()

    vector_store.add_documents(chunks, embeddings)

    print("Ingestion completed successfully.")


if __name__ == "__main__":
    ingest_document()
