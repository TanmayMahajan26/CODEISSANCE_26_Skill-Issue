import os
import sys

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.embeddings import EmbeddingService

def test_embeddings():
    text = "Test String"
    embedding = EmbeddingService.generate_embedding(text)
    
    assert isinstance(embedding, list)
    assert len(embedding) == 384
    assert isinstance(embedding[0], float)

if __name__ == "__main__":
    test_embeddings()
    print("EmbeddingService tests passed!")
