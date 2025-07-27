import os
import json
import argparse
import time
from pdf_processor import PDFProcessor

def process_pdfs(input_dir: str, output_dir: str):
    """Process all PDFs in input directory and save results to output directory"""
    processor = PDFProcessor()
    
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Get list of PDF files
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("No PDF files found in input directory")
        return
    
    print(f"Found {len(pdf_files)} PDF file(s) to process")
    
    for filename in pdf_files:
        input_path = os.path.join(input_dir, filename)
        output_filename = f"{os.path.splitext(filename)[0]}.json"
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"Processing {filename}...")
        start_time = time.time()
        
        try:
            result = processor.process_pdf(input_path)
            
            # Save result to JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            processing_time = time.time() - start_time
            print(f"✓ {filename} processed in {processing_time:.2f}s -> {output_filename}")
            
        except Exception as e:
            print(f"✗ Error processing {filename}: {str(e)}")
            # Create empty result on error
            error_result = {
                "title": os.path.splitext(filename)[0],
                "outline": []
            }
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(error_result, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDF Outline Extractor")
    parser.add_argument('--input', default='/app/input', help='Input directory containing PDFs')
    parser.add_argument('--output', default='/app/output', help='Output directory for JSON files')
    
    args = parser.parse_args()
    
    print(f"Input directory: {args.input}")
    print(f"Output directory: {args.output}")
    
    # Validate input directory exists
    if not os.path.exists(args.input):
        print(f"Error: Input directory {args.input} does not exist")
        exit(1)
    
    process_pdfs(args.input, args.output)
    print("Processing complete!")