from pdf_reader import PDFReader
import os
import re
import time

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

def build_table_of_contents(headers):
    toc = []
    for idx, header in headers:
        toc.append(f"{idx}: {header}")
    return toc

def main():
    try:
        pdf_path = os.path.join("docs", "TasteMate.pdf")
        reader = PDFReader(pdf_path)
        print("Reading PDF...")
        start_time = time.time()
        raw_text = reader.read_text()
        print(f"PDF read in {time.time() - start_time:.2f} seconds.")
        headers = detect_section_headers(raw_text)
        toc = build_table_of_contents(headers)
        print("\nTable of Contents:")
        print("="*50)
        for entry in toc:
            print(entry)
        print("="*50)
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main() 