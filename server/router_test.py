import asyncio
import csv
import os
import sys
import time
import pandas as pd
from datetime import datetime
from router import HospitalRouter

# Test query templates for each agent type
SQL_QUERIES = [
    # Appointment booking
    "I need to book an appointment with Dr. Yamamoto",
    "Can I schedule a consultation for next Tuesday?",
    "I want to make an appointment for my annual checkup",
    "How do I book an appointment with the cardiologist?",
    "Schedule me for a blood test tomorrow",
    "I need to see a doctor this week",
    "Book me a slot with the neurologist",
    "Can I get an appointment at 3:30 PM?",
    "I'd like to book a dental checkup",
    "Schedule me for vaccination",
    
    # Appointment cancellation/rescheduling
    "I need to cancel my appointment on Thursday",
    "Can I reschedule my consultation with Dr. Tanaka?",
    "Need to move my appointment from Monday to Wednesday",
    "I can't make it to my 2:00 PM appointment tomorrow",
    "Please cancel my upcoming consultation",
    "Reschedule my MRI appointment to next week",
    "I want to change my appointment time from morning to afternoon",
    "Cancel my dental cleaning appointment",
    "I need to postpone my checkup",
    
    # Doctor availability
    "When is Dr. Suzuki available this week?",
    "Which neurologists are available on Friday?",
    "Is the dermatologist available tomorrow?",
    "What are Dr. Nakamura's office hours?",
    "Do you have any pediatricians available today?",
    "When can I see Dr. Watanabe?",
    "Is the ENT specialist in today?",
    "Are there any available appointments with the orthopedist?",
    "What time does Dr. Ito see patients?",
    
    # Patient registration
    "I need to register as a new patient",
    "How do I update my patient information?",
    "I want to enroll in your hospital system",
    "Can I register my daughter as a new patient?",
    "What forms do I need to fill out for registration?",
    "How do I sign up for the patient portal?",
    "I need to add my new insurance information to my record",
    "Register my son who is 5 years old",
    
    # Schedule inquiries
    "What are the clinic hours for pediatrics?",
    "Is the radiology department open on weekends?",
    "What time does the laboratory close today?",
    "When does the pharmacy open tomorrow?",
    "Is the hospital clinic open on national holidays?",
    "What are your weekend hours?",
    "Do I need to make an appointment for blood work?",
    "What are the consultation hours for cardiology?"
]

GRAPH_QUERIES = [
    # Medical symptoms
    "I've been having persistent headaches for three days",
    "What could cause sudden dizziness and nausea?",
    "My child has a high fever and rash",
    "I'm experiencing chest pain when I breathe deeply",
    "What does it mean if I have numbness in my left arm?",
    "My joints are swollen and painful",
    "I've been having trouble sleeping and feel anxious",
    "What causes persistent coughing at night?",
    "I've been feeling unusually tired lately",
    "Why am I experiencing shortness of breath?",
    
    # Disease information
    "What is diabetes and how is it treated?",
    "Tell me about hypertension causes",
    "What are the early signs of Alzheimer's?",
    "How is rheumatoid arthritis different from osteoarthritis?",
    "What should I know about asthma?",
    "Explain the difference between type 1 and type 2 diabetes",
    "What are the stages of chronic kidney disease?",
    "How does multiple sclerosis progress?",
    "What are the risk factors for heart disease?",
    "Tell me about migraine triggers",
    
    # Treatment options
    "What are the treatment options for chronic back pain?",
    "How is pneumonia treated in elderly patients?",
    "What treatments are available for severe allergies?",
    "How is Crohn's disease managed?",
    "What therapy is recommended for anxiety disorders?",
    "Treatment approaches for childhood asthma",
    "What are my options for treating osteoporosis?",
    "How is high cholesterol typically treated?",
    "What treatments exist for psoriasis?",
    "How is hyperthyroidism managed?",
    
    # Medication queries
    "What are the side effects of lisinopril?",
    "How does metformin work for diabetes?",
    "Can I take ibuprofen with my blood pressure medication?",
    "What should I know about statin medications?",
    "Is there a generic alternative to Lipitor?",
    "How long should I take antibiotics for a sinus infection?",
    "What is the proper dosage of amoxicillin for a child?",
    "Are there any interactions between my blood thinner and vitamin supplements?",
    "When should I take my thyroid medication?",
    "What's the difference between brand name and generic medications?"
]

RAG_QUERIES = [
    # Hospital policies
    "What is your patient privacy policy?",
    "Do you have a no-smoking policy?",
    "What is your visitor policy for the ICU?",
    "How do you handle medical records requests?",
    "What is your policy on releasing patient information?",
    "What are your COVID-19 visitor restrictions?",
    "Do you have a patient bill of rights?",
    "What is your policy on advance directives?",
    "How do you handle prescription refills?",
    "What is your complaint resolution process?",
    
    # Visiting hours & admission
    "What are the visiting hours for general wards?",
    "Can children visit patients in the hospital?",
    "What are the ICU visiting hours?",
    "How early can I arrive before scheduled surgery?",
    "What time do you begin discharges?",
    "What should I bring for overnight admission?",
    "Are there visitor limitations per patient?",
    "What time can family visit after surgery?",
    "What is the check-in procedure for scheduled admissions?",
    "Do you offer overnight accommodations for family members?",
    
    # Payment information
    "Do you accept international insurance?",
    "What payment methods do you accept?",
    "How do I get an itemized bill?",
    "Do you offer payment plans?",
    "How do I submit my insurance information?",
    "What is your policy on copayments?",
    "Do you provide cost estimates before procedures?",
    "How do I pay my hospital bill online?",
    "What insurance providers do you work with?",
    "Is financial assistance available?",
    
    # Facility questions
    "Do you have parking available for patients?",
    "Is there a cafeteria in the hospital?",
    "Where is the nearest pharmacy to your hospital?",
    "Do you have Wi-Fi available for patients?",
    "Is there an ATM inside the hospital?",
    "Where is the outpatient laboratory located?",
    "Do you have a gift shop?",
    "Are there accommodations near the hospital for families?",
    "Is there a chapel or meditation room available?",
    "Do you provide wheelchair assistance within the facility?"
]

