from pdf_reader import PDFReader
import os
import re

def detect_section_headers(text):
    lines = text.split('\n')
    headers = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if (
            (stripped.isupper() and 5 < len(stripped) < 60) or
            re.match(r"^Step \d+:", stripped) or
            re.match(r"^\d+\. ", stripped) or
            (stripped and len(stripped) < 60 and stripped == stripped.title() and not stripped.endswith('.'))
        ):
            headers.append((i, stripped))
    return headers

def extract_sections(text, headers):
    sections = {}
    for i in range(len(headers)):
        start_idx = headers[i][0]
        end_idx = headers[i + 1][0] if i + 1 < len(headers) else len(text.split('\n'))
        section_content = '\n'.join(text.split('\n')[start_idx:end_idx]).strip()
        sections[headers[i][1]] = section_content
    return sections

def main():
    try:
        pdf_path = os.path.join("docs", "TasteMate.pdf")
        reader = PDFReader(pdf_path)
        raw_text = reader.read_text()
        headers = detect_section_headers(raw_text)
        sections = extract_sections(raw_text, headers)
        print("\nExtracted Sections:")
        print("="*50)
        for section_name, content in sections.items():
            print(f"\nSection: {section_name}")
            print(f"{'='*50}")
            print(content)
            print(f"\n{'-'*50}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main() 