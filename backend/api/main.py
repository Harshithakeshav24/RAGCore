from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import shutil
import uuid

from backend.ingestion.document_loader import load_pdf
from backend.ingestion.chunker import chunk_documents
from backend.retrieval.embeddings import EmbeddingModel
from backend.retrieval.vector_store import VectorStore
from backend.rag_pipeline import RAGPipeline


app = FastAPI(
    title="RAGCore API",
    description="Enterprise Knowledge Retrieval and Generation API",
    version="1.0.0"
)


# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# CONFIGURATION
# =========================

DOCUMENTS_DIR = Path("data/documents")
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# COMPONENTS
# =========================

embedding_model = EmbeddingModel()
vector_store = VectorStore()
rag_pipeline = RAGPipeline()


# =========================
# REQUEST MODELS
# =========================

class QueryRequest(BaseModel):
    question: str


# =========================
# ROOT
# =========================

@app.get("/")
def root():

    return {
        "message": "RAGCore API is running"
    }


# =========================
# HEALTH
# =========================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# =========================
# LIST DOCUMENTS
# =========================

@app.get("/documents")
def list_documents():

    documents = []

    stored_documents = vector_store.collection.get(
        include=["metadatas"]
    )

    metadata_list = stored_documents.get(
        "metadatas",
        []
    )

    document_ids = {}

    for metadata in metadata_list:

        if metadata:

            document_id = metadata.get(
                "document_id"
            )

            source = metadata.get(
                "source"
            )

            if document_id and source:

                document_ids[document_id] = source


    for file_path in DOCUMENTS_DIR.glob("*.pdf"):

        matching_id = None

        for document_id, source in document_ids.items():

            if source == file_path.name:

                matching_id = document_id

                break


        documents.append({
            "document_id": matching_id,
            "filename": file_path.name,
            "size_bytes": file_path.stat().st_size
        })


    return {
        "count": len(documents),
        "documents": documents
    }


# =========================
# UPLOAD DOCUMENT
# =========================

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    if not file.filename.lower().endswith(".pdf"):

        await file.close()

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )


    document_id = str(
        uuid.uuid4()
    )


    file_path = (
        DOCUMENTS_DIR /
        file.filename
    )


    try:

        with file_path.open("wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )


        await file.close()


        documents = load_pdf(
            str(file_path)
        )


        if not documents:

            raise ValueError(
                "The PDF contains no readable pages."
            )


        chunks = chunk_documents(
            documents
        )


        if not chunks:

            raise ValueError(
                "No readable text was found in the PDF."
            )


        texts = [
            chunk["text"]
            for chunk in chunks
        ]


        embeddings = embedding_model.encode(
            texts
        )


        vector_store.add_documents(
            chunks,
            embeddings,
            document_id=document_id
        )


        return {

            "message":
                "Document uploaded and processed successfully.",

            "filename":
                file.filename,

            "document_id":
                document_id,

            "pages":
                len(documents),

            "chunks":
                len(chunks)
        }


    except Exception as e:

        await file.close()


        if file_path.exists():

            try:

                file_path.unlink()

            except PermissionError:

                pass


        raise HTTPException(

            status_code=500,

            detail=
                f"Document processing failed: {str(e)}"
        )


# =========================
# DELETE DOCUMENT
# =========================

@app.delete(
    "/documents/{document_id}"
)
def delete_document(
    document_id: str
):

    try:

        result = vector_store.collection.get(

            where={
                "document_id":
                    document_id
            },

            include=[
                "metadatas"
            ]
        )


        ids = result.get(
            "ids",
            []
        )


        metadatas = result.get(
            "metadatas",
            []
        )


        if not ids:

            raise HTTPException(

                status_code=404,

                detail=
                    "Document not found."
            )


        source = None


        if metadatas:

            source = metadatas[0].get(
                "source"
            )


        vector_store.collection.delete(
            ids=ids
        )


        if source:

            file_path = (
                DOCUMENTS_DIR /
                source
            )


            if file_path.exists():

                try:

                    file_path.unlink()

                except PermissionError:

                    pass


        return {

            "message":
                "Document deleted successfully.",

            "document_id":
                document_id,

            "filename":
                source,

            "deleted_chunks":
                len(ids)
        }


    except HTTPException:

        raise


    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=
                f"Document deletion failed: {str(e)}"
        )


# =========================
# QUERY
# =========================

@app.post("/query")
def query_document(
    request: QueryRequest
):

    if not request.question.strip():

        raise HTTPException(

            status_code=400,

            detail=
                "Question cannot be empty."
        )


    result = rag_pipeline.answer(
        request.question
    )


    return result
