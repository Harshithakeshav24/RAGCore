from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def encode(self, texts):
        return self.model.encode(texts)


if __name__ == "__main__":
    model = EmbeddingModel()

    text = ["RAGCore is an intelligent knowledge retrieval system."]

    vector = model.encode(text)

    print("Embedding created successfully.")
    print("Vector shape:", vector.shape)
