
from helpers.sqlite_helper import init_db, add_document, add_qa_entry, get_all_documents, get_qa_history

# Quick test
init_db()
print("[TEST] Database initialized.")

# Add a sample PDF chunk
add_document("sample.pdf", "This is a test chunk", [0.1, 0.2, 0.3])

# Add a sample Q&A
add_qa_entry("sample.pdf", "What is this chunk about?", "It's a test chunk.")

print("[TEST] Documents:", get_all_documents())
print("[TEST] Q&A History:", get_qa_history("sample.pdf"))