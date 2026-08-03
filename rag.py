import os
from dotenv import load_dotenv
from anthropic import Anthropic
import chromadb

load_dotenv()

claude = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
chroma = chromadb.PersistentClient(path="chroma_db")
collection = chroma.get_or_create_collection("docker_docs")


def retrieve(question, k=5):
    results = collection.query(
        query_texts=[question],
        n_results=k,
        include=["documents", "metadatas"],
    )
    return results["documents"][0], results["metadatas"][0]


def build_context(docs, metas):
    blocks = []
    for doc, meta in zip(docs, metas):
        blocks.append(f"[Source: {meta['source']}]\n{doc}")
    return "\n\n---\n\n".join(blocks)


def ask(question):
    docs, metas = retrieve(question)
    context = build_context(docs, metas)

    system = (
        "You answer questions about Docker using ONLY the provided "
        "documentation excerpts. If the answer isn't in the excerpts, say you "
        "don't have enough information rather than guessing. Cite the source "
        "file(s) you drew from."
    )

    user_message = f"Documentation excerpts:\n\n{context}\n\nQuestion: {question}"

    response = claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text, metas


print("Docker Docs Bot ready. Ask a question, or type 'quit' to exit.\n")
while True:
    question = input("Question: ").strip()
    if question.lower() in {"quit", "exit", ""}:
        break

    answer, metas = ask(question)
    print("\n" + "=" * 60)
    print(answer)
    print("=" * 60)
    print("Sources consulted:")
    seen = set()
    for meta in metas:
        if meta["source"] not in seen:
            print(" -", meta["source"])
            seen.add(meta["source"])
    print()