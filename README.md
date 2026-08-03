# Docker Docs Bot

A retrieval-augmented generation (RAG) chatbot that answers questions about
Docker using the official Docker documentation as its source of truth.

Docker docs are chunked, embedded, and stored in a local vector database
(ChromaDB). At query time, the most relevant chunks are retrieved and passed
to Claude as context, so answers are grounded in the actual docs instead of
the model's general knowledge.

## How it works

1. **`load_docs.py` / `inspect_docs.py`** — sanity-check the raw markdown docs.
2. **`chunk_docs.py`** — splits each doc into ~1000-character chunks (with
   overlap) and writes them to `chunks.json`.
3. **`build_vectorstore.py`** — embeds each chunk and upserts it into a
   persistent ChromaDB collection (`chroma_db/`).
4. **`search.py`** — a simple CLI to inspect raw vector search results
   (no LLM call), useful for debugging retrieval quality.
5. **`rag.py`** — the actual chatbot: retrieves relevant chunks for a
   question and asks Claude to answer using only that context, citing sources.

## Setup

1. Clone the Docker docs content into `data/docs` (this project expects
   markdown pages under `data/docs/content`):

   ```bash
   git clone https://github.com/docker/docker.github.io data/docs
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install anthropic chromadb langchain-text-splitters python-dotenv
   ```

3. Add your Anthropic API key to a `.env` file in the project root:

   ```
   ANTHROPIC_API_KEY=your-key-here
   ```

## Usage

Build the chunk file and vector store (run once, or again after docs update):

```bash
python chunk_docs.py
python build_vectorstore.py
```

Ask questions:

```bash
python rag.py
```

Or inspect raw retrieval without an LLM call:

```bash
python search.py
```

## Notes

- The vector store (`chroma_db/`), chunk cache (`chunks.json`), and cloned
  docs (`data/`) are gitignored since they're large and reproducible from
  the steps above.
- `build_vectorstore.py` uses `upsert`, so it's safe to re-run without
  duplicating chunks.
