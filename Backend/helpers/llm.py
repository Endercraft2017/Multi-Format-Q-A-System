# llm.py
import os
import multiprocessing
from llama_cpp import Llama
from config import LLAMA_CPP_MODEL_DIR, EMBED_MODEL, DEFAULT_MODEL

# Cache for loaded Llama instances
_loaded_models = {}

def get_llm_cpp(model_name: str, embedding: bool = False):
    """
    Loads a llama.cpp model and caches it for reuse.
    """
    if model_name not in _loaded_models:
        model_path = os.path.join(LLAMA_CPP_MODEL_DIR, model_name)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at: {model_path}")

        print(f"[DEBUG] Loading llama-cpp model: {model_path}")

        kwargs = dict(
            model_path=model_path,
            n_ctx=2048,
            n_threads=multiprocessing.cpu_count(),
            use_mmap=True,
            use_mlock=False,
            verbose=False
        )

        if embedding:
            kwargs["embedding"] = True
        else:
            kwargs.update(
                n_batch=256,
                n_parallel=2,
                low_vram=False
            )

        _loaded_models[model_name] = Llama(**kwargs)

    return _loaded_models[model_name]


def embed_text(text: str):
    """
    Generates an embedding vector using the embedding model.
    """
    model = get_llm_cpp(EMBED_MODEL, embedding=True)
    result = model.embed(text)
    return result


def generate_response(context: str, query: str, temperature: float = 0.7, max_tokens: int = 512):
    """
    Generates a chat completion from the main LLM model.
    """
    model = get_llm_cpp(DEFAULT_MODEL, embedding=False)

    prompt = f"""You are an AI assistant. Answer the question in detail using the context provided. 
Include explanations, examples, and relevant information from the context.

Context:
{context}

Question:
{query}

Answer in a clear and concise manner:"""

    response = model(
        prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        stop=["</s>", "User:"]
    )

    if "choices" in response and len(response["choices"]) > 0:
        return response["choices"][0].get("text", "").strip()
    elif "content" in response:
        return response["content"].strip()
    else:
        return ""


if __name__ == "__main__":
    # Quick test
    print("[TEST] Embedding test:", embed_text("Hello world!")[:5])
    print("[TEST] Generation test:", generate_response("You are an AI.", "What is AI?"))
