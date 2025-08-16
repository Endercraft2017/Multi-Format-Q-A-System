from fastapi import FastAPI, UploadFile, File, HTTPException, Body, Query, Form
from fastapi.responses import JSONResponse
from pathlib import Path
import os
import uvicorn
from fastapi.staticfiles import StaticFiles
from helpers.extraction_helper import detect_mime, ALLOWED_EXTS
from helpers.document_loader import load_document
from helpers.sqlite_helper import init_db, list_documents, list_history, add_qa_entry, rename_document
from helpers.vector_helper import search_documents, search_history, search_in_document
from helpers.llm import generate_response, embed_text

app = FastAPI(title="DocQA Step 1 — Upload & Process")

UPLOADS_DIR = Path("data/uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

MAX_BYTES = 50 * 1024 * 1024  # 50MB

init_db()

def sanitize_filename(name: str) -> str:
    base = os.path.basename(name or "upload")
    return base.replace("..", "").strip()

def save_unique(path: Path) -> Path:
    if not path.exists():
        return path
    stem, ext = path.stem, path.suffix
    i = 1
    while True:
        p = path.with_name(f"{stem}_{i}{ext}")
        if not p.exists():
            return p
        i += 1

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    name = sanitize_filename(file.filename)
    ext = Path(name).suffix.lower()

    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    # Save file
    dest = save_unique(UPLOADS_DIR / name)
    dest.write_bytes(content)

    try:
        # Process the document: extract text, chunk, embed, and store
        print(f"Processing: {dest}")
        load_document(dest)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")

    return JSONResponse({
        "message": "File uploaded and processed successfully",
        "saved_as": dest.name,
        "size_bytes": len(content),
        "mime": detect_mime(dest)
    })

@app.post("/ask")
def ask_question_endpoint(question: str = Body(...), top_k: int = 5):

    if not question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        # Step 1 & 2: Retrieve relevant chunks
        q_embedding = embed_text(question)
        results = search_documents(q_embedding, top_k=top_k)

        if not results:
            return {"question": question, "answer": "No relevant document chunks found.", "sources": None}

        # Step 3: Build context for LLM
        context = "\n\n".join([chunk for _, chunk, _ in results])

        # Step 4: Call LLM
        answer = generate_response(context, question)

        # Step 5: Save to QA history
        sources = ", ".join(set(doc_name for doc_name, _, _ in results))
        add_qa_entry(sources, question, answer, q_embedding)

        return {
            "question": question,
            "answer": answer,
            "sources": sources
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question processing failed: {e}")

@app.get("/documents")
def get_documents():
    """List all stored documents."""
    return list_documents()

@app.post("/document/rename")
def rename_document_endpoint(
    document_name: str = Form(...),
    new_name: str = Form(...)
):
    success = rename_document(document_name, new_name)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to rename document")
    return {"status": "success", "old_name": document_name, "new_name": new_name}

@app.get("/history")
def get_history():
    """List all past Q&A history."""
    return list_history()

@app.get("/history/search")
def search_history_endpoint(q: str = Query(..., min_length=1)):
    """Search Q&A history by keyword."""
    return search_history(q)

@app.post("/search-doc")
def search_document(document_name: str, query: str):
    """Search inside a specific document."""

    if not query.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    source_list = [doc['source'] for doc in list_documents()]
    if document_name not in source_list:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        # Step 1: Embed the query
        q_embedding = embed_text(query)

        # Step 2: Retrieve relevant chunks as tuples (doc_name, chunk_text, score)
        results = search_in_document(document_name, q_embedding)

        if not results:
            return {"question": query, "answer": "No relevant document chunks found.", "sources": None}

        # Step 3: Build context for LLM
        context = "\n\n".join([chunk for _, chunk, _ in results])

        # Step 4: Call LLM
        answer = generate_response(context, query)

        # Step 5: Save to QA history
        sources = ", ".join(set(doc_name for doc_name, _, _ in results))
        add_qa_entry(sources, query, answer, q_embedding)

        return {
            "question": query,
            "answer": answer,
            "sources": sources
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question processing failed: {e}")


frontend_path = os.path.join(os.path.dirname(__file__), '..', 'Frontend')
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="Frontend")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
