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
import glob
import pickle
import argparse
import threading
from datetime import datetime

import tqdm
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from sklearn.metrics.pairwise import cosine_similarity

from database.knowledge_graph.retriever import KG_retriever, KG_retriever_GPT

current_file_folder_path = os.path.dirname(os.path.abspath(__file__))
save_dir = os.path.join(current_file_folder_path, '../test_data')

class KnowledgeGraphDataBase:
    G_dict = {}
    retrieval = KG_retriever_GPT(k_list=[2, 2])

    def __init__(self, save_dir=save_dir):
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)
        self.load_most_recent_graph()

    def make_graph_constructor(self, project_id):
        self.G_dict[project_id] = GraphConstructor()

    def add_document_from_json(self, json_path, project_id):
        if project_id not in self.G_dict:
            self.make_graph_constructor(project_id)
        self.G_dict[project_id].add_json_file(json_path)

    def visualize_graph(self, project_id):
        self.G_dict[project_id].visualize_graph()

    def save_graph_data(self):
        filename = f"knowledge_graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        filepath = os.path.join(self.save_dir, filename)
        dict_to_save = {pid: gc.to_dict() for pid, gc in self.G_dict.items()}
        with open(filepath, 'wb') as file:
            pickle.dump(dict_to_save, file)
        print(f"Graph data saved to {filepath}")
        self.cleanup_old_files()

    def load_most_recent_graph(self):
        files = glob.glob(os.path.join(self.save_dir, 'knowledge_graph_*.pkl'))
        if files:
            latest_file = max(files, key=os.path.getctime)
            self.load_graph_data(latest_file)

    def load_graph_data(self, filename):
        filepath = os.path.join(self.save_dir, filename)
        with open(filepath, 'rb') as file:
            loaded_dict = pickle.load(file)
        self.G_dict = {pid: GraphConstructor.from_dict(gc_dict) for pid, gc_dict in loaded_dict.items()}
        print(f"Graph data loaded from {filepath}")

    def delete_project(self, project_id):
        del self.G_dict[project_id]

    def delete_document(self, file_uuid, project_id):
        self.G_dict[project_id].delete_document(file_uuid)
        
    def cleanup_old_files(self):
        file_pattern = "knowledge_graph_"
        
        # List all files in the given directory
        files = os.listdir(self.save_dir)
        
        # Filter and sort files based on the pattern and their timestamp
        matched_files = [f for f in files if f.startswith(file_pattern)]
        matched_files.sort(key=lambda x: datetime.strptime(x[len(file_pattern):-4], '%Y%m%d_%H%M%S'), reverse=True)
        
        # Keep only the most recent 5 files, delete the rest
        for file_to_delete in matched_files[5:]:
            os.remove(os.path.join(self.save_dir, file_to_delete))
            print(f"Deleted old graph files: {file_to_delete}")

    def __str__(self, project_id=None):
        if project_id:
            output.append(f"Project ID: {project_id}")
            output.append(str(graph_constructor[project_id]))
        else:
            output = []
            for project_id, graph_constructor in self.G_dict.items():
                output.append(f"Project ID: {project_id}")
                output.append(str(graph_constructor))
        return '\n\n'.join(output)

    def get_chunk_num(self, project_id, file_uuid=None):
        return self.G_dict[project_id].get_chunk_num(file_uuid)

    def search(self, query, project_id, file_uuid=None):
        if file_uuid is not None:
            raise NotImplementedError("search by file_uuid is not implemented yet")
        return self.retrieval.retrieve(query, self.G_dict[project_id])

