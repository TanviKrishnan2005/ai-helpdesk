
from pathlib import Path
from threading import Lock

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


BASE_DIR = Path(__file__).resolve().parents[3]
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"

MODEL_NAME = "all-MiniLM-L6-v2"

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150

# Load the model only when retrieval is first requested.
model = None
_model_lock = Lock()

_cached_signature = None
_cached_chunks = []
_cached_embeddings = None

_index_lock = Lock()


def get_model():
    """Load the embedding model once, when it is first needed."""
    global model

    if model is None:
        with _model_lock:
            if model is None:
                print(f"Loading embedding model: {MODEL_NAME}")

                model = SentenceTransformer(
                    MODEL_NAME,
                    device="cpu"
                )

                print("Embedding model loaded successfully.")

    return model


def chunk_text(text):
    """Split text into overlapping chunks without losing word boundaries."""
    text = text.strip()

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))

        if end < len(text):
            boundary = text.rfind(" ", start, end)

            if boundary > start:
                end = boundary

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(end - CHUNK_OVERLAP, start + 1)

    return chunks


def load_documents():
    """Load text files and split them into searchable chunks."""
    documents = []

    if not KNOWLEDGE_BASE_DIR.exists():
        return documents

    for file_path in sorted(KNOWLEDGE_BASE_DIR.glob("*.txt")):
        content = file_path.read_text(
            encoding="utf-8",
            errors="replace"
        )

        for index, chunk in enumerate(
            chunk_text(content),
            start=1
        ):
            documents.append({
                "name": file_path.name,
                "chunk_id": index,
                "content": chunk,
            })

    return documents


def build_index():
    """Build or refresh the cached knowledge-base embeddings."""
    global _cached_signature
    global _cached_chunks
    global _cached_embeddings

    with _index_lock:
        files = (
            sorted(KNOWLEDGE_BASE_DIR.glob("*.txt"))
            if KNOWLEDGE_BASE_DIR.exists()
            else []
        )

        signature = tuple(
            (
                str(file_path),
                file_path.stat().st_mtime_ns,
                file_path.stat().st_size,
            )
            for file_path in files
        )

        if signature == _cached_signature:
            return

        _cached_chunks = load_documents()

        if _cached_chunks:
            texts = [
                item["content"]
                for item in _cached_chunks
            ]

            embedding_model = get_model()

            _cached_embeddings = embedding_model.encode(
                texts,
                normalize_embeddings=True,
                show_progress_bar=False,
                batch_size=8,
            )
        else:
            _cached_embeddings = None

        _cached_signature = signature


def search_knowledge_base(query, top_k=3):
    """Return the most relevant knowledge-base chunks."""
    if not query or not query.strip():
        return []

    build_index()

    if not _cached_chunks or _cached_embeddings is None:
        return []

    embedding_model = get_model()

    query_embedding = embedding_model.encode(
        [query.strip()],
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    similarities = cosine_similarity(
        query_embedding,
        _cached_embeddings,
    )[0]

    ranked_indices = similarities.argsort()[::-1][:top_k]

    results = []

    for index in ranked_indices:
        document = _cached_chunks[index]

        results.append({
            "name": document["name"],
            "chunk_id": document["chunk_id"],
            "content": document["content"],
            "score": float(similarities[index]),
        })

    return results


def print_retrieval_results(query, results):
    """Display retrieved chunks and their similarity scores."""

    print("\n" + "=" * 60)
    print(f"QUERY: {query}")
    print("=" * 60)

    if not results:
        print("No documents retrieved.")
        return

    for result in results:
        print(f"\nDocument: {result['name']}")
        print(f"Chunk: {result['chunk_id']}")
        print(f"Similarity Score: {result['score']:.4f}")

        retrieval_pass = result["score"] >= 0.25
        source_pass = result["score"] >= 0.35

        print(
            f"Retrieval Threshold (0.25): "
            f"{'PASS' if retrieval_pass else 'FAIL'}"
        )

        print(
            f"Source Threshold (0.35): "
            f"{'PASS' if source_pass else 'FAIL'}"
        )

    print("=" * 60)
