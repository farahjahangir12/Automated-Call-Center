import os
from supabase import create_client, Client # type: ignore
from dotenv import load_dotenv # type: ignore
import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

# Load environment variables from a .env file
load_dotenv()

# Fetch Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Ensure credentials exist
if not SUPABASE_URL or not SUPABASE_KEY:
    error_msg = "Missing Supabase credentials! Check your .env file."
    logger.error(error_msg)
    raise ValueError(error_msg)

# Initialize the client synchronously
client = create_client(SUPABASE_URL, SUPABASE_KEY)

class AsyncSupabaseClient:
    def __init__(self):
        self._client = client
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the Supabase client if not already done"""
        if self._initialized:
            return

        async with self._lock:
            if not self._initialized:  # Double check
                try:
                    logger.info("Initializing Supabase client")
                    
                    # Test the connection
                    response = self._client.table("patients").select("count").execute()
                    if not response:
                        raise Exception("Failed to connect to Supabase")
                    
                    self._initialized = True
                    logger.info("Successfully connected to Supabase")
                except Exception as e:
                    error_msg = f"Failed to initialize Supabase client: {str(e)}"
                    logger.error(error_msg)
                    raise ConnectionError(error_msg)

    async def table(self, table_name: str):
        """Get a table reference"""
        return self._client.table(table_name)

    async def query(self, table_name: str, query: str, params: dict = None):
        """Execute a query on a table"""
        try:
            table = self._client.table(table_name)
            if query == "select":
                result = table.select("*").execute()
            elif query == "insert":
                result = table.insert(params).execute()
            elif query == "update":
                result = table.update(params).execute()
            elif query == "delete":
                result = table.delete().eq("id", params["id"]).execute()
            else:
                raise ValueError(f"Unsupported query type: {query}")
            
            return result
        except Exception as e:
            logger.error(f"Query error: {str(e)}")
            raise

supabase = AsyncSupabaseClient()

__all__ = ["supabase"]
