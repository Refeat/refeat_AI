import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

import json
import argparse

import networkx as nx

from models.text_ranker.single_file_chunks_graph import ChunksGraph

class TextRanker:
    def __init__(self):
        pass
    
    def get_text_rank(self, data):
        graph = self.generate_graph(data)
        scores = nx.pagerank(graph.graph)

        sorted_chunks = sorted(data, key=lambda chunk: scores[chunk['uuid']], reverse=True)
        return [chunk['text'] for chunk in sorted_chunks]

    def generate_graph(self, data):
        return ChunksGraph(data)
    
# example usage
# python text_ranker.py --data_path ../../modules/test_data/944d4a8c-118d-4eb3-b1d4-f3d8b123b49d.json
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_path', type=str, default='../../modules/test_data/d9277655-3701-4099-b76c-7b1dd5c2018e.json')
    args = parser.parse_args()

    with open(args.data_path, 'r') as f:
        data = json.load(f)
    
    text_ranker = TextRanker()
    ranked_chunks = text_ranker.get_text_rank(data)
    for idx, chunk in enumerate(ranked_chunks):
        print('-'*10, 'rank', idx+1, '-'*10)
        print(chunk)