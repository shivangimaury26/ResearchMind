from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from pypdf import PdfReader
import re

app = Flask(__name__)
CORS(app)

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

    return jsonify({
        "message": "PDF uploaded and text extracted successfully",
        "filename": file.filename,
        "text": text,
        "chunks": chunks
    })

if __name__ == "__main__":
    app.run(debug=True)