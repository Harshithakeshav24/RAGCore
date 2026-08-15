from backend.retrieval.retriever import Retriever
from backend.generation.llm import LLM


class RAGPipeline:
    def __init__(self):
        self.retriever = Retriever()
        self.llm = LLM()

    def answer(self, question):
        results = self.retriever.search(question)

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]

        # No sufficiently relevant documents found
        if not documents:
            return {
                "answer": (
                    "I couldn't find sufficient information "
                    "in the uploaded documents."
                ),
                "sources": []
            }

        context_parts = []

        for i, document in enumerate(documents):
            source = metadatas[i]["source"]
            page = metadatas[i]["page"]

            context_parts.append(
                f"[Source: {source}, Page: {page}]\n{document}"
            )

        context = "\n\n".join(context_parts)

        prompt = f"""
You are RAGCore, an enterprise document question-answering system.

Answer the user's question using ONLY the information provided
in the context.

Do not use outside knowledge.
Do not invent information.

Context:
{context}

Question:
{question}

Answer:
"""

        response = self.llm.generate(prompt)

        sources = []

        for metadata in metadatas:
            source_info = {
                "source": metadata["source"],
                "page": metadata["page"]
            }

            if source_info not in sources:
                sources.append(source_info)

        return {
            "answer": response,
            "sources": sources
        }


if __name__ == "__main__":
    rag = RAGPipeline()

    question = "Who is the Prime Minister of India?"

    result = rag.answer(question)

    print("\nQuestion:")
    print(question)

    print("\nAnswer:")
    print(result["answer"])

    print("\nSources:")

    if result["sources"]:
        for source in result["sources"]:
            print(
                f"- {source['source']} — Page {source['page']}"
            )
    else:
        print("No relevant sources found.")