class GraphConstructor:
    def __init__(self):
        self.G = nx.DiGraph()
        self.file_uuid_to_uuid = {}
        self.uuid_to_file_uuid = {}
        self.uuid_to_node = {}
        self.uuid_list = []
        self.embedding_list = []
        self.child_embeddings_list = []
        self.lock = threading.Lock() # 동시에 add_data_to_graph가 실행되지 않도록 lock
        self.token_filter_length = 100

    def add_json_file(self, json_path):
        json_data = self.read_json_file(json_path)
        file_uuid = json_data['file_uuid']
        data_list = json_data['data'] # chunk list
        with self.lock:
            for data in tqdm.tqdm(data_list):
                self.add_data_to_graph(file_uuid, data)

    def read_json_file(self, json_path):
        with open(json_path, encoding='utf-8') as f:
            return json.load(f)

    def add_data_to_graph(self, file_uuid, data, k_knn=5):
        if not self.embedding_list: # add first node
            self.add_first_node(file_uuid, data)
        else:
            self.add_node(file_uuid, data, k_knn)

    def add_first_node(self, file_uuid, data):
        if data['token_num'] < self.token_filter_length:
            return
        new_node_uuid = data['uuid']
        child_embeddings = data['child_embeddings']
        
        if file_uuid not in self.file_uuid_to_uuid:
            self.file_uuid_to_uuid[file_uuid] = []

        self.file_uuid_to_uuid[file_uuid].append(new_node_uuid)
        self.uuid_to_file_uuid[new_node_uuid] = file_uuid
        self.uuid_to_node[new_node_uuid] = data
        self.uuid_list.append(new_node_uuid)
        self.embedding_list.append(data['embedding'])
        self.child_embeddings_list.append(child_embeddings)
    
    def add_node(self, file_uuid, data, k_knn):
        if data['token_num'] < self.token_filter_length:
            return
        new_node_uuid = data['uuid']
        new_embedding = np.array(data['embedding']).reshape(1, -1)
        child_embeddings = np.array(data['child_embeddings'])

        existing_embeddings = np.array(self.embedding_list)
        similarities = self.calculate_similarities(new_embedding, existing_embeddings)
        self.update_graph(new_node_uuid, similarities, k_knn)

        if file_uuid not in self.file_uuid_to_uuid:
            self.file_uuid_to_uuid[file_uuid] = []

        self.file_uuid_to_uuid[file_uuid].append(new_node_uuid)
        self.uuid_to_file_uuid[new_node_uuid] = file_uuid
        self.uuid_to_node[new_node_uuid] = data
        self.uuid_list.append(new_node_uuid)
        self.embedding_list.append(data['embedding'])
        self.child_embeddings_list.append(child_embeddings)

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
            self.G.remove_edge(node_uuid, neighbors[-1])

    def delete_document(self, file_uuid):
        with self.lock:
            if file_uuid not in self.file_uuid_to_uuid:
                print(f"No nodes associated with file_uuid {file_uuid}")
                return
            
            node_uuids_to_delete = self.file_uuid_to_uuid[file_uuid]

            for node_uuid in node_uuids_to_delete:
                if self.G.has_node(node_uuid):
                    self.G.remove_node(node_uuid)

                if node_uuid in self.uuid_to_node:
                    del self.uuid_to_node[node_uuid]

                if node_uuid in self.uuid_to_file_uuid:
                    del self.uuid_to_file_uuid[node_uuid]

                # Remove node uuid and corresponding embedding by index
                if node_uuid in self.uuid_list:
                    idx = self.uuid_list.index(node_uuid)
                    self.uuid_list.pop(idx)
                    self.embedding_list.pop(idx)
                    self.child_embeddings_list.pop(idx)

            # Remove the entry from file_uuid_to_uuid
            del self.file_uuid_to_uuid[file_uuid]

    def get_chunk_num(self, file_uuid=None):
        if file_uuid:
            chunk_num = 0
            for uuid in file_uuid:
                chunk_num += len(self.file_uuid_to_uuid.get(uuid, []))
            return chunk_num
        else:
            return len(self.uuid_list)

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

    def __str__(self):
        output = []
        for node_uuid in self.G.nodes():
            neighbors = self.G[node_uuid]
            connections = []
            for neighbor_uuid, attrs in neighbors.items():
                weight = attrs['weight']
                neighbor_text = self.uuid_to_node.get(neighbor_uuid, "Unknown").get('text', "Unknown")
                connections.append(f"{neighbor_text} (Weight: {weight:.2f})")
            node_text = self.uuid_to_node.get(node_uuid, "Unknown").get('text', "Unknown")
            connections_text = '\n'.join(connections)
            output.append(f"Node '{node_text}' \nconnected to: {connections_text}")
        return '\n\n'.join(output)
    
    def to_dict(self):
        return {
            "G": nx.node_link_data(self.G),
            'file_uuid_to_uuid': self.file_uuid_to_uuid,
            'uuid_to_file_uuid': self.uuid_to_file_uuid,
            "uuid_to_node": self.uuid_to_node,
            "uuid_list": self.uuid_list,
            "embedding_list": self.embedding_list,
            "child_embeddings_list": self.child_embeddings_list,
        }

    @staticmethod
    def from_dict(data):        
        gc = GraphConstructor()
        gc.G = nx.node_link_graph(data["G"])
        gc.file_uuid_to_uuid = data["file_uuid_to_uuid"]
        gc.uuid_to_file_uuid = data["uuid_to_file_uuid"]
        gc.uuid_to_node = data["uuid_to_node"]
        gc.uuid_list = data["uuid_list"]
        gc.embedding_list = data["embedding_list"]
        gc.child_embeddings_list = data["child_embeddings_list"]
        return gc

# example usage
# python graph_construct.py --json_path "../../modules/test_data/6feb401c-8ab2-4440-8671-fad5e7e1f115.json" --project_id 1 --query "전기차와 하이브리드차의 규모"
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--json_path', type=str, default='../../modules/test_data/6feb401c-8ab2-4440-8671-fad5e7e1f115.json')
    parser.add_argument('--project_id', type=int, default=1)
    parser.add_argument('--query', type=str, default='전기차와 하이브리드차의 규모')
    args = parser.parse_args()

    db = KnowledgeGraphDataBase()

    # ------ add data ------ #
    project_id = args.project_id
    db.add_document_from_json(args.json_path, project_id)

    # ------ visualize data ------ #
    db.visualize_graph(project_id)

    # ------ save graph ------ #
    db.save_graph_data()

    # ------ load graph ------ #
    db.load_most_recent_graph()

    # ------ delete data ------ #
    delete_uuid = '6feb401c-8ab2-4440-8671-fad5e7e1f115'
    db.delete_document(delete_uuid, project_id=project_id)
    print(len(db.G_dict[project_id].uuid_list))

    # ------ search ------ #
    print(db.search(args.query, project_id))