async def generate_test_queries():
    """Generate a diverse set of test queries for classification"""
    test_queries = []
    
    # Add all template queries
    test_queries.extend([(query, "sql") for query in SQL_QUERIES])
    test_queries.extend([(query, "graph") for query in GRAPH_QUERIES])
    test_queries.extend([(query, "rag") for query in RAG_QUERIES])
    
    # Add variations with question marks, polite forms, etc.
    variations = []
    for query, expected in test_queries[:50]:  # Take a subset for variations
        variations.append((f"{query}?", expected))
        variations.append((f"I was wondering {query.lower()}?", expected))
        variations.append((f"Could you please tell me {query.lower()}?", expected))
        
    test_queries.extend(variations)
    
    # Sort randomly and take first 300
    import random
    random.shuffle(test_queries)
    return test_queries[:300]

async def test_router_classification(csv_path):
    """Test router classification on queries and save results"""
    # Initialize the router
    print("Initializing router...")
    router = await HospitalRouter.create()
    print("Router initialized successfully!")
    
    # Load or generate test queries
    if os.path.exists(csv_path):
        print(f"Loading existing test queries from {csv_path}")
        df = pd.read_csv(csv_path)
        test_queries = df['question'].tolist()
        results = []
        
        print(f"Found {len(test_queries)} test queries")
    else:
        print("Generating test queries...")
        query_data = await generate_test_queries()
        test_queries = [q[0] for q in query_data]
        expected = [q[1] for q in query_data]
        
        results = []
        df = pd.DataFrame({
            'question': test_queries,
            'expected': expected,
            'response': ''
        })
        
        # Save the initial CSV
        df.to_csv(csv_path, index=False)
        print(f"Generated {len(test_queries)} test queries and saved to {csv_path}")
    
    # Process in batches to avoid overloading
    batch_size = 5
    delay_between_batches = 2  # seconds
    num_batches = (len(test_queries) + batch_size - 1) // batch_size
    
    print(f"\nTesting router classification on {len(test_queries)} queries in {num_batches} batches")
    print(f"Batch size: {batch_size}, delay: {delay_between_batches}s between batches")
    
    for batch_idx in range(num_batches):
        batch_start = batch_idx * batch_size
        batch_end = min(batch_start + batch_size, len(test_queries))
        
        print(f"\nProcessing batch {batch_idx+1}/{num_batches} (queries {batch_start+1}-{batch_end})")
        
        for idx in range(batch_start, batch_end):
            query = test_queries[idx]
            print(f"\n[{idx+1}/{len(test_queries)}] Testing: '{query[:50]}{'...' if len(query) > 50 else ''}'")
            
            try:
                # Classify the query using the router
                department, confidence = await router.classify_query(query, None)
                
                print(f"✓ Classification: {department} (confidence: {confidence:.2f})")
                
                # Store the result
                response_text = f"{department}|{confidence:.2f}"
                
                # Update the dataframe
                if 'response' in df.columns:
                    df.at[idx, 'response'] = response_text
                else:
                    # Create response column if it doesn't exist
                    df['response'] = ''
                    df.at[idx, 'response'] = response_text
                    
            except Exception as e:
                print(f"✗ Error classifying query: {e}")
                if 'response' in df.columns:
                    df.at[idx, 'response'] = f"ERROR: {str(e)}"
        
        # Save after each batch
        df.to_csv(csv_path, index=False)
        print(f"Saved batch {batch_idx+1}/{num_batches} results to {csv_path}")
        
        # Add delay between batches (except after the last batch)
        if batch_idx < num_batches - 1:
            print(f"Pausing for {delay_between_batches}s before next batch...")
            time.sleep(delay_between_batches)
    
    # Calculate accuracy if expected column exists
    if 'expected' in df.columns:
        # Extract classifications from response column
        classifications = df['response'].apply(lambda x: x.split('|')[0] if '|' in str(x) else 'error')
        
        # Calculate accuracy
        correct = sum(classifications == df['expected'])
        accuracy = correct / len(df) * 100
        
        print(f"\nClassification accuracy: {accuracy:.2f}% ({correct}/{len(df)})")
        
        # Add accuracy details to CSV
        df['correct'] = classifications == df['expected']
        df.to_csv(csv_path, index=False)
    
    print(f"\nAll {len(test_queries)} queries processed and results saved to: {csv_path}")
    return df

if __name__ == "__main__":
    # Get CSV path from command line or use default
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "router_classification_test.csv"
    
    print(f"Starting router classification test with output to: {csv_path}")
    asyncio.run(test_router_classification(csv_path))