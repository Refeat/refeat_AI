import json

class ElasticSearchConfig:
    def __init__(self, json_path):
        with open(json_path, 'r') as f:
            self.config = json.load(f)

    def __str__(self):
        return str(self.config)
    
    def __repr__(self):
        return repr(self.config)

    def __getitem__(self, stage=0, key='query'):
        return self.config[stage][key]
    
    def __setitem__(self, stage=0, key='query', value=''):
        self.config[stage][key] = value

    def set_query(self, query):
        for stage in range(len(self.config)):
            self.config[stage]['query'] = query

    def __len__(self):
        return len(self.config)
    
    def __call__(self):
        return self.config
    
    def __iter__(self):
        return iter(self.config)
    
if __name__ == "__main__":
    json_path = './search_config/hybrid_topic_similarity_chunk.json'
    es_config = ElasticSearchConfig(json_path)
    for config in es_config:
        print(config)