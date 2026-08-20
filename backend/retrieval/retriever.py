from backend.retrieval.embeddings import EmbeddingModel
from backend.retrieval.vector_store import VectorStore


class Retriever:
    def __init__(self, threshold=1.3):
        self.embedding_model = EmbeddingModel()
        self.vector_store = VectorStore()
        self.threshold = threshold

    def search(self, query, n_results=3):
        query_embedding = self.embedding_model.encode([query])[0]

        results = self.vector_store.search(
            query_embedding,
            n_results=n_results
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        filtered_documents = []
        filtered_metadatas = []
        filtered_distances = []

        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances
        ):
            if distance < self.threshold:
                filtered_documents.append(document)
                filtered_metadatas.append(metadata)
                filtered_distances.append(distance)

        return {
            "documents": [filtered_documents],
            "metadatas": [filtered_metadatas],
            "distances": [filtered_distances]
        }


if __name__ == "__main__":
    retriever = Retriever()

    query = "What technologies does RAGCore use?"

    results = retriever.search(query)

    print("\nSearch results:")

    if not results["documents"][0]:
        print("No sufficiently relevant information found.")

    else:
        for i, document in enumerate(results["documents"][0]):
            print(f"\nResult {i + 1}:")
            print("Distance:", results["distances"][0][i])
            print(document)