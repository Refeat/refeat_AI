from sentence_transformers import SentenceTransformer

class MultilingualEmbedding:
    def __init__(self, model='intfloat/multilingual-e5-large', device='cpu'):
        self.embedding_model = SentenceTransformer(model, device=device)
        self.model = model
        # self.dimensions = 768
        self.dimensions = 1024

    def get_embedding(self, query, prefix='query: '):
        if isinstance(query, str):
            try:
                query = prefix + query
                return self.embedding_model.encode(query, normalize_embeddings=True).tolist()
            except Exception as e:
                print(e)
                return None
        elif isinstance(query, list):
            try:
                query = [prefix + q for q in query]
                return self.embedding_model.encode(query, normalize_embeddings=True).tolist()
            except Exception as e:
                print(e)
                return None