import os
from langchain_chroma import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_core.tools import tool
from langchain_text_splitters import MarkdownHeaderTextSplitter


CHROMA_PATH = "data/chroma_db"
KNOWLEDGE_BASE_PATH = "knowledge_base"
COLLECTION_NAME = "style_guide"


def build_vector_store() -> Chroma:

    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    if os.path.exists(CHROMA_PATH):
        print("  [RAG] Loading existing ChromaDB...")
        return Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=CHROMA_PATH
        )

    print("  [RAG] Building ChromaDB from knowledge base...")

    headers_to_split = [("#", "Header1"), ("##", "Header2"), ("###", "Header3")]
    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split)

    all_docs = []
    for filename in os.listdir(KNOWLEDGE_BASE_PATH):
        if filename.endswith(".md"):
            filepath = os.path.join(KNOWLEDGE_BASE_PATH, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            docs = splitter.split_text(content)
            for doc in docs:
                doc.metadata["source"] = filename
            all_docs.extend(docs)
            print(f"  [RAG] Loaded {len(docs)} chunks from {filename}")

    vector_store = Chroma.from_documents(
        documents=all_docs,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_PATH
    )
    print(f"  [RAG] ChromaDB built: {len(all_docs)} total chunks")
    return vector_store

vector_store = build_vector_store()

@tool
def query_style_guide(query: str) -> str:
    try:
        results = vector_store.similarity_search(query, k=3)

        if not results:
            return "No relevant style guide found for this query."

        formatted = []
        for i, doc in enumerate(results, 1):
            source = doc.metadata.get("source", "unknown")
            header = doc.metadata.get("Header2", doc.metadata.get("Header1", ""))
            formatted.append(f"[{i}] From '{source}' — {header}:\n{doc.page_content}")

        return "\n\n".join(formatted)

    except Exception as e:
        return f"Style guide query error: {str(e)}"