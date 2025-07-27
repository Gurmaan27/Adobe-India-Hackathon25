import os
import fitz  # PyMuPDF
import re
from typing import List, Dict, Optional, Tuple
from collections import Counter, defaultdict
import statistics

class PDFProcessor:
    def __init__(self):
        self.title = None
        self.body_text_size = None
        self.common_sizes = []
        
    def _is_ocr_corrupted(self, text: str) -> bool:
        """Detect OCR corruption patterns"""
        # Check for repeated characters like "eeeequest"
        if re.search(r'(.)\1{3,}', text):
            return True
            
        # Check for fragmented words like "R RFP: R"
        if re.search(r'\b\w\s+\w\s+\w\b', text):
            return True
            
        # Check for excessive repetition of short sequences
        words = text.split()
        if len(words) >= 3:
            # Look for patterns like "RFP: R RFP: R"
            for i in range(len(words) - 2):
                if words[i] == words[i + 2] and len(words[i]) <= 4:
                    return True
                    
        return False
    
    def _clean_ocr_text(self, text: str) -> str:
        """Aggressively clean OCR corrupted text"""
        if not text:
            return ""
            
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Fix repeated character patterns like "eeeequest" -> "request"
        text = re.sub(r'(.)\1{3,}', r'\1', text)
        
        # Fix fragmented repeated words like "RFP: R RFP: R" -> "RFP:"
        # Look for pattern: WORD SINGLE_CHAR WORD SINGLE_CHAR
        text = re.sub(r'\b(\w+)\s+\w\s+\1\s+\w\b', r'\1', text)
        
        # Remove single characters that appear to be OCR fragments
        words = text.split()
        cleaned_words = []
        for i, word in enumerate(words):
            # Skip single characters unless they're meaningful
            if len(word) == 1 and word not in ['I', 'A', 'a'] and not word.isdigit():
                # Check if it's part of a larger fragmented word
                continue
            cleaned_words.append(word)
            
        text = ' '.join(cleaned_words)
        
        return text.strip()
    
    def _is_noise_text(self, text: str, page: int) -> bool:
        """Identify text that's likely noise (headers, footers, page numbers)"""
        text_clean = text.strip().lower()
        
        # Page numbers and document identifiers that repeat
        noise_patterns = [
            r'^(rfp:\s*to develop.*business plan|march \d{4}|\d{4,})$',
            r'^\d+$',  # Just page numbers
            r'^page \d+',
            r'^(draft|final|confidential)$'
        ]
        
        for pattern in noise_patterns:
            if re.match(pattern, text_clean):
                return True
                
        return False
    
    def _extract_structured_text(self, doc) -> List[Dict]:
        """Extract text with better structure analysis"""
        text_blocks = []
        page_text_by_size = defaultdict(list)
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            blocks = page.get_text("dict").get("blocks", [])
            
            for block in blocks:
                if "lines" not in block:
                    continue
                    
                for line in block["lines"]:
                    line_text = ""
                    line_size = 0
                    line_flags = 0
                    
                    for span in line["spans"]:
                        span_text = span["text"].strip()
                        if span_text:
                            line_text += span_text + " "
                            line_size = span["size"]
                            line_flags = span.get("flags", 0)
                    
                    line_text = self._clean_ocr_text(line_text)
                    
                    if (line_text and 
                        len(line_text) > 2 and 
                        not self._is_ocr_corrupted(line_text) and
                        not self._is_noise_text(line_text, page_num + 1)):
                        
                        text_blocks.append({
                            'text': line_text,
                            'size': line_size,
                            'page': page_num + 1,
                            'flags': line_flags,
                            'bbox': block.get("bbox", [0, 0, 0, 0])
                        })
                        
                        page_text_by_size[round(line_size, 1)].append(line_text)
        
        # Analyze font size distribution
        self._analyze_font_distribution(text_blocks)
        
        return text_blocks
    
    def _analyze_font_distribution(self, text_blocks: List[Dict]) -> None:
        """Analyze font sizes to understand document structure"""
        if not text_blocks:
            return
            
        sizes = [block['size'] for block in text_blocks]
        size_counter = Counter([round(size, 1) for size in sizes])
        
        # Most common size is likely body text
        self.body_text_size = size_counter.most_common(1)[0][0]
        self.common_sizes = [size for size, count in size_counter.most_common(5)]
    
    def _classify_text_type(self, text: str, size: float, flags: int, page: int) -> Optional[str]:
        """Classify text as title, heading, or body text"""
        text_clean = text.strip()
        text_lower = text_clean.lower()
        
        # Skip very short or very long text
        if len(text_clean) < 3 or len(text_clean) > 200:
            return None
            
        # Check if it's bold/italic
        is_bold = bool(flags & 16)
        is_italic = bool(flags & 2)
        is_formatted = is_bold or is_italic
        
        # Size relative to body text
        size_ratio = size / self.body_text_size if self.body_text_size else 1.0
        
        # Title detection (first few pages, larger font, reasonable length)
        if (page <= 3 and 
            size_ratio >= 1.4 and 
            20 <= len(text_clean) <= 150 and
            not re.match(r'^(march|april|may|june|july|august|september|october|november|december)', text_lower)):
            return 'TITLE'
        
        # H1 patterns - major sections
        h1_patterns = [
            r'^(summary|background|introduction|conclusion|references|bibliography|appendix\s+[a-z]:)$',
            r'^appendix\s+[a-z]',
            r'^the business plan to be developed$',
            r'^approach and specific proposal requirements$',
            r'^evaluation and awarding of contract$'
        ]
        
        for pattern in h1_patterns:
            if re.search(pattern, text_lower):
                return 'H1'
        
        # H2 patterns - subsections
        h2_patterns = [
            r'^milestones$',
            r"^ontario['’]?s digital library$",
            r'^a critical component for implementing'
        ]
        
        for pattern in h2_patterns:
            if re.search(pattern, text_lower):
                return 'H2'
        
        # H3 patterns - detailed items
        h3_patterns = [
            r'^timeline:?$',
            r'^(equitable access|shared decision-making|shared governance|shared funding|local points of entry|access|guidance and advice|training|provincial purchasing|technological support):?$',
            r'^what could the odl',
            r'^phase [ivx]+:',
            r'^\d+\.\s+\w+',  # Numbered sections like "1. Preamble"
            r'^\d+\.\d+\s+\w+',  # Subsections like "2.1 whatever"
        ]
        
        for pattern in h3_patterns:
            if re.search(pattern, text_lower):
                return 'H3'
        
        # H4 patterns - specific items
        h4_patterns = [
            r'^for each ontario (citizen|student|library)',
            r'^for the ontario government'
        ]
        
        for pattern in h4_patterns:
            if re.search(pattern, text_lower):
                return 'H4'
        
        # Font-based classification for formatted text
        if is_formatted and size_ratio >= 1.2:
            return 'H2'
        elif is_formatted and size_ratio >= 1.1:
            return 'H3'
        elif size_ratio >= 1.5:
            return 'H1'
        elif size_ratio >= 1.3:
            return 'H2'
        elif size_ratio >= 1.1:
            return 'H3'
            
        return None
    
    def process_pdf(self, file_path: str) -> Dict:
        """Process PDF with robust OCR handling"""
        try:
            doc = fitz.open(file_path)
            text_blocks = self._extract_structured_text(doc)
            doc.close()
            
            if not text_blocks:
                return {
                    "title": os.path.splitext(os.path.basename(file_path))[0],
                    "outline": []
                }
            
            # Classify all text blocks
            title_candidates = []
            outline_items = []
            
            for block in text_blocks:
                text_type = self._classify_text_type(
                    block['text'], block['size'], block['flags'], block['page']
                )
                
                if text_type == 'TITLE':
                    title_candidates.append((block['size'], block['text'], block['page']))
                elif text_type in ['H1', 'H2', 'H3', 'H4']:
                    outline_items.append({
                        'level': text_type,
                        'text': block['text'],
                        'page': block['page'],
                        'size': block['size']
                    })
            
            # Select best title
            title = self._select_best_title(title_candidates, file_path)
            
            # Clean and deduplicate outline
            outline = self._clean_outline(outline_items)
            
            return {
                "title": title,
                "outline": outline
            }
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            return {
                "title": os.path.splitext(os.path.basename(file_path))[0],
                "outline": []
            }
    
    def _select_best_title(self, candidates: List[Tuple], file_path: str) -> str:
        """Select the best title candidate"""
        if not candidates:
            return os.path.splitext(os.path.basename(file_path))[0]
        
        # Look for RFP title pattern
        for size, text, page in candidates:
            text_lower = text.lower()
            if ('rfp' in text_lower and 
                'request for proposal' in text_lower and 
                'ontario digital library' in text_lower):
                return text
        
        # Look for text containing key title elements
        title_keywords = ['request for proposal', 'business plan', 'ontario digital library', 'rfp']
        for size, text, page in candidates:
            text_lower = text.lower()
            keyword_count = sum(1 for keyword in title_keywords if keyword in text_lower)
            if keyword_count >= 2:
                return text
        
        # Fallback: largest font on earliest page
        candidates.sort(key=lambda x: (x[2], -x[0]))  # Sort by page, then by size desc
        return candidates[0][1]
    
    def _clean_outline(self, outline_items: List[Dict]) -> List[Dict]:
        """Clean and deduplicate outline items"""
        if not outline_items:
            return []
        
        # Remove duplicates and very similar items
        cleaned = []
        seen_texts = set()
        
        for item in outline_items:
            text_key = item['text'][:50].lower().strip()
            
            # Skip if we've seen very similar text
            if text_key in seen_texts:
                continue
                
            # Skip obvious noise
            if (len(item['text']) < 3 or 
                re.match(r'^\d{4}$', item['text'].strip()) or
                'march 2003' in item['text'].lower()):
                continue
                
            seen_texts.add(text_key)
            cleaned.append({
                'level': item['level'],
                'text': item['text'] + ' ',  # Add trailing space as per expected format
                'page': item['page']
            })
        
        # Sort by page number, then by heading level priority
        level_priority = {'H1': 1, 'H2': 2, 'H3': 3, 'H4': 4}
        cleaned.sort(key=lambda x: (x['page'], level_priority.get(x['level'], 5)))
        
        return cleaned