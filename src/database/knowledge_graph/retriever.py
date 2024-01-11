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

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from models.embedder.openai_embedder import OpenAIEmbedder
from models.llm.chain import MakeFakeEvidenceChain

class KNN_Retrieval:
    def __init__(self):
        pass

    @classmethod
    def retrieve(self, query_embedding, graph_constructor, k, visited_nodes, embeddings=None, uuids=None):
        if embeddings is None:
            embeddings = np.array(graph_constructor.embedding_list)
            uuids = graph_constructor.uuid_list

        query_emb = np.array(query_embedding).reshape(1, -1)
        similarities = cosine_similarity(query_emb, embeddings)[0]

        # Get indices of the top k nearest neighbors, excluding visited nodes
        k = min(len(uuids), k)
        top_k_indices = np.argsort(similarities)[-k:]

        # Retrieve the UUIDs for these indices
        top_k_uuids = [uuids[i] for i in top_k_indices if uuids[i] not in visited_nodes]

        return top_k_uuids

class KG_retriever(object):
    def __init__(self, k_list):
        self.k_list = k_list  # List of k values for each step
        self.embedder = OpenAIEmbedder()

    def retrieve(self, query, graph_constructor):
        # Step 1: Convert query to embedding
        query_embedding = self.embedder.get_embedding(query)

        # Initialize set for tracking visited nodes
        all_retrieved_nodes, visited_nodes = [], set()

        # Step 2: Retrieve top k1 similar nodes
        initial_nodes, all_retrieved_nodes, visited_nodes = self._retrieve_initial_nodes(query_embedding, graph_constructor, self.k_list[0], all_retrieved_nodes, visited_nodes)

        # Step 4: Retrieve nodes related to the initial_nodes
        for k in self.k_list[1:]:
            related_nodes = set()
            for node in initial_nodes:
                all_retrieved_nodes, visited_nodes, related_nodes = self._retrieve_neighbor_nodes(node, query_embedding, graph_constructor, k, all_retrieved_nodes, visited_nodes, related_nodes)
            initial_nodes = list(related_nodes)

        return [graph_constructor.uuid_to_node[uuid]['text'] for uuid in all_retrieved_nodes]

    def _get_unvisited_neighbors(self, node, graph_constructor, visited_nodes):
        return [neighbor for neighbor in graph_constructor.G.neighbors(node) if neighbor not in visited_nodes]

    def _get_neighbor_embeddings(self, neighbors, graph_constructor):
        embeddings = []
        for neighbor in neighbors:
            neighbor_index = graph_constructor.uuid_list.index(neighbor)
            embeddings.append(graph_constructor.embedding_list[neighbor_index])
        return embeddings
    
    def _retrieve_initial_nodes(self, query_embedding, graph_constructor, k, all_retrieved_nodes, visited_nodes):
        initial_nodes = KNN_Retrieval.retrieve(query_embedding, graph_constructor, k, visited_nodes)
        self._update_nodes(initial_nodes, all_retrieved_nodes, visited_nodes)
        return initial_nodes, all_retrieved_nodes, visited_nodes
    
    def _retrieve_neighbor_nodes(self, node, query_embedding, graph_constructor, k, all_retrieved_nodes, visited_nodes, related_nodes):
        neighbors = self._get_unvisited_neighbors(node, graph_constructor, visited_nodes)                
        neighbor_embeddings = self._get_neighbor_embeddings(neighbors, graph_constructor)
        if not neighbor_embeddings:
            return all_retrieved_nodes, visited_nodes, related_nodes
        retrieved_nodes = KNN_Retrieval.retrieve(query_embedding, graph_constructor, k, visited_nodes, neighbor_embeddings, neighbors)
        
        self._update_nodes(retrieved_nodes, all_retrieved_nodes, visited_nodes, related_nodes)
        return all_retrieved_nodes, visited_nodes, related_nodes

    def _update_nodes(self, nodes, all_retrieved_nodes, visited_nodes, related_nodes=None):
        for node in nodes:
            all_retrieved_nodes.append(node) if node not in all_retrieved_nodes else None
        visited_nodes.update(nodes)
        related_nodes.update(nodes) if related_nodes else None

class KG_retriever_GPT(KG_retriever):
    def __init__(self, k_list):
        self.k_list = k_list  # List of k values for each step
        self.embedder = OpenAIEmbedder()
        self.make_fake_evidence_chain = MakeFakeEvidenceChain(verbose=True)

    def retrieve(self, query, graph_constructor):
        # Step 1: Convert query to embedding
        query_embedding = self.embedder.get_embedding(query)

        # Initialize set for tracking visited nodes
        all_retrieved_nodes, visited_nodes = [], set()

        # Step 2: Retrieve top k1 similar nodes
        initial_nodes, all_retrieved_nodes, visited_nodes = self._retrieve_initial_nodes(query_embedding, graph_constructor, self.k_list[0], all_retrieved_nodes, visited_nodes)

        # Step 4: Retrieve nodes related to the initial_nodes
        for k in self.k_list[1:]:
            related_nodes = set()
            for node in initial_nodes:
                new_query = self.make_fake_evidence_chain.run(query=query, evidence=graph_constructor.uuid_to_node[node]['text'])
                new_query_embedding = self.embedder.get_embedding(new_query)
                all_retrieved_nodes, visited_nodes, related_nodes = self._retrieve_neighbor_nodes(node, new_query_embedding, graph_constructor, k, all_retrieved_nodes, visited_nodes, related_nodes)
            initial_nodes = list(related_nodes)

        return [{'document':graph_constructor.uuid_to_file_uuid[uuid], 'chunk':graph_constructor.uuid_to_node[uuid]['text'], 'bbox':graph_constructor.uuid_to_node[uuid]['bbox']} for uuid in all_retrieved_nodes]