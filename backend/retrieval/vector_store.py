from typing import List, Dict, Any, Optional

import chromadb


class VectorStore:
    def __init__(self, collection_name: str = "ragcore"):
        self.collection_name = collection_name

        self.client = chromadb.PersistentClient(
            path="data/chroma"
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name
        )

    def add_documents(
        self,
        documents,
        embeddings: List[List[float]],
    ) -> None:
        """
        Add document chunks and their embeddings to ChromaDB.
        """

        if not documents:
            return

        if len(documents) != len(embeddings):
            raise ValueError(
                "Number of documents must match "
                "number of embeddings."
            )

        ids = []
        texts = []
        metadatas = []

        for index, document in enumerate(documents):

            # LangChain Document
            if hasattr(document, "page_content"):

                text = document.page_content

                metadata = dict(
                    document.metadata or {}
                )

            # Dictionary document
            elif isinstance(document, dict):

                text = document.get(
                    "text",
                    ""
                )

                metadata = dict(
                    document.get(
                        "metadata",
                        {}
                    )
                )

            # Fallback
            else:

                text = str(document)

                metadata = {}

            source = metadata.get(
                "source",
                "unknown"
            )

            page = metadata.get(
                "page",
                1
            )

            # Make sure metadata is safe for ChromaDB
            metadata["source"] = str(source)
            metadata["page"] = int(page)

            chunk_id = (
                f"{self.collection_name}_"
                f"{index}_"
                f"{abs(hash(text))}"
            )

            ids.append(chunk_id)
            texts.append(text)
            metadatas.append(metadata)

        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        print(
            f"Added {len(documents)} chunks "
            f"to vector store."
        )

    def search(
        self,
        query_embedding: List[float],
        n_results: int = 3,
        top_k: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Search ChromaDB using a query embedding.

        Supports both n_results and top_k.
        """

        if top_k is not None:
            n_results = top_k

        collection_count = self.collection.count()

        if collection_count == 0:
            return {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
            }

        n_results = min(
            n_results,
            collection_count
        )

        results = self.collection.query(
            query_embeddings=[
                query_embedding
            ],
            n_results=n_results,
        )

        return {
            "documents": results.get(
                "documents",
                [[]]
            ),

            "metadatas": results.get(
                "metadatas",
                [[]]
            ),

            "distances": results.get(
                "distances",
                [[]]
            ),
        }

    def count(self) -> int:
        """
        Return the number of stored chunks.
        """

        return self.collection.count()

    def delete_collection(self) -> None:
        """
        Delete the current collection and recreate it.
        """

        try:
            self.client.delete_collection(
                name=self.collection_name
            )
        except Exception:
            pass

        self.collection = (
            self.client.get_or_create_collection(
                name=self.collection_name
            )
        )

    def delete_document(
        self,
        document_id: str
    ) -> None:
        """
        Delete all chunks belonging to a document.
        """

        try:

            results = self.collection.get(
                where={
                    "document_id": document_id
                }
            )

            ids = results.get(
                "ids",
                []
            )

            if ids:
                self.collection.delete(
                    ids=ids
                )

        except Exception as error:

            print(
                f"Vector store delete warning: {error}"
            )


if __name__ == "__main__":

    store = VectorStore()

    print(
        "Vector store initialized successfully."
    )

    print(
        f"Collection: {store.collection.name}"
    )

    print(
        f"Stored chunks: {store.count()}"
    )