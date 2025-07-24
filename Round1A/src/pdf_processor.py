import os
import fitz  # PyMuPDF
import re
from typing import List, Dict, Optional, Tuple

class PDFProcessor:
    def __init__(self):
        self.title = None
        self.heading_thresholds = {
            'H1': 18,  # Main headings
            'H2': 14,  # Subheadings
            'H3': 12   # Sub-subheadings
        }
        self.min_heading_length = 4
        self.max_title_length = 80

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text while preserving section numbers"""
        text = re.sub(r'\s+', ' ', text).strip()
        # Preserve numbered headings (e.g., "2.1 Introduction")
        if not re.match(r'^\d+\.\d+', text):
            text = re.sub(r'^[^a-zA-Z0-9]+', '', text)  # Remove leading non-alphanumeric
        return text

    def _merge_heading_fragments(self, spans: List[Tuple]) -> List[Dict]:
        """Merge text fragments that belong together"""
        merged = []
        current = None
        
        for size, text, page in spans:
            text = self._clean_text(text)
            if not text or len(text) > 150:  # Skip very long text
                continue
                
            if current and current['page'] == page and abs(current['size'] - size) < 1:
                # Merge with previous if same page and similar size
                current['text'] = f"{current['text']} {text}"
            else:
                if current:
                    merged.append(current)
                current = {'size': size, 'text': text, 'page': page}
        
        if current:
            merged.append(current)
            
        return merged

    def _determine_heading_level(self, font_size: float) -> Optional[str]:
        """Strict heading level detection"""
        if font_size >= self.heading_thresholds['H1']:
            return 'H1'
        elif font_size >= self.heading_thresholds['H2']:
            return 'H2'
        elif font_size >= self.heading_thresholds['H3']:
            return 'H3'
        return None

    def _is_valid_heading(self, text: str, level: str) -> bool:
        """Validate heading text"""
        if len(text) < self.min_heading_length:
            return False
            
        # Skip common non-heading text
        invalid_phrases = ["version", "page", "figure", "table"]
        if any(phrase in text.lower() for phrase in invalid_phrases):
            return False
            
        # Preserve numbered sections
        if re.match(r'^\d+\.\d+', text):
            return True
            
        return True

    def process_pdf(self, file_path: str) -> Dict:
        """Process PDF with level-wise sorting"""
        doc = fitz.open(file_path)
        outline = []
        title_candidates = []
        all_spans = []
        
        # First pass: collect all text spans
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            blocks = page.get_text("dict").get("blocks", [])
            
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if text:
                                all_spans.append((
                                    span["size"],
                                    text,
                                    page_num + 1  # 1-based page numbers
                                ))
        
        # Merge fragments and filter
        merged_blocks = self._merge_heading_fragments(all_spans)
        
        # Process blocks to identify headings
        for block in (merged_blocks):
            size, text, page = block['size'], block['text'], block['page']
            level = self._determine_heading_level(size)
            
            # Title candidates (first 3 pages only)
            if page <= 3 and len(text) <= self.max_title_length:
                title_candidates.append((size, text, page))
                
            # Heading detection
            if level and self._is_valid_heading(text, level):
                outline.append({
                    "level": level,
                    "text": text,
                    "page": page
                })
        
        # Select the best title
        self.title = self._select_title(title_candidates, file_path)
        
        # Final cleaning and organization (sorted by level)
        outline = self._clean_and_sort_outline(outline)
        
        return {
            "title": self._clean_text(self.title),
            "outline": outline
        }
    
    def _select_title(self, candidates: List[Tuple], file_path: str) -> str:
        """Select title matching required format"""
        if not candidates:
            base = os.path.basename(file_path)
            return os.path.splitext(base)[0]
            
        # Sort by: font size (desc), text length (asc), page number (asc)
        candidates.sort(key=lambda x: (-x[0], len(x[1]), x[2]))
        
        # Prefer text that looks like a title
        for size, text, page in candidates:
            if (size >= self.heading_thresholds['H1'] and
                3 <= len(text.split()) <= 8):
                return text
                
        return candidates[0][1]
    
    def _clean_and_sort_outline(self, outline: List[Dict]) -> List[Dict]:
        """Clean and sort outline by heading level (H1 > H2 > H3)"""
        cleaned = []
        seen = set()
        
        # First pass: clean and remove duplicates
        for item in outline:
            identifier = f"{item['level']}-{item['text'][:30].lower()}"
            if identifier not in seen:
                seen.add(identifier)
                item['text'] = self._clean_text(item['text'])
                cleaned.append(item)
        
        # Sort by heading level (H1 first, then H2, then H3)
        # For same level, sort by page number
        cleaned.sort(key=lambda x: (
            ['H1', 'H2', 'H3'].index(x['level']),
            x['page']
        ))
        
        return cleaned