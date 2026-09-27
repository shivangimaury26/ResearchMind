from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from pypdf import PdfReader
import re
from sentence_transformers import SentenceTransformer
import faiss
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()

    if not data or "question" not in data:
        return jsonify({"error": "Question is required"}), 400

    question = data["question"]

    # Find relevant research paper chunks
    results = search_similar_chunks(question)

    if not results:
        return jsonify({
            "answer": "I could not find relevant information in the uploaded research paper."
        })

    context = "\n\n".join(results)

    prompt = f"""
You are ResearchMind, an AI research paper assistant.

Answer the user's question using ONLY the research paper context provided below.
Do not invent information that is not present in the context.
If the answer cannot be found in the context, clearly say that the information is not available in the provided paper.

Research Paper Context:
{context}

User Question:
{question}

Give a clear and concise answer.
"""

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt
    )

    return jsonify({
        "question": question,
        "answer": response.text,
        "sources": results
    })    
@app.route("/summary", methods=["GET"])
def summary():
        try:
            with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
                chunks = json.load(f)

            if not chunks:
                return jsonify({
                    "error": "No research paper has been uploaded yet."
                }), 400

            context = "\n\n".join(chunks)

            prompt = f"""
You are ResearchMind, an AI research paper assistant.

Create a clear and structured summary of the research paper using ONLY
the research paper context provided below.

Do not invent or add information that is not present in the paper.

Include these sections:
1. Research Topic
2. Objective
3. Methodology
4. Key Findings
5. Conclusion

Keep the language simple, clear and suitable for a student.

Research Paper Context:
{context}
"""

            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt
            )

            return jsonify({
                "summary": response.text
            })

        except Exception as e:
            return jsonify({
                "error": "Unable to generate summary.",
                "details": str(e)
            }), 500

if __name__ == "__main__":
    app.run(debug=True)