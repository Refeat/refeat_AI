import tiktoken

class OpenAITokenizer:
    def __init__(self):
        self.encoding = tiktoken.get_encoding('cl100k_base')
    
    def get_encoding(self, text):
        return self.encoding.encode(text)

    def get_token_num(self, text, prefix=None):
        tokenized_text = self.get_encoding(text)
        return len(tokenized_text)