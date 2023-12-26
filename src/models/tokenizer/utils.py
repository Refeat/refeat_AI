import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

from models.tokenizer.multilingual_tokenizer import MultilingualTokenizer
from models.tokenizer.openai_tokenizer import OpenAITokenizer

def get_tokenizer(model_name='multilingual-e5-large'):
    if model_name == 'multilingual-e5-large':
        return MultilingualTokenizer()
    elif model_name == 'openai':
        return OpenAITokenizer()
    else:
        raise NotImplementedError