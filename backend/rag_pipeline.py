from backend.retrieval.retriever import Retriever
from backend.generation.llm import LLM


class RAGPipeline:
    def __init__(self):
        self.retriever = Retriever()
        self.llm = LLM()

    def answer(self, question):
        results = self.retriever.search(question)

        documents = results["documents"][0]

        context = "\n\n".join(documents)

        prompt = f"""
Answer the question using only the information provided in the context.

Context:
{context}

Question:
{question}

Answer:
"""

        response = self.llm.generate(prompt)

        return response


if __name__ == "__main__":
    rag = RAGPipeline()

    question = "What is RAGCore?"

    answer = rag.answer(question)

    print("\nQuestion:")
    print(question)

    print("\nAnswer:")
    print(answer)
