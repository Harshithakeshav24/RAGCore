from pathlib import Path
from pypdf import PdfReader


def load_pdf(file_path):
    """Load text from a PDF file."""
    reader = PdfReader(file_path)

    documents = []

    for page_number, page in enumerate(reader.pages):
        text = page.extract_text()

        if text:
            documents.append({
                "text": text,
                "page": page_number + 1,
                "source": Path(file_path).name
            })

    return documents


if __name__ == "__main__":
    pdf_path = "data/documents/ragcore_test.pdf"

    documents = load_pdf(pdf_path)

    print(f"Pages loaded: {len(documents)}")

    for document in documents:
        print("\n--- Page", document["page"], "---")
        print(document["text"])
