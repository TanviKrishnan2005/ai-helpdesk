from app.services.retriever import search_knowledge_base


results = search_knowledge_base(
    "My Wi-Fi is not working"
)

for result in results:
    print("\nFILE:", result["name"])
    print("SCORE:", result["score"])
    print("CONTENT:")
    print(result["content"])