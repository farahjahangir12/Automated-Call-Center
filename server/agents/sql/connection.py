import os
from supabase import create_client, Client # type: ignore
from dotenv import load_dotenv # type: ignore

# Load environment variables from a .env file
load_dotenv()

# Fetch Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Ensure credentials exist
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials! Check your .env file.")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)



__all__ = ["supabase"]
