import tiktoken

class OpenAITokenizer:
    def __init__(self):
        self.encoding = tiktoken.get_encoding('cl100k_base')
    
    def get_encoding(self, text):
        if isinstance(text, str):
            return self.encoding.encode(text)
        elif isinstance(text, list):
            return self.encoding.encode_batch(text)

    def get_token_num(self, text, prefix=None):
        tokenized_text = self.get_encoding(text)
        if isinstance(text, str):
            return len(tokenized_text)
        elif isinstance(text, list):
            return [len(token) for token in tokenized_text]
        
    def get_decoding(self, token):
        if isinstance(token[0], list):
            return self.encoding.decode_batch(token)
        elif isinstance(token[0], int):
            return self.encoding.decode(token)
    
if __name__ == '__main__':
    text = 'hello world'
    tokenizer = OpenAITokenizer()
    print(tokenizer.get_encoding(text))
    print(tokenizer.get_token_num(text))
    print(tokenizer.get_decoding(tokenizer.get_encoding(text)))