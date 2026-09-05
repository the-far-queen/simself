import numpy as np
from collections import deque
import time
from typing import List, Tuple, Optional

# A placeholder for InfoPacket or any object that has a 'vector' attribute.
# Assuming vectors are numpy arrays.
class MemoryEntry:
    def __init__(self, vector: np.ndarray, timestamp: float, metadata: Optional[dict] = None):
        self.vector = vector
        self.timestamp = timestamp
        self.metadata = metadata if metadata is not None else {}

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Calculates the cosine similarity between two vectors."""
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
        
    return dot_product / (norm_v1 * norm_v2)

class VectorMemory:
    """
    Implements a short-term, bounded vector memory for the agent,
    as described in fieldcore-code.md ("Short-term vector memory (not LLM context)").
    It supports embedding-based retrieval and has a bounded size (FIFO eviction).
    """
    def __init__(self, max_size: int = 100, vector_dim: int = 128):
        self.memory: deque[MemoryEntry] = deque(maxlen=max_size)
        self.vector_dim = vector_dim
        print(f"VectorMemory: Initialized with max size {max_size} and vector dimension {vector_dim}.")

    def add_vector(self, vector: np.ndarray, metadata: Optional[dict] = None):
        """
        Adds a new vector to the memory. If memory is full, the oldest entry is evicted.
        """
        if vector.shape[0] != self.vector_dim:
            raise ValueError(f"Vector dimension mismatch. Expected {self.vector_dim}, got {vector.shape[0]}.")
        self.memory.append(MemoryEntry(vector, time.time(), metadata))
        print(f"VectorMemory: Added new vector. Current size: {len(self.memory)}.")

    def query_similar(self, query_vector: np.ndarray, top_k: int = 5) -> List[Tuple[np.ndarray, float, Optional[dict]]]:
        """
        Queries the memory for vectors similar to the query_vector.
        Returns a list of (vector, similarity_score, metadata) tuples, sorted by similarity.
        """
        if query_vector.shape[0] != self.vector_dim:
            raise ValueError(f"Query vector dimension mismatch. Expected {self.vector_dim}, got {query_vector.shape[0]}.")

        similarities: List[Tuple[np.ndarray, float, Optional[dict]]] = []
        for entry in self.memory:
            similarity = cosine_similarity(query_vector, entry.vector)
            similarities.append((entry.vector, similarity, entry.metadata))
        
        # Sort by similarity in descending order and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def get_all_vectors(self) -> List[np.ndarray]:
        """Returns all vectors currently in memory."""
        return [entry.vector for entry in self.memory]

    def get_current_size(self) -> int:
        """Returns the current number of vectors in memory."""
        return len(self.memory)

if __name__ == '__main__':
    print("--- Running VectorMemory module simulation ---")
    
    mem = VectorMemory(max_size=5, vector_dim=3) # Small memory for easy testing
    
    # 1. Add some vectors
    print("1. Adding vectors to memory.")
    mem.add_vector(np.array([1.0, 0.0, 0.0]), metadata={"color": "red"}) # 'Red'
    mem.add_vector(np.array([0.0, 1.0, 0.0]), metadata={"color": "green"}) # 'Green'
    mem.add_vector(np.array([0.0, 0.0, 1.0]), metadata={"color": "blue"}) # 'Blue'
    
    # 2. Query for similar vectors
    print("2. Querying for similar vectors.")
    query = np.array([0.9, 0.1, 0.1]) # Similar to 'Red'
    results = mem.query_similar(query, top_k=2)
    print(f"Query: {query}")
    for vec, sim, meta in results:
        print(f"  - Vector: {vec}, Similarity: {sim:.3f}, Metadata: {meta}")

    query2 = np.array([0.1, 0.8, 0.2]) # Similar to 'Green'
    results2 = mem.query_similar(query2, top_k=1)
    print(f"Query: {query2}")
    for vec, sim, meta in results2:
        print(f"  - Vector: {vec}, Similarity: {sim:.3f}, Metadata: {meta}")

    # 3. Test bounded size (eviction)
    print("3. Testing bounded size (eviction of oldest entry).")
    mem.add_vector(np.array([1.0, 1.0, 0.0]), metadata={"color": "yellow"}) # 'Yellow' - size is 4
    mem.add_vector(np.array([0.0, 1.0, 1.0]), metadata={"color": "cyan"}) # 'Cyan' - size is 5
    mem.add_vector(np.array([1.0, 0.0, 1.0]), metadata={"color": "magenta"}) # 'Magenta' - 'Red' should be evicted
    
    print(f"Current memory size: {mem.get_current_size()}")
    all_vectors = mem.get_all_vectors()
    print("All vectors in memory (oldest first):")
    for vec in all_vectors:
        print(f"  - {vec}")
    
    # Check if 'Red' is gone (its similarity to query_red should not be 1.0)
    query_red = np.array([1.0, 0.0, 0.0])
    results_red = mem.query_similar(query_red, top_k=1)
    print(f"Query for original 'Red' ({query_red}), closest vector has similarity: {results_red[0][1]:.3f}")
    assert results_red[0][1] < 1.0 # Should no longer be a perfect match if Red was evicted
