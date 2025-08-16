# Backend/vector_helper.py

import math
import sqlite3
import json
from typing import List, Tuple
from config import DB_PATH
from . import sqlite_helper, llm

# ---------- Cosine Similarity ----------
def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm_a = math.sqrt(sum(a * a for a in vec1))
    norm_b = math.sqrt(sum(b * b for b in vec2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)

# ---------- Search ----------
def search_documents(query, top_k: int = 5) -> List[Tuple[str, str, float]]:
    """
    Search the database for the most relevant chunks to a query.
    Returns a list of tuples: (doc_name, chunk_text, score)
    """
    # 1. Embed query
    query_embedding = query

    # 2. Fetch all document chunks from DB
    all_chunks = sqlite_helper.get_all_chunks()

    # 3. Calculate similarity
    scored_chunks = []
    for doc_name, chunk_text, chunk_embedding in all_chunks:
        score = cosine_similarity(query_embedding, chunk_embedding)
        scored_chunks.append((doc_name, chunk_text, score))

    # 4. Sort by score (descending) & return top_k
    scored_chunks.sort(key=lambda x: x[2], reverse=True)
    return scored_chunks[:top_k]

def search_history(query: List[float], top_k: int = 2):
    """Return top-k semantically similar Q&A entries."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, source, question, answer, embedding, timestamp FROM qa_history WHERE embedding IS NOT NULL")
    rows = c.fetchall()
    conn.close()

    query_embedding = llm.embed_text(query)
    results = []
    for r in rows:
        try:
            emb = [float(x) for x in json.loads(r[4])] if r[4] else None
            if emb:
                score = cosine_similarity(query_embedding, emb)
                results.append({
                    "id": r[0],
                    "source": r[1],
                    "question": r[2],
                    "answer": r[3],
                    "timestamp": r[5],
                    "score": score
                })
                print(f"Doc: {r[1]} | Score: {score:.4f}")
        except Exception as e:
            print("Skipping entry due to error:", e)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]

def search_in_document(document_names: list[str], query, top_k: int = 2):
    """
    Search specific documents by name using semantic similarity.
    Returns top-k most relevant chunks across all documents.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    results = []
    for document_name in document_names:
        c.execute("SELECT chunk, embedding FROM documents WHERE source = ?", (document_name,))
        rows = c.fetchall()

        for chunk_text, emb_str in rows:
            emb = json.loads(emb_str) if emb_str else None
            if emb:
                score = cosine_similarity(query, emb)
                results.append((document_name, chunk_text, score))

    conn.close()

    # Sort across all documents
    results.sort(key=lambda x: x[2], reverse=True)
    return results[:top_k]


# ---------- Store ----------
def store_document_chunks(doc_name: str, chunks: List[str]):
    """
    Store document chunks with embeddings into the DB.
    """
    for chunk in chunks:
        embedding = llm.embed_text(chunk)
        sqlite_helper.add_document(doc_name, chunk, embedding)