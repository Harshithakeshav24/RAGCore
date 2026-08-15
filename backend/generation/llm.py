import os
from dotenv import load_dotenv
from google import genai


load_dotenv()


class LLM:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")

        self.client = genai.Client(api_key=api_key)

    def generate(self, prompt):
        response = self.client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        return response.text


if __name__ == "__main__":
    llm = LLM()

    response = llm.generate(
        "In one sentence, explain what Retrieval-Augmented Generation is."
    )

    print("Generated response:")
    print(response)
