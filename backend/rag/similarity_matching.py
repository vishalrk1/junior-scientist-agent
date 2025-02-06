import os 
import json
import pickle
from typing import Optional, List, Set, Dict, Any
from openai import OpenAI
from dataclasses import dataclass

from sklearn.preprocessing import normalize
from rank_bm25 import BM25Okapi
import networkx as nx
import numpy as np
import spacy

@dataclass
class Config:
    use_semantic: bool = True
    use_keyword: bool = True
    use_knowledge_graph: bool = True
    semantic_weight: float = 0.4
    keyword_weight: float = 0.3
    knowledge_graph_weight: float = 0.3

    def validate_weights(self) -> bool:
        weights_sum = (self.semantic_weight * self.use_semantic + 
                      self.keyword_weight * self.use_keyword + 
                      self.knowledge_graph_weight * self.use_knowledge_graph)
        return abs(weights_sum - 1.0) < 0.001

class SimilarityMatching:
    def __init__(self, api_key: str, db_path: Optional[str] = None):
        if not api_key:
            raise ValueError("API key cannot be empty")
        
        try:
            self.client = OpenAI(api_key=api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize OpenAI client: {str(e)}")

        self.db_path = db_path if db_path else "data/hybrid_similarity.pkl"
        
        self.embeddings = []
        self.documents = []
        self.metadata = []
        self.query_cache = {} # Cache for query embeddings
        
        self.bm25 = None
        self.tokenized_docs = []

        self.nlp = spacy.load("en_core_web_lg")
        self.knowledge_graph = nx.Graph()
        self.entity_doc_map = {} 

    def _get_embedding(self, text: str) -> List[float]:
        if not text:
            raise ValueError("Text cannot be empty")
        
        try:
            res = self.client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return res.data[0].embedding
        except Exception as e:
            raise RuntimeError(f"Failed to get embedding: {str(e)}")

    def _get_batch_embeddings(self, texts: List[str], batch_size: int = 128) -> List[List[float]]:
        if not texts:
            raise ValueError("Texts list cannot be empty")
        if batch_size < 1:
            raise ValueError("Batch size must be positive")

        all_embeddings = []
        try:
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                res = self.client.embeddings.create(
                    input=batch,
                    model="text-embedding-3-small"
                )
                batch_embeddings = [item.embedding for item in res.data]
                all_embeddings.extend(batch_embeddings)
            return all_embeddings
        except Exception as e:
            raise RuntimeError(f"Failed to get batch embeddings: {str(e)}")
    
    def _extract_entities_and_relations(self, text: str, doc_idx: int) -> Set[str]:
        doc = self.nlp(text)
        entities = set()
        
        # Extract entities and add to graph
        for ent in doc.ents:
            entity_text = ent.text.lower()
            entities.add(entity_text)
            
            if not self.knowledge_graph.has_node(entity_text):
                self.knowledge_graph.add_node(entity_text, label=ent.label_)
            
            if entity_text not in self.entity_doc_map:
                self.entity_doc_map[entity_text] = set()
            self.entity_doc_map[entity_text].add(doc_idx)

        for sent in doc.sents:
            sent_entities = [ent.text.lower() for ent in sent.ents]
            for i in range(len(sent_entities)):
                for j in range(i + 1, len(sent_entities)):
                    self.knowledge_graph.add_edge(
                        sent_entities[i],
                        sent_entities[j],
                        weight=1.0
                    )
        
        return entities

    def load_data(self, data: List[Dict[str, Any]]) -> None:
        if not data:
            raise ValueError("Data cannot be empty")
        
        if len(self.embeddings) > 0 and len(self.metadata) > 0:
            return

        try:
            texts = [item.get('content', '').lower() for item in data]
            if not all(texts):
                raise ValueError("All items must have non-empty content")

            self.documents = texts
            self.metadata = data
            
            all_embeddings = self._get_batch_embeddings(texts)
            self.embeddings = np.array(all_embeddings).astype('float32')
            
            self.tokenized_docs = [text.split() for text in texts]
            self.bm25 = BM25Okapi(self.tokenized_docs)
            
            # Build knowledge graph
            for idx, text in enumerate(texts):
                self._extract_entities_and_relations(text, idx)
                
            self.save_db()
        except Exception as e:
            raise RuntimeError(f"Failed to load data: {str(e)}")
         
    def save_db(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            data = {
                "embeddings": self.embeddings,
                "documents": self.documents,
                "metadata": self.metadata,
                "query_cache": self.query_cache,
                "tokenized_docs": self.tokenized_docs,
                "knowledge_graph": nx.node_link_data(self.knowledge_graph),
                "entity_doc_map": self.entity_doc_map
            }
            
            with open(self.db_path, "wb") as file:
                pickle.dump(data, file)
        except Exception as e:
            raise RuntimeError(f"Failed to save database: {str(e)}")

    def load_db(self) -> None:
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database file not found at {self.db_path}")
            
        try:
            with open(self.db_path, 'rb') as file:
                data = pickle.load(file)
                self.embeddings = data["embeddings"]
                self.documents = data["documents"]
                self.metadata = data["metadata"]
                self.query_cache = data["query_cache"]
                self.tokenized_docs = data["tokenized_docs"]
                self.knowledge_graph = nx.node_link_graph(data["knowledge_graph"])
                self.entity_doc_map = data["entity_doc_map"]
                
            self.bm25 = BM25Okapi(self.tokenized_docs)
        except Exception as e:
            raise RuntimeError(f"Failed to load database: {str(e)}")
    
    def _get_semantic_scores(self, query_embedding: np.ndarray) -> np.ndarray:
        # Ensure query embedding is 1D
        query_embedding = query_embedding.ravel()
        # Normalize and calculate dot product
        return np.dot(normalize(self.embeddings, axis=1, norm='l2'), 
                     normalize(query_embedding.reshape(1, -1), axis=1, norm='l2').T).ravel()

    def _get_keyword_scores(self, query: str) -> np.ndarray:
        return np.array(self.bm25.get_scores(query.lower().split()))

    def _get_graph_scores(self, query: str) -> np.ndarray:
        query_entities = {ent.text.lower() for ent in self.nlp(query).ents}
        scores = np.zeros(len(self.documents))
        
        for query_entity in query_entities:
            if query_entity in self.knowledge_graph:
                # Find related entities within 2 hops
                related_entities = set()
                for node in nx.single_source_shortest_path_length(
                    self.knowledge_graph, query_entity, cutoff=2
                ).keys():
                    related_entities.add(node)
                
                for entity in related_entities:
                    if entity in self.entity_doc_map:
                        doc_indices = self.entity_doc_map[entity]
                        for doc_idx in doc_indices:
                            # Weight by path length and edge weights
                            try:
                                path_length = nx.shortest_path_length(
                                    self.knowledge_graph, 
                                    query_entity, 
                                    entity, 
                                    weight='weight'
                                )
                                scores[doc_idx] += 1.0 / (1.0 + path_length)
                            except nx.NetworkXNoPath:
                                continue
        
        return normalize(scores.reshape(-1, 1), norm='l2').flatten()
    
    def search(self, query: str, config: Config, k: int = 3) -> List[Dict]:
        if not query:
            raise ValueError("Query cannot be empty")
        if k < 1:
            raise ValueError("k must be positive")
        if not config.validate_weights():
            raise ValueError("Config weights must sum to 1.0")
        if not self.documents:
            raise RuntimeError("No documents loaded")

        try:
            scores = np.zeros(len(self.documents))
            weights_sum = 0
            
            # Semantic search
            if config.use_semantic:
                if query in self.query_cache:
                    query_embedding = self.query_cache[query]
                else:
                    query_embedding = self._get_embedding(query)
                    self.query_cache[query] = query_embedding
                
                semantic_scores = self._get_semantic_scores(
                    np.array(query_embedding).reshape(1, -1)
                )
                scores += config.semantic_weight * semantic_scores
                weights_sum += config.semantic_weight
            
            # Keyword search
            if config.use_keyword:
                keyword_scores = self._get_keyword_scores(query)
                scores += config.keyword_weight * normalize(
                    keyword_scores.reshape(-1, 1), 
                    norm='l2'
                ).flatten()
                weights_sum += config.keyword_weight
            
            # Knowledge graph search
            if config.use_knowledge_graph:
                graph_scores = self._get_graph_scores(query)
                scores += config.knowledge_graph_weight * graph_scores  # Fixed attribute name
                weights_sum += config.knowledge_graph_weight  # Fixed attribute name
            
            # Normalize final scores
            if weights_sum > 0:
                scores /= weights_sum
            
            # Get top k results
            top_indices = np.argsort(-scores)[:k]
            
            results = []
            for idx in top_indices:
                result = {
                    "metadata": self.metadata[idx],
                    "similarity": float(scores[idx])
                }
                results.append(result)
            
            return results
        except Exception as e:
            raise RuntimeError(f"Search failed: {str(e)}")


