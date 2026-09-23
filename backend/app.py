from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from pypdf import PdfReader
import re
from sentence_transformers import SentenceTransformer
import faiss
import json

app = Flask(__name__)
CORS(app)
model = SentenceTransformer("all-MiniLM-L6-v2")
INDEX_PATH = "vector_store/researchmind.index"
CHUNKS_PATH = "vector_store/chunks.json"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
def chunk_text(text, chunk_size=1000, overlap=200):
    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks

def search_similar_chunks(query, top_k=3):
    index = faiss.read_index(INDEX_PATH)

    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    query_embedding = model.encode([query])

    distances, indices = index.search(query_embedding, top_k)

    results = []

    for i in indices[0]:
        if i < len(chunks):
            results.append(chunks[i])

    return results    

@app.route("/")
def home():
    return "ResearchMind Backend is Running!"


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(file_path)

    # Extract text from PDF
    reader = PdfReader(file_path)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    text = clean_text(text) 
    chunks = chunk_text(text)    

    embeddings = model.encode(chunks)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    faiss.write_index(index, "vector_store/researchmind.index")

    with open("vector_store/chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    return jsonify({
        "message": "PDF uploaded and text extracted successfully",
        "filename": file.filename,
        "text": text,
        "chunks": chunks,
        "embeddings": embeddings.tolist(),
        "faiss_vectors": index.ntotal
    })
@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()

    if not data or "query" not in data:
        return jsonify({"error": "Query is required"}), 400

    query = data["query"]

    results = search_similar_chunks(query)

    return jsonify({
        "query": query,
        "results": results
    })    

if __name__ == "__main__":
    app.run(debug=True)