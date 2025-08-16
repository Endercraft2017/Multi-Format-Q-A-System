import os
from pathlib import Path
from .vector_helper import store_document_chunks
from .extraction_helper import run_extractor

def recursive_split(text, chunk_size=450, chunk_overlap=0, separators=None):
    if separators is None:
        separators = ["\n\n", "\n", " ", ""]  # Paragraph → line → space → char

    sep = separators[0]
    parts = text.split(sep)

    chunks = []
    current_chunk = ""

    for part in parts:
        if len(current_chunk) + len(sep) + len(part) <= chunk_size:
            if current_chunk:
                current_chunk += sep + part
            else:
                current_chunk = part
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = part

    if current_chunk:
        chunks.append(current_chunk.strip())

    # Split further if chunks are still too big
    if len(separators) > 1:
        refined_chunks = []
        for chunk in chunks:
            if len(chunk) > chunk_size:
                refined_chunks.extend(
                    recursive_split(chunk, chunk_size, chunk_overlap, separators[1:])
                )
            else:
                refined_chunks.append(chunk)
        chunks = refined_chunks

    # Add overlap
    if chunk_overlap > 0 and len(chunks) > 1:
        overlapped_chunks = []
        for i, chunk in enumerate(chunks):
            if i > 0:
                chunk = chunks[i-1][-chunk_overlap:] + chunk
            overlapped_chunks.append(chunk)
        chunks = overlapped_chunks

    return chunks

def load_document(file_path):
    print(f"[LOADER] Loading document: {file_path}")
    """
    Reads a document, chunks it, embeds it, and stores it in the database.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    print(f"[LOADER] Extracting text from: {file_path}")
    text = run_extractor(path)

    if not text.strip():
        print(f"[ERROR] No text found in {file_path}")
        return

    print(f"[LOADER] Splitting text into chunks...")
    chunks = recursive_split(text)

    print(f"[LOADER] Storing document chunks in database...")
    doc_name = os.path.basename(file_path)
    store_document_chunks(doc_name, chunks)

    print(f"[LOADER] Document '{doc_name}' loaded successfully.")