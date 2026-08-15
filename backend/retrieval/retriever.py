from backend.retrieval.embeddings import EmbeddingModel
from backend.retrieval.vector_store import VectorStore


class Retriever:
    def __init__(self):
        self.embedding_model = EmbeddingModel()
        self.vector_store = VectorStore()

    def search(self, query, n_results=3):
        query_embedding = self.embedding_model.encode([query])[0]

        results = self.vector_store.search(
            query_embedding,
            n_results=n_results
        )

        return results


if __name__ == "__main__":
    retriever = Retriever()

    query = "What is this document about?"

    results = retriever.search(query)

    print("\nSearch results:")

    for i, document in enumerate(results["documents"][0]):
        print(f"\nResult {i + 1}:")
        print(document)
