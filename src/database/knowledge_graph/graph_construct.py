import os
import sys
# project root path를 추가
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

# openai api key를 추가
from utils import add_api_key
add_api_key()

import json
import uuid
import glob
import pickle
from datetime import datetime

import tqdm
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from sklearn.metrics.pairwise import cosine_similarity

class KnowledgeGraphDataBase:
    def __init__(self, save_dir='../test_data'):
        self.G_dict = {}
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)
        self.load_most_recent_graph()

    def make_graph_constructor(self, project_id=-1):
        self.G_dict[project_id] = GraphConstructor()

    def add_document_from_json(self, json_path, project_id=-1):
        if project_id not in self.G_dict:
            self.make_graph_constructor(project_id)
        self.G_dict[project_id].add_json_file(json_path)

    def visualize_graph(self, project_id=-1):
        self.G_dict[project_id].visualize_graph()

    def save_graph_data(self):
        filename = f"knowledge_graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        filepath = os.path.join(self.save_dir, filename)
        with open(filepath, 'wb') as file:
            pickle.dump(self.G_dict, file)

    def load_most_recent_graph(self):
        files = glob.glob(os.path.join(self.save_dir, 'knowledge_graph_*.pkl'))
        if files:
            latest_file = max(files, key=os.path.getctime)
            self.load_graph_data(latest_file)

    def load_graph_data(self, filename):
        filepath = os.path.join(self.save_dir, filename)
        with open(filepath, 'rb') as file:
            self.G_dict = pickle.load(file)

    def delete_project(self, project_id):
        del self.G_dict[project_id]

class GraphConstructor:
    def __init__(self):
        self.G = nx.DiGraph()
        self.uuid_to_node = {}
        self.node_to_uuid = {}
        self.uuid_list = []
        self.embedding_list = []

    def add_json_file(self, json_path):
        data_list = self.read_json_file(json_path)['data'] # chunk list
        for data in tqdm.tqdm(data_list):
            self.add_data_to_graph(data)

    def read_json_file(self, json_path):
        with open(json_path, encoding='utf-8') as f:
            return json.load(f)

    def add_data_to_graph(self, data, k_knn=5):
        if not self.embedding_list: # add first node
            self.add_first_node(data)
        else:
            self.add_node(data, k_knn)

    def add_first_node(self, data):
        new_node_uuid = uuid.uuid4()
        new_embedding = np.array(data['embedding']).reshape(1, -1)
        
        self.uuid_to_node[new_node_uuid] = data['text']
        self.uuid_list.append(new_node_uuid)
        self.node_to_uuid[data['text']] = new_node_uuid
        self.embedding_list.append(new_embedding[0])
        return new_node_uuid
    
    def add_node(self, data, k_knn):
        new_node_uuid = uuid.uuid4()
        new_embedding = np.array(data['embedding']).reshape(1, -1)

        existing_embeddings = np.array(self.embedding_list)
        similarities = self.calculate_similarities(new_embedding, existing_embeddings)
        self.update_graph(new_node_uuid, similarities, k_knn)

        self.uuid_to_node[new_node_uuid] = data['text']
        self.node_to_uuid[data['text']] = new_node_uuid
        self.uuid_list.append(new_node_uuid)
        self.embedding_list.append(new_embedding[0])

    def calculate_similarities(self, new_embedding, existing_embeddings):
        return cosine_similarity(new_embedding, existing_embeddings)[0]

    def update_graph(self, new_node_uuid, similarities, k_knn):
        num_neighbors = min(len(self.uuid_to_node), k_knn)

        # Retrieve the indices of the top k similarity score nodes
        top_k_indices = np.argsort(similarities)[-num_neighbors:]

        # Retrieve the UUIDs for these indices
        top_k_uuids = [self.uuid_list[i] for i in top_k_indices]

        for i, neighbor_uuid in enumerate(top_k_uuids):
            similarity_score = similarities[top_k_indices[i]]
            self.G.add_edge(new_node_uuid, neighbor_uuid, weight=similarity_score)
            self.G.add_edge(neighbor_uuid, new_node_uuid, weight=similarity_score)
            self.trim_neighbors(neighbor_uuid, k_knn)

    def trim_neighbors(self, node_uuid, k_knn):
        # 새로운 노드가 추가되면 기존 노드의 이웃 노드들 중 가장 유사도가 낮은 노드를 제거
        neighbors = list(self.G.neighbors(node_uuid))
        if len(neighbors) > k_knn:
            neighbors.sort(key=lambda x: self.G[node_uuid][x]['weight'], reverse=True)
            # print neightbors weight score
            self.G.remove_edge(node_uuid, neighbors[-1])

    def visualize_graph(self):
        font_name = 'Malgun Gothic'
        plt.rc('font', family=font_name)
        plt.figure(figsize=(20, 8))
        plt.title("Graph Visualization")
        pos = nx.spring_layout(self.G)

        nx.draw_networkx_nodes(self.G, pos, node_size=700)
        nx.draw_networkx_edges(self.G, pos, edgelist=self.G.edges(), width=1.5)

        node_labels = {node: node for node in self.G.nodes()}
        nx.draw_networkx_labels(self.G, pos, labels=node_labels, font_size=12, font_family=font_name)

        edge_labels = nx.get_edge_attributes(self.G, 'weight')
        edge_labels = {key: f'{value:.2f}' for key, value in edge_labels.items()}
        nx.draw_networkx_edge_labels(self.G, pos, edge_labels=edge_labels, font_color='red', font_family=font_name)

        plt.show()