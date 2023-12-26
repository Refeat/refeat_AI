from transformers import AutoTokenizer

class MultilingualTokenizer:
    def __init__(self, model_name='intfloat/multilingual-e5-large'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    def get_encoding(self, text):
        if isinstance(text, str):
            return self.tokenizer(text)['input_ids'][1:-1]
        elif isinstance(text, list):
            return [token[1:-1] for token in self.tokenizer(text)['input_ids']]
    
    def get_token_num(self, text):
        tokenized_text = self.get_encoding(text)
        if isinstance(text, str):
            return len(tokenized_text)
        elif isinstance(text, list):
            return [len(token) for token in tokenized_text]