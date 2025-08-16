from helpers.llm import generate_response, embed_text


print("[TEST] Embedding test:", embed_text("Hello world!"))
print("[TEST] Generation test:", generate_response("You are an AI.", "What is AI?"))
