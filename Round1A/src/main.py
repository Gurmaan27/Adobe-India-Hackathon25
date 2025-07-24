import os
import json
import argparse
from pdf_processor import PDFProcessor

def process_pdfs(input_dir: str, output_dir: str):
    processor = PDFProcessor()
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.pdf'):
            input_path = os.path.join(input_dir, filename)
            output_filename = f"{os.path.splitext(filename)[0]}.json"
            output_path = os.path.join(output_dir, output_filename)
            
            print(f"Processing {filename}...")
            result = processor.process_pdf(input_path)
            
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Results saved to {output_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDF Outline Extractor")
    parser.add_argument('--input', default='/app/input', help='Input directory containing PDFs')
    parser.add_argument('--output', default='/app/output', help='Output directory for JSON files')
    
    args = parser.parse_args()
    process_pdfs(args.input, args.output)