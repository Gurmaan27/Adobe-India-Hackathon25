import os
import json
import fitz  # PyMuPDF
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from collections import defaultdict

INPUT_DIR = "/app/input/PDFs"
OUTPUT_DIR = "/app/output"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # ~80MB

# Inputs – customize or read from input.json
persona = "Travel Planner"
job_to_be_done = "Plan a trip of 4 days for a group of 10 college friends"

model = SentenceTransformer(MODEL_NAME)

def extract_text_sections(pdf_path):
    doc = fitz.open(pdf_path)
    sections = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        if len(text.strip()) > 100:
            sections.append({
                "page_number": page_num,
                "text": text.strip()
            })
    return sections

def clean_title(text):
    lines = text.strip().splitlines()
    for line in lines:
        title = line.strip()
        if title and not title.startswith("•") and len(title) > 5:
            return title[:100]
    return "Untitled Section"

def rank_sections(persona, job, sections):
    query = f"{persona}: {job}"
    query_embedding = model.encode([query])[0]
    scores = []
    for section in sections:
        emb = model.encode([section["text"]])[0]
        score = cosine_similarity([query_embedding], [emb])[0][0]
        scores.append((score, section))
    scores.sort(reverse=True, key=lambda x: x[0])
    return scores

def limit_per_file(sections, max_sections=5, per_file_limit=2):
    counts = defaultdict(int)
    final = []
    for sec in sections:
        if counts[sec["document"]] < per_file_limit:
            final.append(sec)
            counts[sec["document"]] += 1
        if len(final) == max_sections:
            break
    return final

def generate_output(input_files, max_sections=5):
    metadata = {
        "input_documents": input_files,
        "persona": persona,
        "job_to_be_done": job_to_be_done,
        "processing_timestamp": datetime.utcnow().isoformat()
    }

    extracted_sections = []
    subsection_analysis = []
    rank = 1

    all_ranked = []
    for file in input_files:
        path = os.path.join(INPUT_DIR, file)
        sections = extract_text_sections(path)
        ranked = rank_sections(persona, job_to_be_done, sections)
        for score, section in ranked:
            section["document"] = file
            section["score"] = score
            all_ranked.append(section)

    # Sort all by score and enforce diversity across files
    all_ranked.sort(key=lambda x: x["score"], reverse=True)
    top_sections = limit_per_file(all_ranked, max_sections=max_sections, per_file_limit=2)

    for section in top_sections:
        extracted_sections.append({
            "document": section["document"],
            "section_title": clean_title(section["text"]),
            "importance_rank": rank,
            "page_number": section["page_number"]
        })
        subsection_analysis.append({
            "document": section["document"],
            "refined_text": section["text"][:1000],
            "page_number": section["page_number"]
        })
        rank += 1

    return {
        "metadata": metadata,
        "extracted_sections": extracted_sections,
        "subsection_analysis": subsection_analysis
    }

if __name__ == "__main__":
    input_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".pdf")]
    output = generate_output(input_files, max_sections=5)
    with open(os.path.join(OUTPUT_DIR, "result.json"), "w") as f:
        json.dump(output, f, indent=4)
