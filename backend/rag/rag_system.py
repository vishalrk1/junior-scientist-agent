import os 
import json
import tempfile
from typing import List, Dict, Optional
import logging
from openai import OpenAI

from rag.IVFPQVectorDB import IVFPQVectorDB
from rag.doc_processor import DocumentProcessor

class RagSystem:
    def __init__(self, api_key=None, session_id=None):
        self.client = OpenAI(api_key=api_key)
        self.session_id = session_id
        self.doc_processor = DocumentProcessor(chunk_size=500, chunk_overlap=50)
        self.vector_db = IVFPQVectorDB(
            api_key=api_key, 
            db_path=f'data/rag_sessions/{session_id}/vector_db.pkl'
        )
        self.memory = []
        self.chunks = []
        self.max_context_length = 4000
        self.temperature = 0.7
    
    def get_embeddings(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    
    def process_files(self, files: List) -> int:
        for file in files:
            chunks = self.doc_processor.process_files(file)
            self.chunks.extend(chunks)
        self._load_vector_store()
        return len(self.chunks)

    def process_one_file(self, file):
        print(">>> Processing file")
        chunks = self.doc_processor.process_files(file)
        self.chunks.extend(chunks)
        return chunks
    
    def _load_vector_store(self):
        os.makedirs(f'data/rag_sessions/{self.session_id}', exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                json.dump(self.chunks, f)
                temp_path = f.name
                
        self.vector_db.load_data(temp_path)
        self.vector_db.save_db()
        os.unlink(temp_path)
    
    def _format_context(self, relevant_docs: List[Dict]) -> str:
        context = "\n\nRelevant Information:\n"
        for i, doc in enumerate(relevant_docs, 1):
            context += f"\nDocument {i}:\n{doc['metadata']['content']}\n"
        return context

    def _get_system_prompt(self) -> str:
        return """You are a helpful AI assistant. Your task is to:
        1. Answer questions based on the provided context, strictly dont use information out of this documents
        2. If the answer cannot be found in the context, say so
        3. Provide clear and concise answers
        5. Cite specific documents when possible"""

    def chat(self, question: str, temperature: Optional[float] = None) -> Dict:
        try:
            relevant_docs = self.vector_db.search(question, k=4, similarity_threshold=0.4)
            if not relevant_docs:
                return {
                    "answer": "I couldn't find any relevant information to answer your question.",
                    "sources": []
                }

            context = self._format_context(relevant_docs)
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "system", "content": context},
                {"role": "user", "content": question}
            ]

            if self.memory:
                last_exchanges = self.memory[-2:]  # Last 1 Q&A pairs
                messages[1:1] = last_exchanges

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=2000
            )

            answer = response.choices[0].message.content

            # Update memory
            self.memory.extend([
                {"role": "user", "content": question},
                {"role": "assistant", "content": answer}
            ])

            return {
                "answer": answer,
                "sources": [doc['metadata']["title"] for doc in relevant_docs]
            }

        except Exception as e:
            logging.error(f"Error in chat: {str(e)}")
            raise RuntimeError(f"Failed to generate response: {str(e)}")

    def clear_memory(self):
        self.memory = []

    def set_temperature(self, temperature: float):
        if 0 <= temperature <= 1:
            self.temperature = temperature
        else:
            raise ValueError("Temperature must be between 0 and 1")

    def get_chat_history(self) -> List[Dict]:
        return self.memory