import json
from pathlib import Path

from backend.rag_pipeline import RAGPipeline


EVALUATION_FILE = Path("evaluation/test_questions.json")


def normalize(text):
    return text.lower().strip()


def run_evaluation():

    with open(EVALUATION_FILE, "r", encoding="utf-8") as file:
        test_cases = json.load(file)

    pipeline = RAGPipeline()

    total = len(test_cases)
    passed = 0

    print("\n" + "=" * 70)
    print("RAGCore Evaluation")
    print("=" * 70)

    for index, test_case in enumerate(test_cases, start=1):

        question = test_case["question"]

        expected_source = test_case["expected_source"]

        expected_phrases = test_case[
            "expected_answer_contains"
        ]

        print(f"\nTest {index}/{total}")
        print(f"Question: {question}")

        try:

            result = pipeline.answer(question)

            answer = result.get(
                "answer",
                ""
            )

            sources = result.get(
                "sources",
                []
            )

            answer_lower = normalize(answer)

            # Check expected answer phrases
            answer_passed = all(
                normalize(phrase) in answer_lower
                for phrase in expected_phrases
            )

            # Check expected source
            source_passed = True

            if expected_source is not None:

                source_names = [
                    source.get("source")
                    for source in sources
                ]

                source_passed = (
                    expected_source
                    in source_names
                )

            else:

                source_passed = (
                    len(sources) == 0
                )

            test_passed = (
                answer_passed
                and source_passed
            )

            if test_passed:

                passed += 1

                print("Result: PASS")

            else:

                print("Result: FAIL")

            print(
                f"Answer: {answer}"
            )

            print(
                f"Sources: {sources}"
            )

        except Exception as error:

            print("Result: ERROR")

            print(
                f"Error: {error}"
            )

    accuracy = (
        passed / total * 100
        if total > 0
        else 0
    )

    print("\n" + "=" * 70)

    print(
        f"Evaluation Score: {passed}/{total} "
        f"({accuracy:.1f}%)"
    )

    print("=" * 70)

    return accuracy


if __name__ == "__main__":

    run_evaluation()
