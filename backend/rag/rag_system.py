import os 
import re
import json
import tempfile
import logging
from io import BytesIO
from openai import OpenAI
from typing import List, Dict, Optional

from rag.IVFPQVectorDB import IVFPQVectorDB
from rag.doc_processor import DocumentProcessor

class RagSystem:
    def __init__(self, api_key=None, session_id=None):
        self.client = OpenAI(api_key=api_key)
        self.session_id = session_id
        self.doc_processor = DocumentProcessor(chunk_size=1000, chunk_overlap=100)
        self.vector_db = IVFPQVectorDB(
            api_key=api_key, 
            db_path=f'data/rag_sessions/{session_id}/vector_db.pkl'
        )
        self.memory = []
        self.chunks = []
        self.temperature = 0.7
    
    def get_embeddings(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    
    async def process_files(self, files: List) -> int:
        chunks = []
        for file in files:
            content = await file.read()
            file_obj = BytesIO(content)
            file_obj.name = file.filename
            file_chunks = self.doc_processor.process_files(file_obj)
            chunks.extend(file_chunks)
            await file.seek(0)
        self.chunks.extend(chunks)
        self._load_vector_store()
        return len(chunks)
    
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
        5. Do not Cite specific documents in your response
        6. If Information is not available, say so and tell user you cant answer this question"""

    def _update_query(self, question: str) -> str:
        prompt = """
        You are an advanced AI assistant specialized in query processing and contextual understanding. Process each query through these steps:
        ## Query Analysis and Enhancement
        ### Analysis Steps:
        1. SCAN CONVERSATION HISTORY
        - Previous questions and their topics
        - Established context and key information
        - Ongoing discussion themes

        2. IDENTIFY CONTEXTUAL ELEMENTS
        - Pronouns (it, they, this, that)
        - Implicit references to previous topics
        - Time-based references
        - Location mentions
        - Subject continuity markers

        3. QUERY RECONSTRUCTION
        - Replace pronouns with specific references
        - Add missing context from previous exchanges
        - Keep critical keywords intact
        - Maintain technical precision
        - Create concise, self-contained question
        
        Finally respond with update query only in following format:
        `<query>{updated query}</query>`
        """
        
        if self.memory:
            last_exchanges = self.memory[-2:]
            prompt += f"\n\nLast Exchanges:\n{last_exchanges[0]['content']}\n{last_exchanges[1]['content']}"
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": question}
        ]
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.2,
            max_tokens=300
        )
        
        match = re.search(r'<query>(.*?)</query>', response.choices[0].message.content.strip())
        if match:
            return match.group(1)
        return question
    
    def chat(self, question: str, temperature: Optional[float] = None) -> Dict:
        try:
            updated_question = self._update_query(question)
            relevant_docs = self.vector_db.search(updated_question, k=4, similarity_threshold=0.3)
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
                last_exchanges = self.memory[-2:]
                messages[1:1] = last_exchanges

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=2000
            )

            answer = response.choices[0].message.content
            self.memory.extend([
                {"role": "user", "content": question},
                {"role": "assistant", "content": answer}
            ])
            return {
                "answer": answer,
                "sources": [{
                    "title": doc['metadata']["title"],
                    "similarity": doc['similarity']
                } for doc in relevant_docs]
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