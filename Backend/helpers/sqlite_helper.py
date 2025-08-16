# sqlite_helper.py
import sqlite3
import json
import os
from typing import List, Tuple
from datetime import datetime
from config import DB_PATH


def init_db():
    """
    Initializes the SQLite database with tables for documents and Q&A history.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Table for storing PDF chunks and embeddings
    c.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,               
            chunk TEXT NOT NULL,                
            embedding TEXT NOT NULL              
        )
    """)

    # Table for storing Q&A history
    c.execute("""
        CREATE TABLE IF NOT EXISTS qa_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,                         
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            embedding TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ---------- Document Functions ----------
def add_document(source: str, chunk: str, embedding: List[float]):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO documents (source, chunk, embedding)
        VALUES (?, ?, ?)
    """, (source, chunk, json.dumps(embedding)))
    conn.commit()
    conn.close()


def get_all_documents() -> List[Tuple[int, str, str, List[float]]]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, source, chunk, embedding FROM documents")
    rows = c.fetchall()
    conn.close()
    return [(r[0], r[1], r[2], json.loads(r[3])) for r in rows]

def search_by_source(source: str) -> List[Tuple[int, str, str, List[float]]]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, source, chunk, embedding FROM documents WHERE source = ?", (source,))
    rows = c.fetchall()
    conn.close()
    return [(r[0], r[1], r[2], json.loads(r[3])) for r in rows]


def delete_source(source: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM documents WHERE source = ?", (source,))
    conn.commit()
    conn.close()


# ---------- Q&A History Functions ----------
def add_qa_entry(source: str, question: str, answer: str, embedding: List[float]):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO qa_history (source, question, answer, embedding, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (source, question, answer, json.dumps(embedding), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_qa_history(source: str = None) -> List[Tuple[int, str, str, str, str]]:
    """
    Retrieves Q&A history. If a source is given, filters by it.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if source:
        c.execute("SELECT * FROM qa_history WHERE source = ? ORDER BY id DESC", (source,))
    else:
        c.execute("SELECT * FROM qa_history ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def search_history(keyword: str):
    """
    Search Q&A history for entries containing the keyword in either
    the question or the answer.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    query = f"%{keyword}%"
    c.execute("""
        SELECT id, source, question, answer, timestamp
        FROM qa_history
        WHERE question LIKE ? OR answer LIKE ?
        ORDER BY id DESC
    """, (query, query))
    rows = c.fetchall()
    conn.close()
    return [
        {"id": r[0], "source": r[1], "question": r[2], "answer": r[3], "timestamp": r[4]}
        for r in rows
    ]


def list_documents():
    """
    Return a distinct list of documents with a chunk count, newest first.
    [
      {"source": "fileA.pdf", "chunks": 12},
      {"source": "fileB.txt", "chunks": 5},
      ...
    ]
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT source,
               COUNT(*) AS chunks,
               MAX(id) AS last_id
        FROM documents
        GROUP BY source
        ORDER BY last_id DESC
    """)
    rows = c.fetchall()
    conn.close()
    return [{"source": r[0], "chunks": r[1]} for r in rows]

def rename_document(source: str, new_name: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE documents SET source = ? WHERE source = ?", (new_name, source))
    c.execute("UPDATE qa_history SET source = ? WHERE source = ?", (new_name, source))
    conn.commit()
    conn.close()
    return True

def list_history(source: str = None):
    """
    Returns Q&A history formatted as a list of dicts:
    [
      {"id": 1, "source": "sample_doc.txt", "question": "...", "answer": "...", "timestamp": "..."},
      ...
    ]
    """
    rows = get_qa_history(source)
    return [
        {
            "id": r[0],
            "source": r[1],
            "question": r[2],
            "answer": r[3],
            "timestamp": r[5]
        }
        for r in rows
    ]

def get_all_chunks():
    """Return all stored document chunks."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT source, chunk, embedding FROM documents")
    rows = c.fetchall()
    conn.close()
    return [(r[0], r[1], json.loads(r[2])) for r in rows]
