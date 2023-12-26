from transformers import AutoTokenizer

class MultilingualTokenizer:
    def __init__(self, model_name='intfloat/multilingual-e5-large'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    def get_encoding(self, text):
        return self.tokenizer(text)['input_ids']
    
    def get_token_num(self, text):
        tokenized_text = self.get_encoding(text)
        return len(tokenized_text)
