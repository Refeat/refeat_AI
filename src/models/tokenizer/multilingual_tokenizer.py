import argparse

from transformers import AutoTokenizer

class MultilingualTokenizer:
    def __init__(self, model_name='intfloat/multilingual-e5-large'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    def __call__(self, text):
        return self.get_encoding(text)

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

# example usage
# single text tokenization
# python multilingual_tokenizer.py --text "Hello, my dog is cute"
# multiple text tokenization
# python multilingual_tokenizer.py --text_list "Hello, my dog is cute" --text_list "What is your name?"
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--text', type=str, default='')
    parser.add_argument('--text_list', type=str, action='append', default=[])
    args = parser.parse_args()

    multilingual_tokenizer = MultilingualTokenizer()

    # ------ single text tokenization ------ #
    if args.text:
        tokenized_text = multilingual_tokenizer.get_encoding(args.text)
        print(f'Tokenized text: {tokenized_text}')
        print(f'Tokenized text length: {len(tokenized_text)}')

    # ------ multiple text tokenization ------ #
    if args.text_list:
        tokenized_text = multilingual_tokenizer.get_encoding(args.text_list)
        print(f'Tokenized text: {tokenized_text}')