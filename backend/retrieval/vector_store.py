import chromadb


class VectorStore:
    def __init__(self, collection_name="ragcore"):
        self.client = chromadb.PersistentClient(
            path="data/chroma"
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name
        )

    def add_documents(self, chunks, embeddings):
        ids = [
            f"{chunk['source']}_{chunk['page']}_{i}"
            for i, chunk in enumerate(chunks)
        ]

        documents = [chunk["text"] for chunk in chunks]

        metadatas = [
            {
                "source": chunk["source"],
                "page": chunk["page"]
            }
            for chunk in chunks
        ]

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadatas
        )

        print(f"Added {len(chunks)} chunks to vector store.")

    def search(self, query_embedding, n_results=3):
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results
        )

        return results


if __name__ == "__main__":
    store = VectorStore()

    print("Vector store initialized successfully.")
    print("Collection:", store.collection.name)
