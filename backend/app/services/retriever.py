from pathlib import Path

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


BASE_DIR = Path(__file__).resolve().parents[3]
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"

model = SentenceTransformer("all-MiniLM-L6-v2")


def load_documents():
    documents = []

    for file_path in KNOWLEDGE_BASE_DIR.glob("*.txt"):
        content = file_path.read_text(encoding="utf-8")

        documents.append({
            "name": file_path.name,
            "content": content
        })

    return documents


def search_knowledge_base(query, top_k=2):
    documents = load_documents()

    if not documents:
        return []

    document_texts = [
        document["content"]
        for document in documents
    ]

    document_embeddings = model.encode(document_texts)
    query_embedding = model.encode([query])

    similarities = cosine_similarity(
        query_embedding,
        document_embeddings
    )[0]

    ranked_documents = sorted(
        zip(documents, similarities),
        key=lambda item: item[1],
        reverse=True
    )

    return [
        {
            "name": document["name"],
            "content": document["content"],
            "score": float(score)
        }
        for document, score in ranked_documents[:top_k]
    ]