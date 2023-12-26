import os
import configparser
config = configparser.ConfigParser()
current_path = os.path.dirname(os.path.abspath(__file__))
config.read(os.path.join(current_path, '../../../.secrets.ini'))
openai_api_key = config['OPENAI']['OPENAI_API_KEY']
os.environ.update({'OPENAI_API_KEY': openai_api_key})

from openai import OpenAI

class OpenAIEmbedding:
    def __init__(self, model="text-embedding-ada-002"):
        self.embedding_model = OpenAI(api_key=openai_api_key).embeddings
        self.model = model
        self.dimensions = 1536

    def get_embedding(self, query, prefix=None):
        if isinstance(query, str):
            try:
                embedding = self.embedding_model.create(input = [query], model=self.model).data[0].embedding
            except Exception as e:
                print(e)
                embedding = None
        elif isinstance(query, list):
            try:
                # empty string의 index를 기록해두고, embedding 후 결과에 대해 empty string의 index에 해당하는 embedding을 추가
                empty_string_index = [i for i, q in enumerate(query) if len(q.strip()) == 0]
                query = [q for q in query if len(q) > 0]
                embedding = self.embedding_model.create(input = query, model=self.model).data
                embedding = [e.embedding for e in embedding]
                for i in empty_string_index:
                    embedding.insert(i, None)
            except Exception as e:
                print(e)
                return None
        return embedding
    
if __name__ == '__main__':
    openai_embedding = OpenAIEmbedding()
    # print(len(openai_embedding.get_embedding('Hello, my dog is cute')))
    print(len(openai_embedding.get_embedding(['Hello, my dog is cute', 'Hello, my cat is cute'])))
    print(len(openai_embedding.get_embedding(['Hello, my dog is cute', 'Hello, my cat is cute'])[0]))