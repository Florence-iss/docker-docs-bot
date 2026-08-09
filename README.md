# Docker Docs Bot

A retrieval-augmented generation (RAG) chatbot that answers questions about
Docker using the official Docker documentation as its source of truth.

Docker docs are chunked, embedded, and stored in a local vector database
(ChromaDB). At query time, the most relevant chunks are retrieved and passed
to Claude as context, so answers are grounded in the actual docs instead of
the model's general knowledge.
<img width="642" height="328" alt="image" src="https://github.com/user-attachments/assets/7432ef47-b0b5-497b-810c-5484c0397271" />

## How it works

1. **`load_docs.py` / `inspect_docs.py`** — sanity-check the raw markdown docs.
2. **`chunk_docs.py`** — splits each doc into ~1000-character chunks (with
   overlap) and writes them to `chunks.json`.
3. **`build_vectorstore.py`** — embeds each chunk and upserts it into a
   persistent ChromaDB collection (`chroma_db/`).
4. **`search.py`** — a simple CLI to inspect raw vector search results
   (no LLM call), useful for debugging retrieval quality.
5. **`rag.py`** — the chatbot as a CLI: retrieves relevant chunks for a
   question and asks Claude to answer using only that context, citing sources.
6. **`app.py`** — the same chatbot as a Streamlit web UI, with chat history
   and an expandable sources list per answer.

There's also an alternate implementation that uses an AWS Bedrock Knowledge
Base instead of the local ChromaDB/Claude pipeline above:

7. **`ask_docker_bot.py`** — CLI version: retrieves from a Bedrock Knowledge
   Base and generates an answer with a Bedrock model (Amazon Nova Lite).
8. **`docker_bot_app.py`** — the same Bedrock-backed bot as a Streamlit web
   UI. Uses local AWS credentials (`aws configure`) when run on your machine,
   or credentials from Streamlit Secrets when deployed to Streamlit Cloud.

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
   pip install -r requirements.txt
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

Ask questions from the CLI:

```bash
python rag.py
```

Or launch the Streamlit web UI:

```bash
streamlit run app.py
```

Or inspect raw retrieval without an LLM call:

```bash
python search.py
```

### Bedrock version

`ask_docker_bot.py` and `docker_bot_app.py` don't use `chroma_db/` — they
query an AWS Bedrock Knowledge Base instead (set `KNOWLEDGE_BASE_ID` in each
file), and need AWS credentials (`aws configure` locally, or Streamlit
Secrets when deployed) rather than `ANTHROPIC_API_KEY`.

```bash
python ask_docker_bot.py       # CLI
streamlit run docker_bot_app.py  # web UI
```

## Running with Docker

The Dockerfile packages the Streamlit UI along with a prebuilt vector store,
so run `chunk_docs.py` and `build_vectorstore.py` locally first (see
Usage above) to generate `chroma_db/` before building the image.

Build the image:

```bash
docker build -t docker-docs-bot .
```

Run it, passing your API key and mapping the Streamlit port:

```bash
docker run -p 8501:8501 -e ANTHROPIC_API_KEY=your-key-here docker-docs-bot
```

Then open `http://localhost:8501` in your browser.

## Notes

- The vector store (`chroma_db/`), chunk cache (`chunks.json`), and cloned
  docs (`data/`) are gitignored since they're large and reproducible from
  the steps above.
- `build_vectorstore.py` uses `upsert`, so it's safe to re-run without
  duplicating chunks.
