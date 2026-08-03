import json
from pathlib import Path
import chromadb

chunks = json.loads(Path("chunks.json").read_text(encoding="utf-8"))
print(f"Loaded {len(chunks)} chunks")

# a vector store that saves to disk in ./chroma_db
client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection("docker_docs")

# add in batches so we get progress and stay within limits.
# upsert makes this safe to re-run without duplicating anything.
BATCH = 1000
for start in range(0, len(chunks), BATCH):
    batch = chunks[start:start + BATCH]
    collection.upsert(
        ids=[f"chunk-{start + i}" for i in range(len(batch))],
        documents=[c["text"] for c in batch],
        metadatas=[
            {
                "title": c["title"],
                "source": c["source"],
                "chunk_index": c["chunk_index"],
            }
            for c in batch
        ],
    )
    done = min(start + BATCH, len(chunks))
    print(f"  embedded and stored {done}/{len(chunks)}")

print(f"\nDone. Collection now holds {collection.count()} chunks.")
