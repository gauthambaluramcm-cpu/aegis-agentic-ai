from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

CHROMA_DIR = BASE_DIR / "data" / "chroma_db"


# ============================================================
# LOAD EMBEDDING MODEL
# ============================================================

print("Loading embedding model...")

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

print("✓ Embedding model loaded")


# ============================================================
# LOAD CHROMA DATABASE
# ============================================================

print("\nLoading Chroma database...")

vectorstore = Chroma(
    persist_directory=str(CHROMA_DIR),
    collection_name="aegis_knowledge_base",
    embedding_function=embeddings
)

print("✓ Chroma database loaded")


# ============================================================
# RAG RETRIEVAL FUNCTION
# ============================================================

def retrieve_relevant_context(query, k=5):
    """
    Retrieve relevant documents from the AEGIS knowledge base.

    Parameters:
        query: Text describing the security situation.
        k: Number of documents to retrieve.

    Returns:
        List of retrieved document information.
    """

    results = vectorstore.similarity_search_with_score(
        query,
        k=k
    )

    retrieved_context = []

    for document, score in results:

        retrieved_context.append({
            "source": document.metadata.get("source_file"),
            "document_type": document.metadata.get("document_type"),
            "page": document.metadata.get("page", "N/A"),
            "score": score,
            "content": document.page_content
        })

    return retrieved_context


# ============================================================
# TEST RETRIEVAL
# ============================================================

if __name__ == "__main__":

    query = """
    A user accessed a large amount of sensitive data using
    an unusual device. The access may be unauthorized.
    What security and access control policies are relevant?
    """

    print("\n" + "=" * 60)
    print("AEGIS RAG RETRIEVAL TEST")
    print("=" * 60)

    print("\nQuery:")
    print(query)

    results = retrieve_relevant_context(
        query,
        k=5
    )

    print("\n" + "=" * 60)
    print("RETRIEVED DOCUMENTS")
    print("=" * 60)

    for i, result in enumerate(results, start=1):

        print(f"\n--- Result {i} ---")

        print(f"Source       : {result['source']}")
        print(f"Document type: {result['document_type']}")
        print(f"Page         : {result['page']}")
        print(f"Score        : {result['score']:.4f}")

        print("\nContent:")
        print(result["content"][:1000])

    print("\n" + "=" * 60)
    print("RETRIEVAL TEST COMPLETE")
    print("=" * 60)