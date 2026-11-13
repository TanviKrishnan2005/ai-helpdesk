from app.services.retriever import search_knowledge_base

queries = [
    # Wi-Fi
    "How do I fix my Wi-Fi?",
    "My laptop cannot connect to the internet.",
    "The network is not working.",

    # Account
    "I cannot log into my account.",
    "I forgot my password.",
    "My account is locked.",

    # Software
    "My application keeps crashing.",
    "How do I fix software issues?",
    "My application is not responding.",

    # IT support
    "What are the IT support hours?",
    "When can I contact the IT helpdesk?",

    # Unsupported queries
    "How can I claim travel reimbursement?",
    "How do I apply for annual leave?",
    "How can I request a salary advance?"
]

MIN_RETRIEVAL_SCORE = 0.25
MIN_SOURCE_SCORE = 0.35

for query in queries:
    print("\n" + "=" * 65)
    print("QUERY:", query)
    print("=" * 65)

    results = search_knowledge_base(query, top_k=3)

    if not results:
        print("No results retrieved. Expected action: CREATE TICKET")
        continue

    best_score = float(results[0]["score"])

    print(f"\nBest score: {best_score:.4f}")

    if best_score < MIN_RETRIEVAL_SCORE:
        print("Decision: CREATE TICKET (below retrieval threshold)")
        continue

    relevant_results = [
    result for result in results
    if float(result["score"]) >= MIN_SOURCE_SCORE
    and result["name"] == results[0]["name"]
]

    for result in results:
        score = float(result["score"])
        status = "PASS" if score >= MIN_SOURCE_SCORE else "FAIL"

        print(
            f"{result['name']} | "
            f"Score: {score:.4f} | "
            f"Source threshold: {status}"
        )

    if relevant_results:
        print("Decision: SEND RELEVANT SOURCES TO OLLAMA")
    else:
        print("Decision: CREATE TICKET (no relevant sources)")