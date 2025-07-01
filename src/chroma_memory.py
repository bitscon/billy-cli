import chromadb

client = chromadb.PersistentClient(path="/home/billybs/projects/billy/db/chroma")
memory = client.get_or_create_collection("billy_memory")

def save_vector_memory(id, content):
    memory.add(
        ids=[id],
        documents=[content],
        metadatas=[{"source": "billy"}]
    )

def query_vector_memory(query_text, n_results=3):
    results = memory.query(
        query_texts=[query_text],
        n_results=n_results
    )
    return results

def get_semantic_memory(query_text, n_results=3):
    results = query_vector_memory(query_text, n_results)
    memories = []
    for doc_list in results["documents"]:
        for doc in doc_list:
            memories.append(doc)
    return memories
