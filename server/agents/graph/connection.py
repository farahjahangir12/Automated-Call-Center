import os
from langchain_community.graphs import Neo4jGraph  # Ensure correct import
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Fetch Neo4j credentials from environment variables
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "medicalrag")

# Ensure credentials exist
if not NEO4J_URI or not NEO4J_USERNAME or not NEO4J_PASSWORD:
    raise ValueError("Missing Neo4j credentials! Check your .env file.")

# Initialize Neo4j graph connection
graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    database=NEO4J_DATABASE,
    refresh_schema=False
)

__all__ = ["graph"]