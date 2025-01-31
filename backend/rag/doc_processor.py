from typing import List, BinaryIO
import PyPDF2
import tiktoken
from io import BytesIO

class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def split_text(self, text: str) -> List[str]:
        """Spliting text into chunks based on token count"""
        chunks = []
        tokens = self.tokenizer.encode(text)
        for i in range(0, len(tokens), self.chunk_size - self.chunk_overlap):
            chunk = tokens[i:i+self.chunk_size]
            chunks.append(self.tokenizer.decode(chunk))
        return chunks
    
    def read_pdf(self, file: BinaryIO) -> str:
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise ValueError(f"Error reading PDF file: {str(e)}")
    
    def read_text(self, file: BinaryIO) -> str:
        try:
            if isinstance(file.read(), bytes):
                file.seek(0)
                return file.read().decode('utf-8')
            file.seek(0)
            return file.read()
        except UnicodeDecodeError:
            raise ValueError("Could not decode text file with UTF-8 encoding")

    def process_files(self, file: BinaryIO):
        try:
            if not hasattr(file, 'name'):
                raise ValueError("File object must have a name attribute")

            if file.name.endswith('.pdf'):
                text = self.read_pdf(file)
            elif file.name.endswith('.txt'):
                text = self.read_text(file)
            else:
                raise ValueError("File format not supported")
            
            chunks = self.split_text(text)
            doc_chunks = []
            
            for i, chunk in enumerate(chunks):
                doc_chunks.append({
                    "title": f"{file.name} - Chunk {i+1}",
                    "content": chunk,
                    "summary": f"Chunk {i+1} of document {file.name}"
                })
            print("Processed file:", len(doc_chunks))
            return doc_chunks
        except Exception as e:
            raise ValueError(f"Error processing file {file.name}: {str(e)}")