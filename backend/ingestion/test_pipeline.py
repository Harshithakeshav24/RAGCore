from document_loader import load_pdf
from chunker import chunk_documents


pdf_path = "data/documents/ragcore_test.pdf"

documents = load_pdf(pdf_path)

print("Pages loaded:", len(documents))

chunks = chunk_documents(documents)

print("Chunks created:", len(chunks))

for i, chunk in enumerate(chunks, start=1):
    print(f"\n--- Chunk {i} ---")
    print("Source:", chunk["source"])
    print("Page:", chunk["page"])
    print("Text:", chunk["text"])
