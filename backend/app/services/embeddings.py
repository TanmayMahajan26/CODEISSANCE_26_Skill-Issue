from sentence_transformers import SentenceTransformer

class EmbeddingService:
    _model = None

    @classmethod
    def get_model(cls) -> SentenceTransformer:
        if cls._model is None:
            # Initialize model globally to avoid reloading on each request
            # all-MiniLM-L6-v2 provides a good balance of performance and quality (384 dimensions)
            cls._model = SentenceTransformer('all-MiniLM-L6-v2')
        return cls._model

    @classmethod
    def generate_embedding(cls, text: str) -> list[float]:
        if not text:
            return [0.0] * 384
        
        model = cls.get_model()
        # Encode returns a numpy array, convert to standard Python list of floats
        embedding = model.encode(text)
        return embedding.tolist()
