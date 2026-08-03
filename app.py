import os
from dotenv import load_dotenv
from anthropic import Anthropic
import chromadb
import streamlit as st

load_dotenv()


# --- cache the clients so they load once, not on every interaction ---
@st.cache_resource
def get_clients():
    claude = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    chroma = chromadb.PersistentClient(path="chroma_db")
    collection = chroma.get_or_create_collection("docker_docs")
    return claude, collection


claude, collection = get_clients()


def retrieve(question, k=5):
    results = collection.query(
        query_texts=[question],
        n_results=k,
        include=["documents", "metadatas"],
    )
    return results["documents"][0], results["metadatas"][0]


def build_context(docs, metas):
    return "\n\n---\n\n".join(
        f"[Source: {m['source']}]\n{d}" for d, m in zip(docs, metas)
    )


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


# --- UI ---
st.set_page_config(page_title="Docker Docs Bot", page_icon="🐳")
st.title("🐳 Docker Docs Bot")
st.caption("Ask anything about Docker. Answers come only from the official docs.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# replay the conversation so far
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("Sources"):
                for s in msg["sources"]:
                    st.write("-", s)

# handle new input
if question := st.chat_input("e.g. How do I limit a container's memory?"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching the docs..."):
            answer, metas = ask(question)
            # unique source list, order preserved
            sources = list(dict.fromkeys(m["source"] for m in metas))
        st.markdown(answer)
        with st.expander("Sources"):
            for s in sources:
                st.write("-", s)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": sources}
    )