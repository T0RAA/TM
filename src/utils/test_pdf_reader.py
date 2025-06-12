from pdf_reader import PDFReader
import os
import re

def detect_section_headers(text):
    lines = text.split('\n')
    headers = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Heuristic: all caps, or starts with 'Step', or starts with a number and period, or is long and title-like
        if (
            (stripped.isupper() and 5 < len(stripped) < 60) or
            re.match(r"^Step \d+:", stripped) or
            re.match(r"^\d+\. ", stripped) or
            (stripped and len(stripped) < 60 and stripped == stripped.title() and not stripped.endswith('.'))
        ):
            headers.append((i, stripped))
    return headers

def main():
    try:
        # Get the PDF path
        pdf_path = os.path.join("docs", "TasteMate.pdf")
        reader = PDFReader(pdf_path)
        
        # First, print the raw text content
        print("\nRaw PDF Content:")
        print("="*50)
        raw_text = reader.read_text()
        print(raw_text[:2000])  # Print only the first 2000 chars for brevity
        print("\n... (truncated) ...\n")
        print("="*50)
        
        print("\nDetecting possible section headers...")
        headers = detect_section_headers(raw_text)
        for idx, header in headers:
            print(f"Line {idx}: {header}")
        print(f"\nTotal detected headers: {len(headers)}")
        
        # Then try to extract sections
        print("\nAttempting to extract sections...")
        section_markers = [h[1] for h in headers]
        sections = reader.extract_sections(section_markers)
        
        if not sections:
            print("\nNo sections found. The PDF might have different section headers.")
            print("Please check the raw content above to identify the correct section markers.")
        else:
            print("\nExtracted Sections:")
            for section_name, content in sections.items():
                print(f"\n{'='*50}")
                print(f"Section: {section_name}")
                print(f"{'='*50}")
                print(content)
                print(f"\n{'-'*50}")
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main() 