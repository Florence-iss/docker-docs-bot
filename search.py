import chromadb

client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection("docker_docs")

print(f"Searching across {collection.count()} chunks.")
print("Ask a Docker question, or type 'quit' to exit.\n")

while True:
    question = input("Question: ").strip()
    if question.lower() in {"quit", "exit", ""}:
        break

    results = collection.query(
        query_texts=[question],
        n_results=5,
        include=["documents", "metadatas", "distances"],
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    print(f"\nTop {len(docs)} matches:\n")
    for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists), 1):
        print(f"{i}. {meta['title']}  ({meta['source']})")
        print(f"   distance: {dist:.3f}  (lower = closer in meaning)")
        print(f"   {doc[:200].strip()}...\n")