#!/usr/bin/env python
# filepath: d:\FYP\server\agents\rag\run_evaluation.py

import asyncio
import os
import sys
from dotenv import load_dotenv
import pandas as pd

# Don't import both modules at the top level
# Instead, use a function to handle the evaluation logic
async def run_evaluation_process(evaluation_csv: str):
    """Run the evaluation process with the given CSV file"""
    # Dynamically import what we need when we need it
    from evaluation import preprocess_dataset, evaluate_rag_performance, evaluate_retrieval_performance
    
    print(f"Loading dataset: {evaluation_csv}")
    df = preprocess_dataset(evaluation_csv)
    
    # Here you'd normally run the RAG system
    # For now, just assume the data already has needed columns
    
    # Convert to format needed for evaluation
    from datasets import Dataset
    dataset = Dataset.from_pandas(df)
    
    # Run evaluations
    try:
        rag_results = await evaluate_rag_performance(dataset)
        retrieval_results = await evaluate_retrieval_performance(df)
        
        print("\nEvaluation Results:")
        print("RAG Results:", rag_results)
        print("Retrieval Results:", retrieval_results)
        
    except Exception as e:
        print(f"Evaluation failed: {str(e)}")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Get evaluation file from command line or environment
    evaluation_csv = sys.argv[1] if len(sys.argv) > 1 else os.getenv("EVALUATION_CSV", "evaluation_data.csv")
    
    print(f"Starting RAG evaluation using {evaluation_csv}...")
    asyncio.run(run_evaluation_process(evaluation_csv))