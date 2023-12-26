import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

from models.embedder.multilingual_embedder import MultilingualEmbedder
from models.embedder.openai_embedder import OpenAIEmbedder

def get_embedder(model_name='multilingual-e5-large'):
    if model_name == 'multilingual-e5-large':
        return MultilingualEmbedder()
    elif model_name == 'openai':
        return OpenAIEmbedder()
    else:
        raise NotImplementedError