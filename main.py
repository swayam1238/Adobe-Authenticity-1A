import fitz  # PyMuPDF
import json
import os
import time
from collections import Counter
import re

def is_gibberish(text):
    """Detects if a line of text is likely a PDF extraction error."""
    words = text.split()
    if len(words) > 5 and sum(1 for w in words if len(w) == 1) / len(words) > 0.4:
        return True
    if len(re.findall(r'(\s\w\s\w\s)', text)) > 3:
        return True
    return False

def find_document_title(doc):
    """Finds the document title using a more robust block-based method."""
    try:
        first_page = doc[0]
        dict_blocks = first_page.get_text("dict")["blocks"]
        
        font_sizes = [s["size"] for b in dict_blocks if "lines" in b for l in b["lines"] for s in l["spans"]]
        if not font_sizes: raise ValueError("No text on page")
        
        largest_font_size = max(font_sizes)
        title_candidates = [s["text"] for b in dict_blocks if "lines" in b for l in b["lines"] for s in l["spans"] if abs(s["size"] - largest_font_size) < 0.1]
        
        potential_title = " ".join(title_candidates).strip()
        
        if potential_title and not is_gibberish(potential_title):
            return re.sub(r'\s+', ' ', potential_title).strip()

    except Exception:
        pass

    if doc.metadata and doc.metadata.get("title"):
        return doc.metadata.get("title")

    return os.path.basename(doc.name).replace('.pdf', '')


def analyze_font_styles(doc):
    """Analyzes document-wide font styles, skipping headers/footers."""
    styles = Counter()
    for page in doc:
        page_height = page.rect.height
        header_zone = page_height * 0.10
        footer_zone = page_height * 0.90
        
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            # *** CORRECTED THIS LINE ***
            # Access bounding box via the 'bbox' key
            bbox = b.get('bbox', None)
            if bbox and "lines" in b and (bbox[1] > header_zone and bbox[3] < footer_zone):
                for l in b["lines"]:
                    for s in l["spans"]:
                        is_bold = (s["flags"] & 2**4) or ("bold" in s["font"].lower())
                        styles[(round(s["size"]), is_bold)] += 1
    if not styles:
        return None, []
        
    body_style = styles.most_common(1)[0][0]
    unique_styles = sorted(styles.keys(), key=lambda x: (x[0], x[1]), reverse=True)
    return body_style, unique_styles


def extract_outline_from_pdf(pdf_path):
    """Extracts a structured outline using a defensive, multi-pass approach."""
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening {pdf_path}: {e}")
        return None

    title = find_document_title(doc)
    outline = []

    toc = doc.get_toc()
    if toc and len(toc) > 3:
        for level, text, page in toc:
            h_level = f"H{min(level, 3)}"
            if not is_gibberish(text):
                outline.append({"level": h_level, "text": text.strip(), "page": page})
        return {"title": title, "outline": outline}
    
    outline = []
    body_style, unique_styles = analyze_font_styles(doc)

    if body_style is None:
        return {"title": title, "outline": []}

    potential_headings = []
    for page_num, page in enumerate(doc):
        if page_num == 0 and len(doc) > 1: continue

        page_height = page.rect.height
        header_zone = page_height * 0.10
        footer_zone = page_height * 0.90

        blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)["blocks"]
        for block in blocks:
            # *** CORRECTED THIS LINE ***
            bbox = block.get('bbox', None)
            if not bbox or (bbox[1] < header_zone or bbox[3] > footer_zone): continue

            if "lines" in block:
                for line in block["lines"]:
                    if line["spans"]:
                        span = line["spans"][0]
                        text = " ".join([s["text"] for s in line["spans"]]).strip()
                        
                        if not text or len(text.split()) > 20 or text.endswith(('.', ':', ',')) or is_gibberish(text) or re.match(r'^\d+$', text):
                            continue

                        font_size = round(span["size"])
                        is_bold = (span["flags"] & 2**4) or ("bold" in span["font"].lower())
                        current_style = (font_size, is_bold)

                        if current_style[0] > body_style[0] or (current_style[1] and not body_style[1]):
                            potential_headings.append({"style": current_style, "text": text, "page": page_num + 1})

    if not potential_headings:
        return {"title": title, "outline": []}

    heading_styles = sorted(list(set([h["style"] for h in potential_headings])), key=lambda x: (x[0], x[1]), reverse=True)
    level_map = {style: f"H{i+1}" for i, style in enumerate(heading_styles[:3])}

    for h in potential_headings:
        if h["style"] in level_map:
            level = level_map[h["style"]]
            if not any(o['text'] == h['text'] for o in outline):
                outline.append({"level": level, "text": h['text'], "page": h['page']})

    return {"title": title, "outline": outline}


def process_all_pdfs(input_dir, output_dir):
    """Processes all PDFs in the input directory and saves JSON outlines."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_dir, filename)
            start_time = time.time()
            
            print(f"Processing '{filename}'...")
            result = extract_outline_from_pdf(pdf_path)
            
            if result:
                output_filename = os.path.splitext(filename)[0] + ".json"
                output_path = os.path.join(output_dir, output_filename)
                
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=4, ensure_ascii=False)
                
                end_time = time.time()
                print(f"Finished '{filename}' in {end_time - start_time:.2f} seconds. Output saved to '{output_path}'.")

if __name__ == "__main__":
    INPUT_DIR = "./input" if os.path.exists("./input") else "input"
    OUTPUT_DIR = "./output" if os.path.exists("./output") else "output"
    
    if not os.path.exists(INPUT_DIR): os.makedirs(INPUT_DIR)
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)

    process_all_pdfs(INPUT_DIR, OUTPUT_DIR)