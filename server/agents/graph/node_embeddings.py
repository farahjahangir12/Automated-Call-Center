import os
import json
import logging
from typing import Optional, List

import numpy as np
from sentence_transformers import SentenceTransformer
from langchain_neo4j import Neo4jGraph
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Neo4j Graph
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
    database="medicalrag"
)

class NodeEmbeddingSystem:
    def __init__(self):
        """Initialize embedding system"""
        self.model = self._load_embedding_model()

    def _load_embedding_model(self, model_name: str = "all-MiniLM-L6-v2"):
        """Load sentence transformer model with error handling"""
        try:
            logger.info(f"Loading embedding model: {model_name}")
            return SentenceTransformer(model_name)
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def fetch_nodes_for_embedding(self, label: Optional[str] = None) -> List[dict]:
        """
        Fetch nodes for embedding with optional label filtering
        
        Args:
            label: Optional node label to filter nodes
        
        Returns:
            List of nodes with id, label, and name
        """
        query = """
        MATCH (n)
        WHERE n.name IS NOT NULL
        {{ LABEL_FILTER }}
        RETURN id(n) as node_id, labels(n)[0] as label, n.name as name
        """
        
        if label:
            query = query.replace("{{ LABEL_FILTER }}", f"AND '{label}' IN labels(n)")
        else:
            query = query.replace("{{ LABEL_FILTER }}", "")
        
        try:
            result = graph.query(query)
            logger.info(f"Found {len(result)} nodes for embedding")
            return result
        except Exception as e:
            logger.error(f"Error fetching nodes: {e}")
            return []

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for given text
        
        Args:
            text: Input text to generate embedding
        
        Returns:
            Embedding as a list or None if generation fails
        """
        try:
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed for text '{text}': {e}")
            return None

    def update_node_embedding(self, node_id: int, embedding: List[float], source_text: str) -> bool:
        """
        Update node with embedding and source text
        
        Args:
            node_id: Neo4j node ID
            embedding: Generated embedding
            source_text: Original text used for embedding
        
        Returns:
            Boolean indicating success of update
        """
        update_query = """
        MATCH (n) WHERE id(n) = $node_id
        SET n.embedding = $embedding,
            n.source_text = $source_text,
            n.embedding_timestamp = timestamp()
        """
        
        try:
            graph.query(update_query, params={
                "node_id": node_id, 
                "embedding": embedding,
                "source_text": source_text
            })
            logger.info(f"Updated embedding for node {node_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update embedding for node {node_id}: {e}")
            return False

    def embed_nodes(self, label: Optional[str] = None) -> None:
        """
        Embed all nodes or nodes with specific label
        
        Args:
            label: Optional node label to filter nodes
        """
        nodes = self.fetch_nodes_for_embedding(label)
        
        logger.info(f"Starting embedding process for {len(nodes)} nodes")
        
        for node in nodes:
            embedding = self.generate_embedding(node["name"])
            
            if embedding:
                self.update_node_embedding(
                    node_id=node["node_id"], 
                    embedding=embedding, 
                    source_text=node["name"]
                )

if __name__ == "__main__":
    print("=== 🚀 Starting Node Embedding Application ===")
    embedding_system = NodeEmbeddingSystem()
    embedding_system.embed_nodes()
