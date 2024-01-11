import os
import json
from typing import List

current_path = os.path.dirname(os.path.abspath(__file__))

class ElasticSearchConfig:
    def __init__(self, json_path=os.path.join(current_path, './search_config/similarity_chunk.json')):
        with open(json_path, 'r') as f:
            self.config = json.load(f)

    def __str__(self):
        return str(self.config)
    
    def __repr__(self):
        return repr(self.config)

    def __getitem__(self, key, stage=0):
        return self.config[stage][key]
    
    def __setitem__(self, key, value, stage=0):
        self.config[stage][key] = value

    def set_query(self, query):
        for stage in range(len(self.config)):
            self.config[stage]['query'] = query

    def set_filter(self, filter:List[str]):
        self.config[0]['filter'] = filter

    def set_project_id(self, project_id):
        self.config[0]['project_id'] = project_id

    def __len__(self):
        return len(self.config)
    
    def __call__(self):
        return self.config
    
    def __iter__(self):
        return iter(self.config)
    
    def reset(self):
        self.__init__()
    
if __name__ == "__main__":
    json_path = './search_config/hybrid_topic_similarity_chunk.json'
    es_config = ElasticSearchConfig(json_path)
    for config in es_config:
        print(config)