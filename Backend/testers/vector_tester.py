# Backend/vector_tester.py

from helpers.sqlite_helper import init_db, get_all_chunks
from helpers.vector_helper import store_document_chunks, search_documents

if __name__ == "__main__":
    print("[TEST] Initializing database...")
    init_db()

    # Test data
    doc_name = "sample_doc.txt"
    chunks = [
        "Python is a popular programming language for AI.",
        "The Eiffel Tower is located in Paris, France.",
        "Artificial Intelligence can be used in many industries."
    ]

    print(f"[TEST] Storing chunks for document: {doc_name}")
    store_document_chunks(doc_name, chunks)

    print("[TEST] Fetching all stored chunks...")
    for row in get_all_chunks():
        print(row)

    print("\n[TEST] Running search for: 'Where is the Eiffel Tower?'")
    results = search_documents("Where is the Eiffel Tower?", top_k=3)
    for doc, chunk, score in results:
        print(f"Doc: {doc} | Score: {score:.4f}\nChunk: {chunk}\n")

    print("\n[TEST] Running search for: 'What is Python used for?'")
    results = search_documents("What is Python used for?", top_k=3)
    for doc, chunk, score in results:
        print(f"Doc: {doc} | Score: {score:.4f}\nChunk: {chunk}\n")
