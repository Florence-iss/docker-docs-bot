import json
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter

CONTENT_DIR = Path("data/docs/content")


def split_front_matter(text):
    """Separate the --- YAML header --- from the actual body."""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[1], parts[2].strip()
    return "", text


def get_title(front_matter):
    """Pull the title: line out of the front matter, if present."""
    for line in front_matter.splitlines():
        if line.strip().startswith("title:"):
            return line.split("title:", 1)[1].strip().strip('"').strip("'")
    return "Untitled"


splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""],
)

all_chunks = []
md_files = list(CONTENT_DIR.rglob("*.md"))

for path in md_files:
    text = path.read_text(encoding="utf-8")
    front, body = split_front_matter(text)
    if not body.strip():
        continue  # skip docs with no real content

    title = get_title(front)
    source = str(path.relative_to(CONTENT_DIR))

    for i, chunk in enumerate(splitter.split_text(body)):
        all_chunks.append({
            "text": chunk,
            "title": title,
            "source": source,
            "chunk_index": i,
        })

print(f"Processed {len(md_files)} files into {len(all_chunks)} chunks")

Path("chunks.json").write_text(json.dumps(all_chunks, indent=2), encoding="utf-8")
print("Saved chunks to chunks.json")

# peek at one chunk from the middle
example = all_chunks[len(all_chunks) // 2]
print("\nExample chunk")
print("Title:", example["title"])
print("Source:", example["source"])
print("-" * 60)
print(example["text"][:500])
