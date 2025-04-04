import os
import json
import re
import asyncio
from langchain_community.graphs import Neo4jGraph
from langchain.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv

load_dotenv()

# Initialize components
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
    database="medicalrag"
)

llm = ChatGroq(
    model_name="gemma2-9b-it",
    temperature=0.2,
    api_key=os.getenv("GROQ_API_KEY"),
)

memory = ConversationBufferMemory()

def clean_cypher_query(query: str) -> str:
    """Clean and validate Cypher queries"""
    # Remove markdown code blocks if present
    if query.startswith("```cypher"):
        query = query[9:]  # Remove ```cypher
    if query.endswith("```"):
        query = query[:-3]  # Remove ```
    
    # Fix common syntax issues
    query = query.strip()
    query = query.replace('"', "'")  # Standardize quotes
    query = query.replace("SYMPTOMM_OF", "SYMPTOM_OF")  # Fix relationship typo
    
    # Ensure query ends with semicolon
    if not query.endswith(";"):
        query += ";"
    
    return query

def execute_query_with_fuzzy_matching(graph, query):
    """Perform fuzzy matching on entity names before executing the query."""
    print("\n=== 🛠️ Starting execute_query_with_fuzzy_matching ===")
    print(f"Original query: {query}")
    
    # Clean the query first
    query = clean_cypher_query(query)
    modified_query = query
    
    # Match both {name: 'value'} and {{name: 'value'}} patterns
    matches = re.finditer(r"{{\s*name\s*:\s*['\"]([^'\"]+)['\"]\s*}}|{\s*name\s*:\s*['\"]([^'\"]+)['\"]\s*}", query)

    for match in matches:
        # Use group 1 or group 2 depending on which pattern matched
        entity_name = match.group(1) if match.group(1) else match.group(2)
        entity_name = entity_name.strip()
        print(f"🔍 Found entity name in query: '{entity_name}'")

        fuzzy_match_query = f"""
            MATCH (n)
            WHERE apoc.text.levenshteinSimilarity(n.name, "{entity_name}") > 0.7
            RETURN n.name AS correctedName LIMIT 1
        """
        print(f"Fuzzy match query:\n{fuzzy_match_query}")
        
        result = graph.query(fuzzy_match_query)
        print(f"Fuzzy match result: {result}")

        if result and result[0].get("correctedName"):
            corrected_name = result[0]["correctedName"]
            modified_query = modified_query.replace(entity_name, corrected_name)
            print(f"✅ Corrected '{entity_name}' to '{corrected_name}'")
        else:
            print(f"⚠ No fuzzy match found for '{entity_name}'. Proceeding with original.")

    print(f"Final query to execute: {modified_query}")
    try:
        query_result = graph.query(modified_query)
        print(f"Query result: {query_result}")
        print("=== 🛠️ Finished execute_query_with_fuzzy_matching ===")
        return query_result
    except Exception as e:
        print(f"⚠️ Query execution failed: {str(e)}")
        return None

async def handle_query(user_question: str) -> str:
    """Handle medical graph queries programmatically for router integration"""
    try:
        if user_question.lower() in ['exit', 'quit', 'bye']:
            memory.clear()
            return "Thank you for contacting Osaka University Hospital. Have a good day!"
            
        examples = [
            {"question": "How many diseases are there?", "query": "MATCH (d:Disease) RETURN count(d);"},
            {"question": "Symptoms of COVID-19?", "query": "MATCH (s:Symptom)-[:SYMPTOM_OF]->(d:Disease {{name: 'COVID-19'}}) RETURN s.name;"},
            {"question": "Drugs for Diabetes?", "query": "MATCH (d:Disease {{name: 'Diabetes'}})<-[:PRESCRIBED_FOR]-(drug:Drug) RETURN drug.name;"},
        ]

        schema = """Node properties:
Disease {name: STRING}, Symptom {name: STRING}, GeneticLinkage {name: STRING}, 
CareInstruction {name: STRING}, Drug {name: STRING}, Treatment {name: STRING}, 
SideEffect {name: STRING}.

Relationships:
(:Symptom)-[:SYMPTOM_OF]->(:Disease), 
(:GeneticLinkage)-[:LINKED_TO]->(:Disease), 
(:CareInstruction)-[:RECOMMENDED_FOR]->(:Disease), 
(:Drug)-[:PRESCRIBED_FOR]->(:Disease), 
(:Drug)-[:RECOMMENDED_DOSAGE]->(:Disease), 
(:Treatment)-[:TREATS]->(:Disease), 
(:Treatment)-[:USES_DRUG]->(:Drug), 
(:Treatment)-[:HAS_SIDE_EFFECT]->(:SideEffect)."""

        example_prompt = PromptTemplate.from_template(
            "User input: {question}\nCypher query: {query}"
        )

        prompt = FewShotPromptTemplate(
            examples=examples,
            example_prompt=example_prompt,
            prefix="""You are a Neo4j expert. Generate ONLY the Cypher query - no additional text or markdown. 

Important rules:
1. Always use single quotes for string values
2. Always end queries with a semicolon
3. Never include markdown code blocks
4. Use correct relationship types from schema

Schema:
{schema}

Examples:""",
            suffix="User input: {question}\nCypher query:",
            input_variables=["question", "schema"],
        )

        # Generate Cypher query
        formatted_prompt = prompt.format(
            question=user_question,
            schema=schema
        )
        response = llm.invoke(formatted_prompt)
        
        if not response or not hasattr(response, 'content'):
            return "I couldn't generate a proper query for that question."

        generated_query = response.content
        print(f"\nGenerated query before cleaning: {generated_query}")
        generated_query = clean_cypher_query(generated_query)
        print(f"Cleaned query: {generated_query}")

        query_result = execute_query_with_fuzzy_matching(graph, generated_query)

        if not query_result:
            return "I couldn't find any information about that in our database."

        # Generate natural language response
        response_prompt = f"""You are a Clinical Triage agent for Osaka University Hospital. 
Explain these results in simple, compassionate terms:

Question: {user_question}
Results: {json.dumps(query_result, indent=2)}

Response:"""
        
        final_response = llm.invoke(response_prompt)
        
        # Update conversation memory
        memory.chat_memory.add_user_message(user_question)
        memory.chat_memory.add_ai_message(final_response.content)
        
        return final_response.content
        
    except Exception as e:
        memory.clear()
        return f"⚠️ An error occurred: {str(e)}"

# Preserve original main for testing
def main():
    """Standalone testing mode"""
    print("""
    ┌───────────────────────────────────────────────────────────────┐
    │          Osaka University Hospital - Clinical Triage          │
    │                   Automated Call Center System                │
    └───────────────────────────────────────────────────────────────┘
    Type 'exit' to end the conversation.
    """)

    while True:
        try:
            user_input = input("\nPatient: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\nThank you for contacting Osaka University Hospital. Have a good day!")
                break
                
            if not user_input:
                print("Please enter a valid question.")
                continue

            response = asyncio.run(handle_query(user_input))
            print(f"\nAssistant: {response}")
            
        except KeyboardInterrupt:
            print("\n\nSession ended by user. Goodbye!")
            break

if __name__ == "__main__":
    print("=== 🚀 Starting application ===")
    main()