import os
import json
import re
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

def execute_query_with_fuzzy_matching(graph, query):
    """Perform fuzzy matching on entity names before executing the query."""
    print("\n=== 🛠️ Starting execute_query_with_fuzzy_matching ===")
    print(f"Original query: {query}")
    
    modified_query = query
    match = re.search(r"{{\s*name\s*:\s*['\"]([^'\"]+)['\"]\s*}}", query) or \
           re.search(r"{\s*name\s*:\s*['\"]([^'\"]+)['\"]\s*}", query)

    if match:
        entity_name = match.group(1).strip()
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
            modified_query = query.replace(entity_name, corrected_name)
            print(f"✅ Corrected '{entity_name}' to '{corrected_name}'")
        else:
            print(f"⚠ No fuzzy match found for '{entity_name}'. Proceeding with original.")
    else:
        print("ℹ️ No entity name found in query for fuzzy matching")

    print(f"Final query to execute: {modified_query}")
    query_result = graph.query(modified_query)
    print(f"Query result: {query_result}")
    print("=== 🛠️ Finished execute_query_with_fuzzy_matching ===")
    return query_result

def generate_response(user_question):
    """Generate response to user question using Neo4j and LLM"""
    examples = [
        {"question": "How many diseases are there?", "query": "MATCH (d:Disease) RETURN count(d)"},
        {"question": "Symptoms of COVID-19?", "query": "MATCH (s:Symptom)-[:SYMPTOM_OF]->(d:Disease {{name: 'COVID-19'}}) RETURN s.name"},
        {"question": "Drugs for Diabetes?", "query": "MATCH (d:Disease {{name: 'Diabetes'}})<-[:PRESCRIBED_FOR]-(drug:Drug) RETURN drug.name"},
    ]

    schema = """Node properties:
Disease {{name: STRING}}, Symptom {{name: STRING}}, GeneticLinkage {{name: STRING}}, 
CareInstruction {{name: STRING}}, Drug {{name: STRING}}, Treatment {{name: STRING}}, 
SideEffect {{name: STRING}}.

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
        prefix="""You are a Neo4j expert. Given an input question, create a syntactically correct Cypher query and return only the Cypher query as output.

Here is the schema information:
{schema}.

Examples of questions and their corresponding Cypher queries:""",
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

    generated_query = response.content.strip()
    query_result = execute_query_with_fuzzy_matching(graph, generated_query)

    if not query_result:
        return "I couldn't find any information about that in our database."

    # Generate natural language response
    response_prompt = f"""You are a Clinical Triage agent for Osaka University Hospital.
Convert this database query result into a natural language response:

User query: {user_question}
Query result: {json.dumps(query_result, indent=2)}

Response:"""
    
    final_response = llm.invoke(response_prompt)
    return final_response.content

def main():
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

            # Add to memory and generate response
            memory.chat_memory.add_user_message(user_input)
            response = generate_response(user_input)
            memory.chat_memory.add_ai_message(response)
            
            print(f"\nAssistant: {response}")
            
        except KeyboardInterrupt:
            print("\n\nSession ended by user. Goodbye!")
            break
        except Exception as e:
            print(f"\n⚠️ An error occurred: {str(e)}")

if __name__ == "__main__":
    print("=== 🚀 Starting application ===")
    main()