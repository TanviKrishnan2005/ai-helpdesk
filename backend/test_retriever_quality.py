
from app.services.retriever import search_knowledge_base


TEST_QUESTIONS = [
    "What are the IT support working hours?",
    "How do I reset my password?",
    "My Wi-Fi is not connecting. What should I do?",
    "How can I recover my account?",
    "How do I repair a 3D printer's mechanical parts?",
]


def main():
    for question in TEST_QUESTIONS:
        print("\n" + "=" * 70)
        print(f"QUESTION: {question}")

        try:
            results = search_knowledge_base(question, top_k=3)
        except Exception as exc:
            print(f"RETRIEVAL ERROR: {exc}")
            continue

        if not results:
            print("No results returned.")
            continue

        for rank, result in enumerate(results, start=1):
            print(f"\nResult {rank}")
            print(f"File: {result['name']}")
            print(f"Chunk: {result['chunk_id']}")
            print(f"Similarity: {result['score']:.4f}")
            print(f"Passage: {result['content'][:350]}")


if __name__ == "__main__":
    main()
