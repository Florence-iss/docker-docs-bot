# Start from a slim official Python image
FROM python:3.13-slim

# Set the working directory inside the container
WORKDIR /app

# Install dependencies first so this layer caches unless requirements change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code and the prebuilt vector store
COPY app.py .
COPY chroma_db/ ./chroma_db/

# Streamlit's default port
EXPOSE 8501

# Run the app, bound to all interfaces so it's reachable from outside the container
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]