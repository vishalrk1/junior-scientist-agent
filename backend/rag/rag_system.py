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

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

class QueryType(Enum):
    CONTEXT = "context"
    DETAIL = "detail"
    VERIFICATION = "verification"

@dataclass
class SubQuery:
    text: str
    query_type: QueryType
    importance: int

class RagSystem:
    def __init__(self, api_key=None, session_id=None):
        self.client = OpenAI(api_key=api_key)
        self.session_id = session_id
        self.doc_processor = DocumentProcessor(chunk_size=500, chunk_overlap=100)
        self.vector_db = IVFPQVectorDB(
            api_key=api_key, 
            db_path=f'data/rag_sessions/{session_id}/vector_db.pkl'
        )
        self.memory = []
        self.chunks = []
        self.temperature = 0.7
        self.logger = logging.getLogger(__name__)
    
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
    
    def _get_relevant_questions(self, question: str) -> List[SubQuery]:
        prompt = """
        You are an expert at breaking down complex questions for RAG systems. Generate comprehensive subqueries that will help gather all necessary information from the document collection.

        For the given question, generate at least 3 types of subqueries:
        1. CONTEXT: Broader background information needed to understand the topic
        2. DETAIL: Specific facts, figures, or data points
        3. VERIFICATION: Cross-reference information or verify claims

        Requirements:
        - Each subquery must be focused and specific
        - Subqueries should cover different aspects of the question
        - Include importance level (5=highest, 1=lowest)
        - Ensure subqueries are actually answerable from documents

        Format your response exactly as:
        <subqueries>
        type: [context/detail/verification]
        importance: [1-5]
        query: [your subquery here]
        ---
        [repeat for each subquery]
        </subqueries>
        """
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Question: {question}"}
        ]

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.2,
                max_tokens=500
            )
            
            return self._parse_subqueries(response.choices[0].message.content.strip())
            
        except Exception as e:
            self.logger.error(f"Error generating subqueries: {str(e)}")
            return [SubQuery(text=question, query_type=QueryType.DETAIL, importance=5)]

    def _parse_subqueries(self, content: str) -> List[SubQuery]:
        subqueries = []
        
        match = re.search(r'<subqueries>(.*?)</subqueries>', content, re.DOTALL)
        if not match:
            return []
            
        blocks = match.group(1).split('---')
        
        for block in blocks:
            if not block.strip():
                continue
                
            try:
                type_match = re.search(r'type:\s*(context|detail|verification)', block, re.IGNORECASE)
                importance_match = re.search(r'importance:\s*([1-5])', block)
                query_match = re.search(r'query:\s*(.+?)(?=\n|$)', block, re.DOTALL)
                
                if all([type_match, importance_match, query_match]):
                    subqueries.append(SubQuery(
                        text=query_match.group(1).strip(),
                        query_type=QueryType[type_match.group(1).upper()],
                        importance=int(importance_match.group(1))
                    ))
            except Exception as e:
                self.logger.error(f"Error parsing subquery block: {str(e)}")
                continue
                
        return subqueries if subqueries else []

    def chat(self, question: str, temperature: Optional[float] = None) -> Dict:
        try:
            updated_question = self._update_query(question)
            subqueries = self._get_relevant_questions(updated_question)
            
            subqueries.sort(key=lambda x: x.importance, reverse=True)
            
            self.logger.info("Generated subqueries:")
            all_relevant_docs = []
            query_results = {}
            
            for sq in subqueries:
                self.logger.info(f"Processing {sq.query_type.value} query: {sq.text}")
                docs = self.vector_db.search(sq.text, k=2, similarity_threshold=0.3)
                if docs:
                    query_results[sq.text] = docs
                    all_relevant_docs.extend(docs)

            if not all_relevant_docs:
                return {
                    "answer": "I couldn't find any relevant information to answer your question.",
                    "sources": []
                }
            
            seen_contents = set()
            unique_docs = []
            for doc in all_relevant_docs:
                content = doc['metadata']['content']
                if content not in seen_contents:
                    seen_contents.add(content)
                    unique_docs.append(doc)

            context = self._format_context(unique_docs)
            
            # Include subquery results in system message
            system_message = self._get_system_prompt() + "\n\nQuery Analysis:\n"
            for sq in subqueries:
                system_message += f"\n{sq.query_type.value.title()} Query: {sq.text}"

            messages = [
                {"role": "system", "content": system_message},
                {"role": "system", "content": context},
                {"role": "user", "content": question}
            ]

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
                } for doc in unique_docs]
            }

        except Exception as e:
            self.logger.error(f"Error in chat: {str(e)}")
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