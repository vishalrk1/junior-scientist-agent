import os 
import re
import json
import tempfile
import logging
from io import BytesIO
from openai import OpenAI
from typing import List, Dict, Optional

from rag.similarity_matching import SimilarityMatching
from rag.doc_processor import DocumentProcessor
from models.rag import SettingsConfig, RagSession

from models.rag import SettingsConfig, RagSession

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

class RagSystem:
    def __init__(self, api_key=None, session_id=None, settings: Optional[SettingsConfig] = None):
        self.client = OpenAI(api_key=api_key)
        self.session_id = session_id
        self.doc_processor = DocumentProcessor(chunk_size=500, chunk_overlap=100)
        self.vector_db = SimilarityMatching(
            api_key=api_key, 
            db_path=f'data/rag_sessions/{session_id}/vector_db.pkl'
        )
        self.memory = []
        self.chunks = []
        self.settings = settings or SettingsConfig()
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
        self.vector_db.load_data(self.chunks)
        self.vector_db.save_db()
    
    def _format_context(self, relevant_docs: List[Dict]) -> str:
        context = "\n\nRelevant Information:\n"
        for i, doc in enumerate(relevant_docs, 1):
            context += f"\nDocument {i}:\n{doc['metadata']['content']}\n"
        return context

    def _get_system_prompt(self) -> str:
        return """You are a helpful AI assistant. Your task is to:
        1. Use the provided context as your primary knowledge source
        2. If the complete answer is not in the context but you can provide a partial or related answer based on the available information, do so while being transparent about limitations
        3. Synthesize information from multiple context pieces when relevant
        4. Provide clear, concise, and informative answers
        5. When the context contains relevant information, use it to explain concepts without explicitly citing documents
        6. If the question is completely unrelated to the provided context or there's no relevant information at all, politely indicate that you cannot provide an answer based on the available information
        
        Remember to:
        - Be helpful and informative while staying grounded in the provided context
        - Provide partial answers when possible, clearly indicating what aspects you can and cannot address
        - Use natural, conversational language while maintaining accuracy"""

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
    
    def _get_relevant_questions(self, question: str) -> List[str]:
        prompt = """
        You are an AI specialized in extracting search keywords. Your task is to:
        1. Analyze the question and chat history
        2. Extract 2-3 SHORT, focused search queries
        3. Each query should:
           - Be 3-5 words maximum
           - Contain important keywords from the question
           - Remove stop words and unnecessary context
           - Focus on technical terms and specific entities

        FORMAT YOUR RESPONSE EXACTLY AS:
        <queries>
        query1
        query2
        query3
        </queries>

        Example:
        Question: "What are the environmental impacts of solar panel manufacturing?"
        <queries>
        solar panel manufacturing impact
        solar environmental effects
        panel production pollution
        </queries>
        """
        
        if self.memory:
            context = "\nPrevious exchange:\n"
            context += f"Q: {self.memory[-2]['content']}\n"
            context += f"A: {self.memory[-1]['content']}"
            prompt += context

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Question: {question}"}
        ]

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.2,
                max_tokens=200
            )
            
            queries = self._parse_queries(response.choices[0].message.content.strip())
            queries.append(question)
            return queries
            
        except Exception as e:
            self.logger.error(f"Error generating queries: {str(e)}")
            return [question]

    def _parse_queries(self, content: str) -> List[str]:
        queries = []
        match = re.search(r'<queries>(.*?)</queries>', content, re.DOTALL)
        if match:
            queries = [q.strip() for q in match.group(1).strip().split('\n') if q.strip()]
        return queries if queries else []

    def chat(self, question: str) -> Dict:
        if not self.settings:
            raise RuntimeError("Settings not configured")

        try:
            updated_question = self._update_query(question)
            search_queries = self._get_relevant_questions(updated_question)
            
            self.logger.info("Generated search queries:")
            all_relevant_docs = []
            
            for query in search_queries:
                docs = self.vector_db.search(query, self.settings, k=2)
                if docs:
                    all_relevant_docs.extend(docs)
                self.logger.info(f" >>> query: {query}\t docs: {len(docs)}")

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
            system_message = self._get_system_prompt() + "\n\nQuery Analysis:\n"
            for query in search_queries:
                system_message += f"\nQuery: {query}"

            messages = [
                {"role": "system", "content": system_message},
                {"role": "system", "content": context},
                {"role": "user", "content": question}
            ]

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=self.settings.temperature,
                max_tokens=self.settings.max_token
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

    def get_chat_history(self) -> List[Dict]:
        return self.memory

    def update_settings(self, new_settings: SettingsConfig) -> None:
        """Update system settings and validate the configuration."""
        if not new_settings.validate_weights():
            raise ValueError("Invalid settings: weights must sum to 1.0")
        
        self.settings = new_settings
        self.logger.info("Settings updated successfully")
        
        if hasattr(self.vector_db, 'update_settings'):
            self.vector_db.update_settings(new_settings)

    def _reset_caches(self) -> None:
        """Reset any caches that might be affected by settings changes."""
        self.query_cache = {}
        self.memory = []