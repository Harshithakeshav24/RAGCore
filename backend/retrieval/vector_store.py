from typing import List, Dict, Any, Optional

import chromadb


class VectorStore:

    def __init__(
        self,
        collection_name: str = "ragcore"
    ):
        self.collection_name = collection_name

        self.client = chromadb.PersistentClient(
            path="data/chroma"
        )

        self.collection = (
            self.client.get_or_create_collection(
                name=collection_name
            )
        )

    def add_documents(
        self,
        documents,
        embeddings: List[List[float]],
    ) -> None:

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

            if hasattr(document, "page_content"):

                text = document.page_content

                metadata = dict(
                    document.metadata or {}
                )

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

            else:

                text = str(document)

                metadata = {}

            text = str(text).strip()

            if not text:
                continue

            source = metadata.get(
                "source",
                "unknown"
            )

            page = metadata.get(
                "page",
                1
            )

            document_id = metadata.get(
                "document_id",
                "unknown"
            )

            try:
                page = int(page)
            except Exception:
                page = 1

            metadata["source"] = str(source)
            metadata["page"] = page
            metadata["document_id"] = str(
                document_id
            )

            safe_document_id = str(
                document_id
            ).replace("-", "")

            chunk_hash = abs(
                hash(text)
            )

            chunk_id = (
                f"{self.collection_name}_"
                f"{safe_document_id}_"
                f"{index}_"
                f"{chunk_hash}"
            )

            ids.append(chunk_id)
            texts.append(text)
            metadatas.append(metadata)

        if not texts:
            return

        # Important:
        # embeddings must correspond exactly
        # to the documents being stored.
        valid_embeddings = embeddings[
            :len(texts)
        ]

        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=valid_embeddings,
            metadatas=metadatas,
        )

        print(
            f"Added {len(texts)} chunks "
            f"to vector store."
        )

    def search(
        self,
        query_embedding: List[float],
        n_results: int = 3,
        top_k: Optional[int] = None,
    ) -> Dict[str, Any]:

        if top_k is not None:
            n_results = top_k

        collection_count = (
            self.collection.count()
        )

        if collection_count == 0:

            return {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
            }

        n_results = max(
            1,
            min(
                n_results,
                collection_count
            )
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

        return self.collection.count()

    def delete_document(
        self,
        document_id: str
    ) -> int:

        document_id = str(
            document_id
        )

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

            if not ids:

                print(
                    f"No vector chunks found for "
                    f"document: {document_id}"
                )

                return 0

            self.collection.delete(
                ids=ids
            )

            print(
                f"Deleted {len(ids)} chunks for "
                f"document: {document_id}"
            )

            return len(ids)

        except Exception as error:

            print(
                f"Vector store delete warning: "
                f"{error}"
            )

            return 0

    def delete_collection(self) -> None:

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

        print(
            f"Vector collection "
            f"'{self.collection_name}' "
            f"reset successfully."
        )


if __name__ == "__main__":

    store = VectorStore()

    print(
        "Vector store initialized successfully."
    )

    print(
        f"Collection: "
        f"{store.collection.name}"
    )

    print(
        f"Stored chunks: "
        f"{store.count()}"
    )