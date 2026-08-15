def chunk_documents(documents, chunk_size=500, overlap=50):
    """Split documents into smaller overlapping chunks."""

    chunks = []

    for document in documents:
        text = document["text"]

        start = 0

        while start < len(text):
            end = start + chunk_size

            chunk_text = text[start:end]

            if chunk_text.strip():
                chunks.append({
                    "text": chunk_text,
                    "page": document["page"],
                    "source": document["source"]
                })

            start += chunk_size - overlap

    return chunks
