import pdfplumber
from typing import Dict, List, Optional
import os

class PDFReader:
    """Utility class for reading and parsing PDF files."""
    
    def __init__(self, pdf_path: str):
        """Initialize PDF reader with path to PDF file."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at: {pdf_path}")
        self.pdf_path = pdf_path
    
    def read_text(self) -> str:
        """Read all text from the PDF file."""
        text = ""
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    
    def read_tables(self) -> List[List[List[str]]]:
        """Extract tables from the PDF file."""
        tables = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                page_tables = page.extract_tables()
                if page_tables:
                    tables.extend(page_tables)
        return tables
    
    def get_metadata(self) -> Dict[str, str]:
        """Get PDF metadata."""
        with pdfplumber.open(self.pdf_path) as pdf:
            return pdf.metadata
    
    def extract_sections(self, section_markers: List[str]) -> Dict[str, str]:
        """Extract specific sections from the PDF based on markers."""
        text = self.read_text()
        sections = {}
        
        for i in range(len(section_markers)):
            start_marker = section_markers[i]
            end_marker = section_markers[i + 1] if i + 1 < len(section_markers) else None
            
            start_idx = text.find(start_marker)
            if start_idx == -1:
                continue
                
            if end_marker:
                end_idx = text.find(end_marker, start_idx)
                if end_idx == -1:
                    end_idx = len(text)
            else:
                end_idx = len(text)
                
            section_content = text[start_idx:end_idx].strip()
            sections[start_marker] = section_content
            
        return sections

def read_tastemate_pdf() -> Dict[str, str]:
    """Read and parse the TasteMate PDF document."""
    pdf_path = os.path.join("docs", "TasteMate.pdf")
    reader = PDFReader(pdf_path)
    
    # Define section markers based on the PDF structure
    section_markers = [
        "System Architecture",
        "Feature Requirements",
        "Implementation Guidelines",
        "Design Patterns",
        "Machine Learning Components",
        "Data Models",
        "API Endpoints"
    ]
    
    return reader.extract_sections(section_markers) 