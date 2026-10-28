from app.services.retriever import search_knowledge_base

question = "What are the operating hours of the IT support desk?"

results = search_knowledge_base(question, top_k=3)

print("\nQuestion:", question)
print("\nRetrieved passages:")

for result in results:
    print("\n----------------------------")
    print("File:", result["name"])
    print("Chunk:", result["chunk_id"])
    print("Score:", round(result["score"], 4))
    print("Content:", result["content"])