
## 📁 Round 1A – PDF Outline Extractor

### 📄 Project Name: `pdf-outline-extractor`

### 🧠 Objective

Extract structured outline information (titles, H1s, H2s, H3s) from a PDF and output it in a well-formatted JSON structure.

---

### 📦 Folder Structure

```
Round1A/
├── main.py
├── Dockerfile
├── README.md
├── requirements.txt
├── input/              # Input PDFs
└── output/             # Output JSON
```

---

### ⚙️ How to Use

#### 🔧 1. Build Docker Image

```bash
docker build --platform linux/amd64 -t pdf-outline-extractor .
```

#### 🚀 2. Run the Container

```bash
docker run --rm -v %cd%\input:/app/input -v %cd%\output:/app/output --network none pdf-outline-extractor
```

---

### 📤 Output Format

Example output (`output/result.json`):

```json
{
  "document_name": "sample.pdf",
  "outline": [
    { "title": "Title of the Document", "type": "title", "page_number": 1 },
    { "title": "Introduction", "type": "H1", "page_number": 1 },
    { "title": "Background", "type": "H2", "page_number": 2 },
    ...
  ]
}
```

---

### ✅ Key Features

* Purely offline
* Extracts logical structure based on font size, spacing, and hierarchy
* Lightweight, fast, and Dockerized

---

## 📁 Round 1B – Persona-Based Document Insight Generator

### 📄 Project Name: `round1b-solution`

### 🧠 Objective

Given a **persona** and a **job-to-be-done**, extract the **most relevant sections** and **refined summaries** from a collection of PDFs.

---

### 📦 Folder Structure

```
Round1B/
├── main.py
├── Dockerfile
├── README.md
├── requirements.txt
├── approach_explanation.md
├── input/              # Input PDFs
└── output/             # Output JSON (result.json)
```

---

### ⚙️ How to Use

#### 🔧 1. Build Docker Image

```bash
docker build --platform linux/amd64 -t round1b-solution .
```

#### 🚀 2. Run the Container (Offline)

```bash
docker run --rm -v %cd%\input:/app/input -v %cd%\output:/app/output --network none round1b-solution
```

---

### 📤 Output Format

Example `result.json`:

```json
{
  "metadata": {
    "input_documents": [...],
    "persona": "Travel Planner",
    "job_to_be_done": "Plan a trip for 10 college friends",
    "processing_timestamp": "2025-07-27T11:20:00Z"
  },
  "extracted_sections": [
    { "document": "Things to Do.pdf", "section_title": "Coastal Adventures", "importance_rank": 1, "page_number": 2 },
    ...
  ],
  "subsection_analysis": [
    { "document": "Things to Do.pdf", "refined_text": "The South of France is renowned...", "page_number": 2 },
    ...
  ]
}
```

---

### ✅ Key Features

* Uses `sentence-transformers` for semantic matching
* Ranks sections across multiple PDFs
* Ensures topic diversity via per-document limits
* Works offline (no internet required at runtime)

