"""
docker_bot_app.py
A simple web chat page for your Docker-docs Knowledge Base bot.

Works both ways:
  - On your Mac: uses the credentials from `aws configure`.
  - On Streamlit Cloud: uses credentials you paste into the app's Secrets box
    (so no keys ever live in this file or in GitHub).

Run locally with:  streamlit run docker_bot_app.py
"""

import boto3
import streamlit as st

# ----- Settings -----
REGION = "us-east-1"
KNOWLEDGE_BASE_ID = "MAVXSIAQDY"
GEN_MODEL_ID = "amazon.nova-lite-v1:0"
# --------------------


@st.cache_resource
def get_clients():
    """
    Build the AWS clients.

    If AWS keys are provided in Streamlit's Secrets (used when deployed online),
    use them. Otherwise fall back to the local `aws configure` credentials.
    """
    extra = {}
    if "aws" in st.secrets:
        extra = {
            "aws_access_key_id": st.secrets["aws"]["aws_access_key_id"],
            "aws_secret_access_key": st.secrets["aws"]["aws_secret_access_key"],
        }

    agent_runtime = boto3.client("bedrock-agent-runtime", region_name=REGION, **extra)
    bedrock = boto3.client("bedrock-runtime", region_name=REGION, **extra)
    return agent_runtime, bedrock


def retrieve(agent_runtime, question):
    """Step 1: get the most relevant doc pieces from the Knowledge Base."""
    response = agent_runtime.retrieve(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        retrievalQuery={"text": question},
    )
    return response.get("retrievalResults", [])


def generate(bedrock, question, chunks):
    """Step 2: ask a cheap model to answer using only the retrieved pieces."""
    context = "\n\n".join(c["content"]["text"] for c in chunks)
    prompt = (
        "Answer the question using only the Docker documentation below. "
        "If the answer isn't in it, say you don't know.\n\n"
        f"Documentation:\n{context}\n\n"
        f"Question: {question}"
    )
    response = bedrock.converse(
        modelId=GEN_MODEL_ID,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 500, "temperature": 0.2},
    )
    return response["output"]["message"]["content"][0]["text"]


def sources_from(chunks):
    """Pull the S3 file names the pieces came from, for citations."""
    found = set()
    for c in chunks:
        uri = c.get("location", {}).get("s3Location", {}).get("uri")
        if uri:
            found.add(uri)
    return sorted(found)


# ----- The web page -----
st.set_page_config(page_title="Docker Docs Bot", page_icon="🐳")
st.title("🐳 Docker Docs Bot")
st.caption("Ask a question about Docker. Answers come from the official docs, via AWS Bedrock.")

agent_runtime, bedrock = get_clients()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("How do I install Docker?")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching the docs..."):
            try:
                chunks = retrieve(agent_runtime, question)
                if not chunks:
                    answer = "I couldn't find anything relevant in the docs."
                else:
                    answer = generate(bedrock, question, chunks)
                    sources = sources_from(chunks)
                    if sources:
                        answer += "\n\n**Sources:**\n" + "\n".join(
                            f"- {s}" for s in sources
                        )
            except Exception as error:
                answer = f"Something went wrong: {error}"
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})