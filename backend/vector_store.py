import os
import chromadb
from chromadb.utils import embedding_functions
from .database import EMS_PROTOCOLS, get_all_protocols

# Initialize ChromaDB
# For a persistent DB: chromadb.PersistentClient(path="./chroma_db")
chroma_client = chromadb.Client() 
collection = chroma_client.create_collection(name="ems_movements")

# We can use a default embedding function or a specific one.
# For simplicity and offline capability without keys, we'll rely on the default (all-MiniLM-L6-v2) 
# which ChromaDB downloads automatically.

def initialize_vector_db():
    print("Initializing Vector Database...")
    protocols = get_all_protocols()
    
    ids = []
    documents = []
    metadatas = []
    
    for key, data in EMS_PROTOCOLS.items():
        ids.append(key)
        # We embed the description and the action name as the semantic content
        text_content = f"{data['action']}: {data['description']} Muscles: {', '.join(data['muscles'])}"
        documents.append(text_content)
        metadatas.append({"action": data['action'], "key": key})
        
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print(f"Vector Database populated with {len(ids)} movements.")

def search_movement(query, n_results=1):
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )

    print(f"The result is {results}");
    
    if not results['ids'] or len(results['ids'][0]) == 0:
        return None
        
    # extract the best match key
    best_key = results['ids'][0][0]
    distance = results['distances'][0][0] # Smaller distance = better match
    
    print(f"Query: '{query}' mapped to '{best_key}' with distance {distance}")
    
    # Threshold for "I don't know"
    # Empirical testing: exact match is ~0. unrelated is > 1.3
    if distance > 1.5: 
        print("Distance too high. Returning None.")
        return None

    return best_key
