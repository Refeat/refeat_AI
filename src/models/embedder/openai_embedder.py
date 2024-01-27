import os
import configparser
config = configparser.ConfigParser()
current_path = os.path.dirname(os.path.abspath(__file__))
config.read(os.path.join(current_path, '../../../.secrets.ini'))
openai_api_key = config['OPENAI']['OPENAI_API_KEY']
os.environ.update({'OPENAI_API_KEY': openai_api_key})

import argparse

from openai import OpenAI

class OpenAIEmbedder:
    def __init__(self, model="text-embedding-3-large"):
        self.embedding_model = OpenAI(api_key=openai_api_key).embeddings
        self.model = model
        self.dimensions = 3072

    def get_embedding(self, query, prefix=None):
        if isinstance(query, str):
            try:
                embedding = self.embedding_model.create(input = [query], model=self.model).data[0].embedding
            except Exception as e:
                print(e)
                embedding = None
        elif isinstance(query, list):
            try:
                # empty string의 index를 기록해두고, embedding을 계산한 후에 해당 index에 None을 삽입
                empty_string_index = [i for i, q in enumerate(query) if len(q.strip()) == 0]
                query = [q for q in query if len(q) > 0]
                embedding = self.embedding_model.create(input = query, model=self.model).data
                embedding = [e.embedding for e in embedding]
                for i in empty_string_index:
                    embedding.insert(i, None)
            except Exception as e:
                print(e)
                return None
        else:
            raise ValueError(f'query should be str or list. but {type(query)} is given')
        return embedding

# example usage
# single text embedding
# python openai_embedder.py --text "Hello, my dog is cute"
# multiple text embedding
# python openai_embedder.py --text_list "Hello, my dog is cute" --text_list "What is your name?"
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--text', type=str, default='')
    parser.add_argument('--text_list', type=str, action='append', default=[])
    args = parser.parse_args()

    openai_embedder = OpenAIEmbedder()
    
    # ------ single text embedding ------ #
    if args.text:
        embedding = openai_embedder.get_embedding(args.text)    
        print(f'Dimension of embedding: {len(embedding)}')
        print(f'First 5 values of embedding: {embedding[:5]}')

    # ------ multiple text embedding ------ #
    if args.text_list:
        embedding = openai_embedder.get_embedding(args.text_list)    
        print(f'Dimension of embedding: {len(embedding[0])}')
        for idx, e in enumerate(embedding):
            print(f'{idx+1} text First 5 values of embedding: {e[:5]}')

