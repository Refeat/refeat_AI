import json
import argparse

import matplotlib.pyplot as plt
import networkx as nx
from sklearn.metrics.pairwise import cosine_similarity

class ChunksGraph:
    def __init__(self, data, cosine_sim_threshold=0.2, filter_text_length=50):
        self.cosine_sim_threshold = cosine_sim_threshold
        self.filter_text_length = filter_text_length
        self.short_text_nodes = set()
        self.data = data
        self.graph = self.generate_graph(data)

    def generate_graph(self, data):
        # embeddings 추출 및 코사인 유사도 계산
        embeddings = [chunk['embedding'] for chunk in data]
        cosine_sim_matrix = cosine_similarity(embeddings)

        # 그래프 초기화
        G = nx.Graph()

        # 노드와 엣지 추가
        self.add_nodes(G, data)
        self.add_edges(G, cosine_sim_matrix)

        return G

    def add_nodes(self, G, data):
        for chunk in data:
            G.add_node(chunk['uuid'])
            if chunk['token_num'] < self.filter_text_length:
                self.short_text_nodes.add(chunk['uuid'])

    def add_edges(self, G, cosine_sim_matrix):
        uuids = [chunk['uuid'] for chunk in self.data]  # Extract UUIDs from the data

        for i in range(len(cosine_sim_matrix)):
            for j in range(i + 1, len(cosine_sim_matrix)):
                # Use UUIDs for nodes
                uuid_i = uuids[i]
                uuid_j = uuids[j]

                if (uuid_i not in self.short_text_nodes) and (uuid_j not in self.short_text_nodes):
                    if cosine_sim_matrix[i][j] >= self.cosine_sim_threshold:
                        G.add_edge(uuid_i, uuid_j, weight=float(cosine_sim_matrix[i][j]))
    
    def visualize_graph(self):
        plt.figure(figsize=(20, 8))
        plt.title("Graph Visualization")
        pos = nx.spring_layout(self.graph)

        nx.draw_networkx_nodes(self.graph, pos, node_size=700)
        nx.draw_networkx_edges(self.graph, pos, edgelist=self.graph.edges(), width=1.5)

        node_labels = {node: node for node in self.graph.nodes()}
        nx.draw_networkx_labels(self.graph, pos, labels=node_labels, font_size=8)

        edge_labels = nx.get_edge_attributes(self.graph, 'weight')
        edge_labels = {key: f'{value:.2f}' for key, value in edge_labels.items()}
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels, font_color='red')

        plt.show()
        plt.savefig('graph.png')

# example usage
# python single_file_chunks_graph.py --data_path ../../moduels/test_data/a6e594a6-712c-4e1e-be4a-667dabfee9ca.json
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_path', type=str, default='../../modules/test_data/9d1e839b-9361-4b16-8a73-0252f28e742f.json')
    args = parser.parse_args()

    with open(args.data_path, 'r') as f:
        data = json.load(f)
    graph = ChunksGraph(data['data'])
    graph.visualize_graph()