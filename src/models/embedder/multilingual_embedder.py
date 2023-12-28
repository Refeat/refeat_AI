import argparse

from sentence_transformers import SentenceTransformer

class MultilingualEmbedder:
    def __init__(self, model='intfloat/multilingual-e5-large', device='cpu'):
        self.embedding_model = SentenceTransformer(model, device=device)
        self.model = model
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
            
# example usage
# single text embedding
# python multilingual_embedder.py --text "Hello, my dog is cute"
# multiple text embedding
# python multilingual_embedder.py --text_list "Hello, my dog is cute" --text_list "What is your name?"
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--text', type=str, default='')
    parser.add_argument('--text_list', type=str, action='append', default=[])
    args = parser.parse_args()

    multilingual_embedder = MultilingualEmbedder()
    
    # ------ single text embedding ------ #
    if args.text:
        embedding = multilingual_embedder.get_embedding(args.text)    
        print(f'Dimension of embedding: {len(embedding)}')
        print(f'First 5 values of embedding: {embedding[:5]}')

    # ------ multiple text embedding ------ #
    if args.text_list:
        embedding = multilingual_embedder.get_embedding(args.text_list)    
        print(f'Dimension of embedding: {len(embedding)}')
        for e in embedding:
            print(f'First 5 values of embedding: {e[:5]}')