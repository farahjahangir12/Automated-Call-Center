# hospital_pdf_to_supabase.py
import os
import re
import fitz  # PyMuPDF
import hashlib
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_cohere import CohereEmbeddings
import asyncio

# Load environment variables
load_dotenv()

# Initialize clients
embeddings = CohereEmbeddings(
    model="embed-english-v3.0",
    cohere_api_key=os.getenv("COHERE_API_KEY")
)
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Collection configurations
COLLECTION_CONFIG = {
    "Department_Details": {
        "chunk_size": 500,
        "separators": ["Dr. ", "Department of", "\n\n"],
        "metadata_template": {
            "type": "department",
            "auto_fields": {
                "specialty": r"Special(?:ty|ization):\s*(\w+)"
            }
        },
        
    },
    "General_Consulting": {
        "chunk_size": 300,
        "separators": ["Service:", "\n• ", "\n- "],
        "metadata_template": {
            "service": "outpatient",
            "auto_fields": {
                "urgency": r"(emergency|urgent|routine)"
            }
        },
       
    },
    "Payments_and_Billing": {
        "chunk_size": 400,
        "separators": [
            r"\n\d+\..+?\n",
            r"\n•\s",
            r"\n_{10,}\n",
            r"\n[A-Z][a-z]+:\n"
        ],
        "metadata_template": {
            "type": "billing",
            "auto_fields": {
                "payment_component": r"(Calculation|Timeline|Methods)"
            }
        },
        
    },
    "Patient_Safety_Policy": {
        "chunk_size": 500,
        "separators": ["Service:", "\n\n", r"Section \d+\."],
        "metadata_template": {
            "service": "patient care",
            "auto_fields": {
                "urgency": r"(medical care|patient's safety|technological safety)"
            }
        },
       
    },
    "Outpatients_Policies": {
        "chunk_size": 400,
        "separators": ["Hospital Services:", "\n• ", r"Step \d+"],
        "metadata_template": {
            "service": "outpatient",
            "auto_fields": {
                "urgency": r"(emergency|urgent|routine|elective)"
            }
        },
       
       
    },
    "Admission_Discharge": {
        "chunk_size": 350,
        "separators": [
            "Admission Process", 
            "Requirements", 
            "\n• ",
            "\n- ",
            r"\n\d+\.",
            r"\n[A-Z][a-z]+:\n"
        ],
        "metadata_template": {
            "service": "hospital admission",
            "auto_fields": {
                "urgency": r"(emergency|urgent|routine|elective)"
            }
        },
       
    },
    "Principles_Policies": {
        "chunk_size": 300,
        "separators": [
            r"\n##\s+.+?\n",
            r"\n###\s+.+?\n",
            r"\n-\s",
            r"\n•\s",
            r"\nChildren's Rights",
            r"\n\n"
        ],
        "metadata_template": {
            "service": "principles",
            "auto_fields": {
                "rights_type": r"(Patients' Rights|Children's Rights)"
            }
        },
        
    }
}

def get_pdf_hash(pdf_path: str) -> str:
    """Generate hash for change detection"""
    with open(pdf_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def extract_text(pdf_path: str) -> str:
    """Extract and clean text from PDF"""
    with fitz.open(pdf_path) as doc:
        text = "\n".join([page.get_text().strip() for page in doc])
    return re.sub(r'Page \d+|^.*Confidential.*$', '', text, flags=re.MULTILINE)

def chunk_content(text: str, collection: str) -> List[str]:
    """Collection-specific chunking"""
    config = COLLECTION_CONFIG[collection]
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config["chunk_size"],
        chunk_overlap=100,
        separators=config["separators"]
    )
    return splitter.split_text(text)

def generate_metadata(text: str, pdf_path: str, collection: str) -> Dict:
    """Create metadata with auto-extracted fields"""
    config = COLLECTION_CONFIG[collection]
    metadata = config["metadata_template"].copy()
    
    # Auto-extract fields
    for field, pattern in metadata.get("auto_fields", {}).items():
        if match := re.search(pattern, text, re.IGNORECASE):
            metadata[field] = match.group(1).lower()
    
    # Add standard fields
    metadata.update({
        "source_file": os.path.basename(pdf_path),
        "content_hash": hashlib.md5(text.encode()).hexdigest(),
        "pdf_hash": get_pdf_hash(pdf_path),
        "processed_at": datetime.now().isoformat()
    })
    return {k: v for k, v in metadata.items() if v is not None}

async def generate_embeddings(texts: List[str], collection: str) -> List[List[float]]:
    """Generate embeddings using LangChain's CohereEmbeddings"""
    input_type = COLLECTION_CONFIG[collection]
    return await embeddings.aembed_documents(texts)

def upsert_to_supabase(data: List[Dict]):
    """Batch upsert to Supabase"""
    batch_size = 100  # Supabase limit
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        supabase.table("hospital_documents").upsert(batch).execute()

async def process_pdf(pdf_path: str, collection: str):
    """End-to-end PDF processing pipeline"""
    print(f"Processing {pdf_path} for {collection}...")
    
    # Check if PDF was already processed
    current_hash = get_pdf_hash(pdf_path)
    existing = supabase.table("hospital_documents") \
        .select("id") \
        .eq("metadata->>source_file", os.path.basename(pdf_path)) \
        .eq("metadata->>pdf_hash", current_hash) \
        .execute()
    
    if len(existing.data) > 0:
        print(f"✓ Already processed {pdf_path}")
        return
    
    # Process PDF
    text = extract_text(pdf_path)
    chunks = chunk_content(text, collection)
    
    # Process in batches to avoid API limits
    results = []
    for i in range(0, len(chunks), 32):  # Cohere's max batch size
        batch = chunks[i:i + 32]
        batch_embeddings = await generate_embeddings(batch, collection)
        
        for chunk, embedding in zip(batch, batch_embeddings):
            results.append({
                "content": chunk,
                "embedding": embedding,
                "metadata": generate_metadata(chunk, pdf_path, collection)
            })
    
    # Save to Supabase
    upsert_to_supabase(results)
    print(f"✓ Saved {len(results)} chunks from {pdf_path}")

async def main():
    # Example usage - process all PDFs in a folder
    # Try one of these:
    PDF_DIR = r"D:\FYP\client\public"  # Absolute path
    for filename in os.listdir(PDF_DIR):
        if filename.endswith(".pdf"):
            # Map filename to collection
            if "Department" in filename:
                collection = "Department_Details"
            elif "Consulting" in filename:
                collection = "General_Consulting"
            elif "Payment" in filename or "Billing" in filename:
                collection = "Payments_and_Billing"
            elif "Principles" in filename:
                collection = "Principles_Policies"
            elif "Information" in filename or "Outpatient" in filename:
                collection = "Outpatients_Policies"
            elif "admitted" in filename.lower():
                collection = "Admission_Discharge"
            elif "Patient Safety" in filename:
                collection = "Patient_Safety_Policy"
            
            await process_pdf(os.path.join(PDF_DIR, filename), collection)

if __name__ == "__main__":
    asyncio.run(main())