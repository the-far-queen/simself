from typing import List, Dict, Any, Tuple
import re # For basic sentence splitting
import numpy as np # For simulating embeddings
import uuid # For chunk IDs
import time # For timestamp in chunk metadata

class SemanticChunker:
    """
    Implements a Pre-Token Semantic Chunking Layer (PT-SCL),
    as described in CHUNKING.md.
    It identifies and extracts coherent semantic units (chunks) from raw input,
    prior to any traditional tokenization.
    """
    def __init__(self, min_sentence_length: int = 5, keyword_density_threshold: float = 0.2):
        self.min_sentence_length = min_sentence_length
        self.keyword_density_threshold = keyword_density_threshold
        self.known_keywords: Dict[str, List[str]] = { # Example keywords by domain
            "general": ["coherence", "emergence", "pattern", "system", "self", "meaning", "knowledge", "truth", "ethics"],
            "robotics": ["grasp", "move", "actuator", "sensor", "collision", "robot", "plan", "execute"],
            "ethics": ["truth", "responsibility", "harm", "compassion", "value", "ethical", "moral"]
        }
        print("SemanticChunker: Initialized.")

    def _split_into_sentences(self, text: str) -> List[str]:
        """Basic sentence splitting."""
        # This is a very simple regex; real NLP would use more robust methods.
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s for s in sentences if len(s.split()) >= self.min_sentence_length]

    def _calculate_keyword_density(self, sentence: str, domain: str = "general") -> float:
        """Calculates keyword density for a sentence against known keywords."""
        words = set(sentence.lower().split())
        keywords = set(self.known_keywords.get(domain, self.known_keywords["general"]))
        
        common_keywords = words.intersection(keywords)
        if not words:
            return 0.0
        return len(common_keywords) / len(words)

    def _generate_semantic_embedding(self, chunk_text: str) -> np.ndarray:
        """Simulates generating a semantic embedding for a chunk."""
        # In a real system, this would involve an LLM or embedding model.
        # For simulation, a simple hash-based vector.
        seed = sum(ord(c) for c in chunk_text) % 1000 # Simple hash seed
        np.random.seed(seed)
        return np.random.rand(128) # Default embedding dimension

    def chunk_text(self, raw_text: str, domain: str = "general") -> List[Dict[str, Any]]:
        """
        Identifies and extracts semantic chunks from raw text.
        """
        sentences = self._split_into_sentences(raw_text)
        chunks: List[Dict[str, Any]] = []
        current_chunk_sentences: List[str] = []
        
        for sentence in sentences:
            density = self._calculate_keyword_density(sentence, domain)
            
            # If a sentence has high keyword density, it likely starts a new semantic chunk
            # or significantly contributes to the current one.
            # We finalize previous chunk if density is high and there's content.
            if density >= self.keyword_density_threshold and current_chunk_sentences:
                chunks.append(self._finalize_chunk(current_chunk_sentences, domain))
                current_chunk_sentences = [] # Start new chunk
            current_chunk_sentences.append(sentence)
        
        if current_chunk_sentences: # Finalize any remaining sentences
            chunks.append(self._finalize_chunk(current_chunk_sentences, domain))
        
        return chunks

    def _finalize_chunk(self, sentences: List[str], domain: str) -> Dict[str, Any]:
        """Combines sentences into a chunk and generates its metadata."""
        full_chunk_text = " ".join(sentences)
        embedding = self._generate_semantic_embedding(full_chunk_text)
        
        return {
            "id": str(uuid.uuid4()),
            "text": full_chunk_text,
            "embedding": embedding.tolist(), # Convert to list for JSON serialization
            "domain": domain,
            "sentence_count": len(sentences),
            "timestamp": time.time()
        }

if __name__ == '__main__':
    print("--- Running SemanticChunker module simulation ---")
    
    chunker = SemanticChunker(min_sentence_length=4, keyword_density_threshold=0.15)
    
    long_text = """
    The FieldCore system aims for universal coherence. Emergence is a key property of complex adaptive systems.
    Understanding patterns in data is crucial for system stability. Self-organization is observed in many networks.
    The robot needs to grasp the mug. Move the arm slowly to avoid collision. Ethical considerations guide our actions.
    Truth is paramount in all decision-making processes, ensuring agency requires responsibility.
    """

    print("
--- Chunking general text ---")
    chunks = chunker.chunk_text(long_text, domain="general")
    for i, chunk in enumerate(chunks):
        print(f"
Chunk {i+1} (ID: {str(chunk['id'])[:4]}):")
        print(f"  Text: {chunk['text']}")
        print(f"  Domain: {chunk['domain']}")
        print(f"  Embedding (first 3): {chunk['embedding'][:3]}...")

    print("
--- Chunking robotics-focused text ---")
    robot_text = """
    The robot must grasp the tool. Ensure no collision with the environment.
    Move the end effector to the target position. Sensors provide feedback.
    """
    robot_chunks = chunker.chunk_text(robot_text, domain="robotics")
    for i, chunk in enumerate(robot_chunks):
        print(f"
Chunk {i+1} (ID: {str(chunk['id'])[:4]}):")
        print(f"  Text: {chunk['text']}")
        print(f"  Domain: {chunk['domain']}")
