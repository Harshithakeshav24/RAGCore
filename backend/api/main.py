from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf.errors import PdfReadError

from backend.ingestion.document_loader import load_pdf
from backend.ingestion.chunker import chunk_documents
from backend.retrieval.vector_store import VectorStore
from backend.rag_pipeline import RAGPipeline


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DOCUMENTS_DIR = BASE_DIR / "data" / "documents"

DOCUMENTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="RAGCore API",
    description="Enterprise Knowledge Retrieval and Generation System",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================
# SERVICES
# ============================================================

vector_store = VectorStore()

rag_pipeline = RAGPipeline()


# ============================================================
# REQUEST MODEL
# ============================================================

class QueryRequest(BaseModel):
    question: str


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():

    return {
        "name": "RAGCore",
        "description": "Enterprise Knowledge Retrieval and Generation System",
        "status": "online"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():

    return {
        "status": "healthy"
    }


# ============================================================
# UPLOAD PDF
# ============================================================

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided."
        )

    filename = Path(file.filename).name

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    document_id = str(uuid4())

    file_path = (
        DOCUMENTS_DIR
        / f"{document_id}_{filename}"
    )

    try:

        # ----------------------------------------------------
        # READ UPLOADED FILE
        # ----------------------------------------------------

        file_bytes = await file.read()

        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty."
            )

        # ----------------------------------------------------
        # SAVE PDF
        # ----------------------------------------------------

        file_path.write_bytes(file_bytes)

        # ----------------------------------------------------
        # LOAD PDF
        # ----------------------------------------------------

        documents = load_pdf(
            str(file_path)
        )

        if not documents:
            raise HTTPException(
                status_code=400,
                detail="No readable text was found in the PDF."
            )

        # ----------------------------------------------------
        # ADD METADATA
        # ----------------------------------------------------

        for document in documents:

            if not hasattr(document, "metadata"):
                continue

            document.metadata["document_id"] = document_id

            document.metadata["source"] = filename

            if "page" in document.metadata:

                try:

                    document.metadata["page"] = (
                        int(document.metadata["page"]) + 1
                    )

                except Exception:
                    pass

        # ----------------------------------------------------
        # CHUNK DOCUMENT
        # ----------------------------------------------------

        chunks = chunk_documents(
            documents
        )

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="The PDF could not be split into searchable chunks."
            )

        # ----------------------------------------------------
        # EXTRACT TEXT FROM CHUNKS
        # ----------------------------------------------------

        texts = []

        for chunk in chunks:

            if hasattr(chunk, "page_content"):

                text = chunk.page_content

            elif isinstance(chunk, dict):

                text = chunk.get(
                    "text",
                    ""
                )

            else:

                text = str(chunk)

            texts.append(text)

        # ----------------------------------------------------
        # CREATE EMBEDDINGS
        #
        # IMPORTANT:
        # EmbeddingModel belongs to Retriever.
        #
        # RAGPipeline
        #     |
        #     ---> Retriever
        #              |
        #              ---> EmbeddingModel
        #
        # Do NOT use:
        # rag_pipeline.embedding_model
        #
        # Correct:
        # rag_pipeline.retriever.embedding_model
        # ----------------------------------------------------

        embedding_model = (
            rag_pipeline
            .retriever
            .embedding_model
        )

        # IMPORTANT:
        # Your EmbeddingModel.encode() does NOT accept
        # normalize_embeddings.
        #
        # Therefore we only pass texts.

        embeddings = (
            embedding_model
            .encode(texts)
            .tolist()
        )

        # ----------------------------------------------------
        # STORE DOCUMENTS + EMBEDDINGS
        # ----------------------------------------------------

        vector_store.add_documents(
            chunks,
            embeddings
        )

        print(
            f"Successfully processed: {filename}"
        )

        print(
            f"Pages: {len(documents)}"
        )

        print(
            f"Chunks: {len(chunks)}"
        )

        # ----------------------------------------------------
        # SUCCESS RESPONSE
        # ----------------------------------------------------

        return {
            "message": "Document uploaded and processed successfully.",
            "filename": filename,
            "document_id": document_id,
            "pages": len(documents),
            "chunks": len(chunks)
        }

    except HTTPException:

        if file_path.exists():

            try:
                file_path.unlink()
            except Exception:
                pass

        raise

    except PdfReadError:

        if file_path.exists():

            try:
                file_path.unlink()
            except Exception:
                pass

        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid or readable PDF."
        )

    except Exception as error:

        print(
            f"Upload error: {error}"
        )

        if file_path.exists():

            try:
                file_path.unlink()
            except Exception:
                pass

        raise HTTPException(
            status_code=500,
            detail="Failed to process the uploaded PDF."
        )

    finally:

        try:
            await file.close()
        except Exception:
            pass


# ============================================================
# QUERY
# ============================================================

@app.post("/query")
async def query_documents(
    request: QueryRequest
):

    question = request.question.strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:

        result = rag_pipeline.answer(
            question
        )

        return {
            "answer": result.get(
                "answer",
                ""
            ),
            "sources": result.get(
                "sources",
                []
            )
        }

    except Exception as error:

        print(
            f"Query error: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to generate an answer."
        )


# ============================================================
# LIST DOCUMENTS
# ============================================================

@app.get("/documents")
async def list_documents():

    try:

        documents = []

        for file_path in DOCUMENTS_DIR.iterdir():

            if not file_path.is_file():
                continue

            if not file_path.name.lower().endswith(".pdf"):
                continue

            full_name = file_path.name

            parts = full_name.split(
                "_",
                1
            )

            if len(parts) == 2:

                document_id = parts[0]

                display_filename = parts[1]

            else:

                document_id = full_name

                display_filename = full_name

            documents.append(
                {
                    "document_id": document_id,
                    "filename": display_filename,
                    "size_bytes": file_path.stat().st_size
                }
            )

        documents.sort(
            key=lambda item: item["filename"].lower()
        )

        return {
            "count": len(documents),
            "documents": documents
        }

    except Exception as error:

        print(
            f"Document listing error: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to load documents."
        )


# ============================================================
# DELETE DOCUMENT
# ============================================================

@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: str
):

    try:

        matching_files = list(
            DOCUMENTS_DIR.glob(
                f"{document_id}_*.pdf"
            )
        )

        if not matching_files:

            raise HTTPException(
                status_code=404,
                detail="Document not found."
            )

        # Delete vectors belonging to the document.

        try:

            vector_store.delete_document(
                document_id
            )

        except Exception as error:

            print(
                f"Vector delete warning: {error}"
            )

        # Delete physical PDF files.

        deleted_files = []

        for file_path in matching_files:

            file_path.unlink()

            deleted_files.append(
                file_path.name
            )

        return {
            "message": "Document deleted successfully.",
            "document_id": document_id,
            "files": deleted_files
        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            f"Delete error: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to delete document."
        )


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "backend.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False
    )