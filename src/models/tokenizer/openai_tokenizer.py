import argparse

import tiktoken

class OpenAITokenizer:
    def __init__(self):
        self.encoding = tiktoken.get_encoding('cl100k_base')

    def __call__(self, text):
        return self.get_encoding(text)
    
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

# example usage
# single text tokenization
# python openai_tokenizer.py --text "Hello, my dog is cute"
# multiple text tokenization
# python openai_tokenizer.py --text_list "Hello, my dog is cute" --text_list "What is your name?"
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--text', type=str, default='')
    parser.add_argument('--text_list', type=str, action='append', default=[])
    args = parser.parse_args()

    openai_tokenizer = OpenAITokenizer()

    # ------ single text tokenization ------ #
    if args.text:
        tokenized_text = openai_tokenizer.get_encoding(args.text)
        print(f'Tokenized text: {tokenized_text}')
        print(f'Tokenized text length: {len(tokenized_text)}')

    # ------ multiple text tokenization ------ #
    if args.text_list:
        tokenized_text = openai_tokenizer.get_encoding(args.text_list)
        print(f'Tokenized text: {tokenized_text}')