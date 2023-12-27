import os
import sys
current_path = os.path.dirname(os.path.abspath(__file__))
for _ in range(2):
    current_path = os.path.dirname(current_path)
sys.path.append(current_path)

from utils import add_api_key
add_api_key()

import json
from datetime import datetime

import tqdm
from elasticsearch import Elasticsearch, helpers
from elasticsearch.helpers import BulkIndexError

from models.embedder.utils import get_embedder

class CustomElasticSearch:
    mappings = {
        "properties": {
            "file_path": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword"
                    }
                }
            },
            "file_name": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword"
                    }
                }
            },
            "full_text":{
                "type": "text"
            },
            "init_date": {
                "type": "date"
            },
            "updated_date": {
                "type": "date"
            },
            "contents": {
                "type": "nested",
                "properties": {
                    "content": {
                        "type": "text"
                    },
                    "bbox": {
                        "properties": {
                            "left_x": {
                                "type": "integer"
                            },
                            "top_y": {
                                "type": "integer"
                            },
                            "right_x": {
                                "type": "integer"
                            },
                            "bottom_y": {
                                "type": "integer"
                            }
                        }
                    },
                    "content_embedding": {
                        "type": "dense_vector",
                        "dims": 1536
                        # "dims": 1024
                    },
                    "page": {
                        "type": "integer"
                    },
                    "token_num": {
                        "type": "integer"
                    }
                }
            }
        }
    }
    settings = {
        "number_of_shards": 1,
        "number_of_replicas": 1
    }
    def __init__(self, index_name='arxiv'):
        self.es = Elasticsearch(hosts=["http://localhost:9200"], timeout=180)
        self.index_name = index_name
        self.embedding = get_embedder('openai')
    
    def _create_index(self, settings=None, mappings=None):
        self._delete_index()
        self.es.indices.create(index=self.index_name, settings=settings, mappings=mappings)

    def _delete_index(self):
        if self.es.indices.exists(index=self.index_name):
            self.es.indices.delete(index=self.index_name)

    def _get_files_from_json_dir(self, json_dir):
        json_files = []
        for root, dirs, files in os.walk(json_dir):
            for file in files:
                if file.endswith('.json'):
                    json_path = os.path.join(root, file)
                    json_files.append(json_path)
        return json_files

    def add_documents_from_json_dir(self, json_dir):
        json_files = self._get_files_from_json_dir(json_dir)
        # version1: 아래는 bulk를 사용하여 한 번에 여러 문서를 추가하는 방법입니다.
        # actions = []
        # for json_path in tqdm.tqdm(json_files):
        #     action = self._prepare_bulk_action(json_path)
        #     if action:
        #         actions.extend(action)
        
        # # Use the helpers.bulk function to add documents in bulk
        # if actions:
        #     try:
        #         helpers.bulk(self.es, actions, index=self.index_name)
        #     except BulkIndexError as e:
        #         for i, error in enumerate(e.errors):
        #             # Log error details
        #             print(f"Error {i}: {error}")
        
        # version2: 아래는 한 번에 한 문서씩 추가하는 방법입니다.
        for json_path in tqdm.tqdm(json_files):
            try:
                self.add_document_from_json(json_path)
            except Exception as e:
                print(f"Error adding document {json_path}")

        # Refresh your index
        self.es.indices.refresh(index=self.index_name)

    def _prepare_bulk_action(self, json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading file {json_path}: {e}")
            return None

        document = self._prepare_document(data)
        if document:
            return [{"_index": self.index_name, "_source": document}]
        return None
    
    def _prepare_document(self, data):
        # Convert to Elasticsearch document format
        document = {
            "file_name": data['file_name'],
            "file_path": data['file_path'],
            "full_text": data['full_text'],
            "init_date": datetime.strptime(data['init_date'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S'),
            "updated_date": datetime.strptime(data['updated_data'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S') if data['updated_date'] else None,
            "contents": [
                {
                    "content": content['text'],
                    "content_embedding": content['embedding'],
                    "bbox": content['bbox'],
                    "page": content['page'],
                    "token_num": content['token_num']
                } for content in data['data']
                    if (content['embedding'] is not None) and (content['text'] != '')
            ]
        }

        return document

    def add_document_from_json(self, json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self._add_document(data)
    
    def _add_document(self, data):
        document = self._prepare_document(data)

        # Elasticsearch에 문서 추가
        self.es.index(index=self.index_name, document=document)

    def post_process_search_results(self, response, search_range):
        # 모든 'chunk'를 저장할 리스트 초기화
        if search_range == 'document':
            all_documents = []
            for hit in response['hits']['hits']:
                document_entry = {
                    'document_info': hit['_source'],
                    'document_score': hit['_score']
                }

                # inner_hits 처리
                inner_hits = hit.get('inner_hits', {}).get('contents', {}).get('hits', {}).get('hits', [])
                if inner_hits:
                    inner_contents = []
                    for inner_hit in inner_hits:
                        inner_content = inner_hit['_source'].get('content', '')
                        inner_score = inner_hit['_score']
                        inner_contents.append({'content': inner_content, 'score': inner_score})
                    document_entry['inner_contents'] = inner_contents

                all_documents.append(document_entry)
            results = all_documents

        elif search_range == 'chunk':
            all_chunks = []
            # 각 문서에 대해 반복
            for hit in response['hits']['hits']:
                # 각 문서의 'inner_hits' 접근
                inner_hits = hit.get('inner_hits', {}).get('contents', {}).get('hits', {}).get('hits', [])

                # 각 'chunk'에 대해 반복
                for inner_hit in inner_hits:
                    # 'chunk' 정보와 점수 추출
                    chunk_info = inner_hit['_source']
                    chunk_score = inner_hit['_score']
                    document_info = hit['_source']
                    document_score = hit['_score']

                    # 모든 'chunk' 저장
                    all_chunks.append({
                        'chunk_info':chunk_info, 
                        'chunk_score':chunk_score, 
                        'document_info':document_info, 
                        'document_score':document_score
                    })

            # 'chunk'를 점수에 따라 내림차순으로 정렬
            all_chunks = sorted(all_chunks, key=lambda x: x['chunk_score'], reverse=True)
            results = all_chunks

        return results
    
    def _create_similarity_query(self, query_vector, search_range, part='chunk', num_chunks=5, limit_token_length=0, filter=None):
        if search_range == 'document':
            # version1: title 또는 summary를 이용해서 검색했을 경우
            if part == 'topic_summary':
                es_query = {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": """
                                double topicScore = (cosineSimilarity(params.query_vector, 'topic_embedding') + 1.0)/2.0;
                                double summaryScore = (cosineSimilarity(params.query_vector, 'summary_embedding') + 1.0)/2.0;
                                return topicScore + summaryScore;
                            """,
                            "params": {"query_vector": query_vector}
                        }
                    }
                }

                if filter and len(filter) > 0:
                    es_query = {
                        "bool": {
                            "must": es_query,
                            "filter": {
                                "bool": {
                                    "should": [
                                        {"match_phrase": {"topic": topic}} for topic in filter
                                    ],
                                    "minimum_should_match": 1
                                }
                            }
                        }
                    }

                return es_query
            
            elif part == 'chunk':
                es_query = {
                    "bool": {
                        "must": {
                            "nested": {
                                "path": "contents",
                                "query": {
                                    "bool": {
                                        "must": {
                                            "script_score": {
                                                "query": {"match_all": {}},
                                                "script": {
                                                    "source": "if (doc['contents.token_num'].value >= params.limit_token_length) { return (cosineSimilarity(params.query_vector, 'contents.content_embedding') + 1.0)/2.0; } else { return 0; }",
                                                    "params": {"query_vector": query_vector, "limit_token_length": limit_token_length}
                                                }
                                            }
                                        }
                                    }
                                },
                                "inner_hits": self._get_inner_hits(num_chunks),
                                "score_mode": "max"
                            }
                        }
                    }
                }

                # filter가 제공되고, 비어있지 않은 경우에만 필터 적용
                if filter and len(filter) > 0:
                    if "filter" not in es_query["bool"]:
                        es_query["bool"]["filter"] = {"bool": {"should": []}}
                    es_query["bool"]["filter"]["bool"]["should"].extend(
                        [{"match_phrase": {"topic": topic}} for topic in filter]
                    )
                    es_query["bool"]["filter"]["bool"]["minimum_should_match"] = 1
                return es_query
            
        elif search_range == 'chunk':
            if part == 'topic_summary':
                raise ValueError("part='topic_summary' is not supported when search_range='chunk'")
            es_query = {
                "bool": {
                    "must": {
                        "nested": {
                            "path": "contents",
                            "query": {
                                "bool": {
                                    "must": {
                                        "script_score": {
                                            "query": {"match_all": {}},
                                            "script": {
                                                "source": "if (doc['contents.token_num'].value >= params.limit_token_length) { return (cosineSimilarity(params.query_vector, 'contents.content_embedding') + 1.0)/2.0; } else { return 0; }",
                                                "params": {"query_vector": query_vector, "limit_token_length": limit_token_length}
                                            }
                                        }
                                    }
                                }
                            },
                            "inner_hits": self._get_inner_hits(num_chunks),
                            "score_mode": "max"
                        }
                    }
                }
            }

            # filter가 제공되고, 비어있지 않은 경우에만 토픽 필터 추가
            if filter and len(filter) > 0:
                if "filter" not in es_query["bool"]:
                    es_query["bool"]["filter"] = {"bool": {"should": []}}
                es_query["bool"]["filter"]["bool"]["should"].extend(
                    [{"match_phrase": {"file_name": file_name}} for file_name in filter]
                )
                es_query["bool"]["filter"]["bool"]["minimum_should_match"] = 1
            return es_query

    def _create_match_query(self, query, search_range, part='chunk', num_chunks=5, limit_token_length=0, filter=None):
        if search_range == 'document':
            # version1: title 또는 summary를 이용해서 검색했을 경우
            # using elastic search match
            if part == 'topic_summary':
                es_query = {
                    "bool": {
                        "must": [
                            {"match": {"topic": query}}
                        ],
                    }
                }

                # filter가 제공되고, 비어있지 않은 경우에만 토픽 필터 추가
                if filter and len(filter) > 0:
                    if "filter" not in es_query["bool"]:
                        es_query["bool"]["filter"] = {"bool": {"should": []}}
                    es_query["bool"]["filter"]["bool"]["should"].extend(
                        [{"match_phrase": {"topic": topic}} for topic in filter]
                    )
                    es_query["bool"]["filter"]["bool"]["minimum_should_match"] = 1
                
                return es_query
            # version2: chunk를 이용해서 검색했을 경우
            elif part == 'chunk':
                es_query = {
                    "bool": {
                        "must": {
                            "nested": {
                                "path": "contents",
                                "query": {
                                    "bool": {
                                        "must": [
                                            {"match": {"contents.index": {"query": query}}}
                                        ],
                                        "filter": {
                                            "bool": {
                                                "must": [
                                                    {"range": {"contents.token_num": {"gte": limit_token_length}}}
                                                ]
                                            }
                                        }
                                    }
                                },
                                "inner_hits": self._get_inner_hits(num_chunks),
                                "score_mode": "max"
                            }
                        }
                    }
                }

                # filter가 제공되고, 비어있지 않은 경우에만 토픽 필터 추가
                if filter and len(filter) > 0:
                    if "filter" not in es_query["bool"]:
                        es_query["bool"]["filter"] = {"bool": {"should": []}}
                    es_query["bool"]["filter"]["bool"]["should"].extend(
                        [{"match_phrase": {"topic": topic}} for topic in filter]
                    )
                    es_query["bool"]["filter"]["bool"]["minimum_should_match"] = 1

                return es_query

        elif search_range == 'chunk':
            es_query = {
                "bool": {
                    "must": {
                        "nested": {
                            "path": "contents",
                            "query": {
                                "bool": {
                                    "must": [
                                        {"match": {"contents.content": {"query": query}}}
                                    ],
                                    "filter": {
                                        "bool": {
                                            "must": [
                                                {"range": {"contents.token_num": {"gte": limit_token_length}}}
                                            ]
                                        }
                                    }
                                }
                            },
                            "inner_hits": self._get_inner_hits(num_chunks),
                            "score_mode": "max"
                        }
                    }
                }
            }

            # filter가 제공되고, 비어있지 않은 경우에만 토픽 필터 추가
            if filter and len(filter) > 0:
                if "filter" not in es_query["bool"]:
                    es_query["bool"]["filter"] = {"bool": {"should": []}}
                es_query["bool"]["filter"]["bool"]["should"].extend(
                    [{"match_phrase": {"file_name": file_name}} for file_name in filter]
                )
                es_query["bool"]["filter"]["bool"]["minimum_should_match"] = 1

            return es_query


    def _get_inner_hits(self, size=5):
        return {
            "size": size,  # 내부 히트 수 상수화
            "sort": [{"_score": {"order": "desc"}}]
        }

    def search(self, 
               query, 
               query_embedding=None, 
               num_results=5, 
               method='similarity', 
               search_range='chunk', 
               part='chunk',
               num_chunks=5, 
               limit_token_length=30, 
               match_weight=0.02, 
               similarity_weight=1,
               filter=None):
        search_results_num = num_results # reranking을 사용할 경우, top_k만큼 search를을 수행
        if method == 'similarity':            
            response = self._similarity_search(query, query_embedding, search_range, part, search_results_num, num_chunks, limit_token_length, filter)
        elif method == 'match':
            response = self._match_search(query, search_range, part, search_results_num, num_chunks, limit_token_length, filter)
        elif method == 'hybrid':
            response = self._hybrid_search(query, query_embedding, search_range, part, search_results_num, num_chunks, limit_token_length, match_weight, similarity_weight, filter)
            
        response = self.post_process_search_results(response, search_range)
        response = response[:num_results] if response is not None else []
        return response
    
    def _create_filter_from_results(self, results):
        topic_list = [result['document_info']['topic'] for result in results]
        return topic_list

    def parse_input_query(self, search_config, filter):
        query = search_config.get('query', None)
        query_embedding = search_config.get('query_embedding', None)
        num_results = search_config.get('num_results', 5)
        method = search_config.get('method', 'hybrid')
        search_range = search_config.get('search_range', 'document')
        part = search_config.get('part', 'chunk')
        num_chunks = search_config.get('num_chunks', 5)
        limit_token_length = search_config.get('limit_token_length', 0)
        match_weight = search_config.get('match_weight', 0.02)
        similarity_weight = search_config.get('similarity_weight', 1)
        filter = search_config.get('filter', filter)
        return query, query_embedding, num_results, method, search_range, part, num_chunks, limit_token_length, match_weight, similarity_weight, filter

    def multi_search(self, search_configs):
        # args: [List of (query, query_embedding, top_k, num_results, method, search_range, part, num_chunks, limit_token_length, match_weight, similarity_weight)]
        filter = None
        for search_config in search_configs:
            query_params = self.parse_input_query(search_config, filter)
            response = self.search(*query_params)
            filter = self._create_filter_from_results(response)
        return response

    def _similarity_search(self, query, query_embedding=None, search_range='document', part='chunk', num_results=5, num_chunks=5, limit_token_length=0, filter=None):
        query_vector = self.embedding.get_embedding(query) if query_embedding is None else query_embedding
        elastic_query = self._create_similarity_query(query_vector, search_range, part, num_chunks, limit_token_length, filter)
        response = self.es.search(index=self.index_name, size=num_results, query=elastic_query)
        return response
    
    def _match_search(self, query, search_range='document', part='chunk', num_results=5, num_chunks=5, limit_token_length=0, filter=None):
        elastic_query = self._create_match_query(query, search_range, part, num_chunks, limit_token_length, filter)
        response = self.es.search(index=self.index_name, size=num_results, query=elastic_query)
        return response
    
    def _hybrid_search(self, query, query_embedding=None, search_range='document', part='chunk', num_results=5, num_chunks=5, limit_token_length=0, match_weight=1, similarity_weight=1, filter=None):
        if search_range == 'chunk':
            raise ValueError("search_range='chunk' is not supported when method='hybrid'")
        single_search_num_results = num_results * 4 # 두 개의 검색을 더하는 방법을 사용하므로, 각각의 검색 결과 수를 N배로 설정
        similarity_response = self._similarity_search(query, query_embedding, search_range, part, single_search_num_results, num_chunks, limit_token_length, filter)
        match_response = self._match_search(query, search_range, part, single_search_num_results, num_chunks, limit_token_length, filter)
        response = self._combine_response(similarity_response, match_response, match_weight, similarity_weight)
        return response
    
    def _combine_response(self, similarity_response, match_response, match_weight=1, similarity_weight=1):
        similarity_hits = similarity_response['hits']['hits']
        match_hits = match_response['hits']['hits']

        combined_results = {}

        # Process similarity hits
        for hit in similarity_hits:
            score = hit['_score'] * similarity_weight
            doc_id = hit['_id']
            combined_results[doc_id] = {'score': score, 'hit': hit}
        pass
        # Process match hits
        for hit in match_hits:
            score = hit['_score'] * match_weight
            doc_id = hit['_id']
            if doc_id in combined_results:
                combined_results[doc_id]['score'] += score
                combined_results[doc_id]['hit']['_score'] += score
            else:
                combined_results[doc_id] = {'score': score, 'hit': hit}
                combined_results[doc_id]['hit']['_score'] = score
        pass
        # Sort the combined results by their scores in descending order
        sorted_results = sorted(combined_results.values(), key=lambda x: x['score'], reverse=True)
        pass
        # Prepare the final response format
        final_response = {
            'hits': {'hits': [result['hit'] for result in sorted_results]},
        }

        return final_response        

if __name__ == "__main__":
    # test elasticsearch
    es = CustomElasticSearch(index_name='refeat_ai')
    
    # # ---------- create index ---------- #
    # es._create_index(settings=es.settings, mappings=es.mappings)
    # json_path = '../../modules/test_data/Cross-lingual Language Model Pretraining_2023-12-26 16_48_17.json'
    # es.add_document_from_json(json_path)
    # es.add_documents_from_json_dir('../../data/arxiv/rag_test_token_256_overlap_16_large/chunk')


    # ---------- delete index ---------- #
    # es._delete_index()

    # ---------- search test ---------- #
    response = es.search(
        query="Cross-lingual Language Model Pretraining bleu score", 
        query_embedding=None,
        num_results=5, # 최종 결과로 반환할 문서 수
        method='similarity', # [similarity, match, hybrid]
        search_range='chunk', # [document, chunk]
        part='chunk', # [chunk, topic_summary]
        num_chunks=5, # reranking을 사용할 경우, 사용할 chunk 수
        limit_token_length=100,
        match_weight=0.02, # hybrid search에서 match search의 가중치
        similarity_weight=1, # hybrid search에서 similarity search의 가중치
        # filter=['Cross-lingual Language Model Pretraining'] # topic filter
        )
    
    for i, result in enumerate(response):
        chunk_score = result['chunk_score'] if 'chunk_score' in result else None
        chunk_info = result['chunk_info'] if 'chunk_info' in result else None
        document_score = result['document_score'] if 'document_score' in result else None
        document_info = result['document_info'] if 'document_info' in result else None
        inner_contents = result['inner_contents'] if 'inner_contents' in result else None

        print(f"Result {i}:")
        if chunk_score and chunk_info:
            print(f"Chunk score: {chunk_score}")
            print(f"Chunk content: {chunk_info['content']}")
        print(f"Document score: {document_score}")
        print(f"Document file path: {document_info['file_name']}")
        if inner_contents:
            for inner_content in inner_contents:
                print(f"\tInner Content Score: {inner_content['score']}, Content: {inner_content['content']}")
