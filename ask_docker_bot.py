"""
ask_docker_bot.py
Ask your Docker-docs Managed Knowledge Base a question from the terminal.

Managed Knowledge Bases don't support the old one-call 'retrieve_and_generate',
so this does RAG in its two natural steps:
  1. RETRIEVE: ask the Knowledge Base for the most relevant doc pieces
  2. GENERATE: hand those pieces + your question to a cheap model to write the answer

Run it with:  python ask_docker_bot.py
"""

import boto3

# ----- Settings you can change -----
REGION = "us-east-1"
KNOWLEDGE_BASE_ID = "MAVXSIAQDY"        # your Knowledge Base ID
GEN_MODEL_ID = "amazon.nova-lite-v1:0"  # cheap model that writes the answer
# -----------------------------------

# One client for talking to the Knowledge Base, one for the model.
agent_runtime = boto3.client("bedrock-agent-runtime", region_name=REGION)
bedrock = boto3.client("bedrock-runtime", region_name=REGION)


def retrieve(question):
    """Step 1: get the most relevant doc pieces from the Knowledge Base."""
    response = agent_runtime.retrieve(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        retrievalQuery={"text": question},
    )
    return response.get("retrievalResults", [])


def generate(question, chunks):
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
    """Pull the S3 file names the pieces came from, so we can show citations."""
    found = set()
    for c in chunks:
        uri = c.get("location", {}).get("s3Location", {}).get("uri")
        if uri:
            found.add(uri)
    return sorted(found)


def main():
    print("Docker docs bot - ask a question (type 'quit' to exit)\n")
    while True:
        question = input("You: ").strip()
        if question.lower() in ("quit", "exit", ""):
            print("Bye!")
            break

        # Step 1: retrieve
        try:
            chunks = retrieve(question)
        except Exception as error:
            print(f"\nRetrieve step failed: {error}\n")
            continue

        if not chunks:
            print("\nBot: I couldn't find anything relevant in the docs.\n")
            continue

        # Step 2: generate (if this fails, we still show the sources so you
        # can see retrieval worked)
        try:
            answer = generate(question, chunks)
            print(f"\nBot: {answer}\n")
        except Exception as error:
            print(f"\nAnswer step failed: {error}")
            print("(But retrieval worked - here are the sources it found.)\n")

        sources = sources_from(chunks)
        if sources:
            print("Sources:")
            for s in sources:
                print(f"  - {s}")
            print()


if __name__ == "__main__":
    main()