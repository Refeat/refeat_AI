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
from datetime import datetime

import tqdm
from elasticsearch import Elasticsearch, helpers
from elasticsearch.helpers import BulkIndexError

from models.embedder.utils import get_embedder
from database.elastic_search.db_config.refeat_db_config import MAPPINGS, SETTINGS, EMBEDDER

class CustomElasticSearch:
    mappings = MAPPINGS
    settings = SETTINGS
    def __init__(self, index_name='refeat_ai'):
        self.es = Elasticsearch(hosts=["http://localhost:9200"], timeout=60)
        self.index_name = index_name
        self.embedding = get_embedder(EMBEDDER)
    
    def _create_index(self, settings=SETTINGS, mappings=MAPPINGS):
        """
        기존의 인덱스를 삭제하고, 새로운 인덱스를 생성합니다.
        """
        self._delete_index()
        self.es.indices.create(index=self.index_name, settings=settings, mappings=mappings)

    def _delete_index(self):
        """
        인덱스를 삭제합니다.
        """
        if self.es.indices.exists(index=self.index_name):
            self.es.indices.delete(index=self.index_name)

    def add_documents_from_json_dir(self, json_dir):
        """
        json_dir에 있는 모든 json 파일을 읽어서, DB에 문서를 추가합니다.
        """
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

        self.refresh_index()

    def _get_files_from_json_dir(self, json_dir):
        """
        json_dir에 있는 모든 json 파일의 경로를 반환합니다.
        """
        json_files = []
        for root, dirs, files in os.walk(json_dir):
            for file in files:
                if file.endswith('.json'):
                    json_path = os.path.join(root, file)
                    json_files.append(json_path)
        return json_files

    def _prepare_bulk_action(self, json_path):
        """
        json 파일을 읽어서, Elasticsearch에 넣기위한 문서 형식으로 변환합니다.
        """
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
        """
        json 데이터를 Elasticsearch에 넣기위한 문서 형식으로 변환합니다.
        """
        document = {
            "project_id": data['project_id'],
            "file_path": data['file_path'],
            "file_uuid": data['file_uuid'],
            'title': data['title'],
            "full_text": data['full_text'],
            'summary': data['summary'],
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
        """
        json 파일을 읽어서, DB에 문서를 추가합니다.
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        document = self._prepare_document(data)

        self.es.index(index=self.index_name, document=document)
        self.refresh_index()

    def refresh_index(self):
        """
        인덱스를 refresh합니다.(refresh 이후 검색이 가능함)
        """
        self.es.indices.refresh(index=self.index_name)

    def get_all_files(self):
        query = {
            "query": {
                "match_all": {}  # 모든 문서를 매치
            }
        }

        response = self.es.search(index=self.index_name, body=query, size=10000)
        files = [hit["_source"] for hit in response["hits"]["hits"]]
        return files
    
    def delete_document(self, file_uuid):
        """
        file_uuid에 해당하는 문서를 삭제합니다.
        """
        query = {
            "query": {
                "match": {
                    "file_uuid": file_uuid
                }
            }
        }

        response = self.es.delete_by_query(index=self.index_name, body=query)
        self.refresh_index()
        return response

    def get_data_by_file_uuid(self, file_uuid):
        """
        file_uuid에 해당하는 문서의 데이터를 반환합니다.

        Args:
            file_uuid: 검색할 file_uuid

        Returns:
            data: file_uuid에 해당하는 문서의 데이터
        """
        query = {
            "query": {
                "match": {
                    "file_uuid": file_uuid
                }
            }
        }

        response = self.es.search(index=self.index_name, body=query)
        data = [hit["_source"] for hit in response["hits"]["hits"]]
        return data

    def get_summary_by_project_id(self, project_id):
        """
        project_id에 해당하는 문서의 summary를 반환합니다.

        Args:
            project_id: 검색할 project_id

        Returns:
            summary_list: project_id에 해당하는 문서의 summary 리스트
        """
        query = {
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"project_id": project_id}}
                    ]
                }
            },
            "_source": ["summary"]  # Only return the file_name field
        }

        response = self.es.search(index=self.index_name, body=query)
        summary_list = [hit["_source"]["summary"] for hit in response["hits"]["hits"]]
        return summary_list

    def post_process_search_results(self, response, search_range):
        """
        Elasticsearch의 검색 결과를 후처리합니다.

        Args:
            response: Elasticsearch의 검색 결과
            search_range: 검색 범위. [document, chunk]

        Returns:
            results: 후처리된 검색 결과
        """
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
    
    def _create_similarity_query(self, query_vector, search_range, part='chunk', num_chunks=5, limit_token_length=0, filter=None, project_filter=None):
        """
        Elasticsearch의 semantic 검색 쿼리를 생성합니다.

        Args:
            query_vector: 검색어의 임베딩 벡터
            search_range: 검색 범위. [document, chunk]
            part: 데이터의 어떤 값으로 검색을 할지. [chunk, topic_summary]
            num_chunks: 검색된 문서의 chunk 중에서, 몇 개의 chunk를 사용할지. chunk는 내부 점수를 기준으로 내림차순으로 정렬되어 있습니다.
            limit_token_length: chunk에서 limit_token_length보다 작은 길이의 chunk는 검색에서 제외합니다.
            filter: 검색 결과를 필터링할 때 사용할 file_uuid 리스트
            project_filter: 검색 결과를 필터링할 때 사용할 project_id

        Returns:
            es_query: Elasticsearch의 semantic 검색 쿼리
        """
        if search_range == 'document':
            # version1: title 또는 summary를 이용해서 검색했을 경우
            if part == 'topic_summary':
                raise ValueError("part='topic_summary' is not supported when search_range='document'")
                # es_query = {
                #     "script_score": {
                #         "query": {"match_all": {}},
                #         "script": {
                #             "source": """
                #                 double topicScore = (cosineSimilarity(params.query_vector, 'topic_embedding') + 1.0)/2.0;
                #                 double summaryScore = (cosineSimilarity(params.query_vector, 'summary_embedding') + 1.0)/2.0;
                #                 return topicScore + summaryScore;
                #             """,
                #             "params": {"query_vector": query_vector}
                #         }
                #     }
                # }

                # if filter and len(filter) > 0:
                #     es_query = {
                #         "bool": {
                #             "must": es_query,
                #             "filter": {
                #                 "bool": {
                #                     "should": [
                #                         {"match_phrase": {"topic": topic}} for topic in filter
                #                     ],
                #                     "minimum_should_match": 1
                #                 }
                #             }
                #         }
                #     }

                # return es_query
            
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

                # filter가 비어있지 않은 경우에만 토픽 필터 추가
                if filter and len(filter) > 0:
                    if "filter" not in es_query["bool"]:
                        es_query["bool"]["filter"] = {"bool": {"should": []}}
                    es_query["bool"]["filter"]["bool"]["should"].extend(
                        [{"match_phrase": {"file_uuid": file_uuid}} for file_uuid in filter]
                    )
                    es_query["bool"]["filter"]["bool"]["minimum_should_match"] = 1

                # project_filter가 비어있지 않은 경우에만 토픽 필터 추가
                if project_filter:
                    if "filter" not in es_query["bool"]:
                        es_query["bool"]["filter"] = []
                    es_query["bool"]["filter"].append({"term": {"project_id": project_filter}})
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

            # filter가 비어있지 않은 경우에만 토픽 필터 추가
            if filter and len(filter) > 0:
                if "filter" not in es_query["bool"]:
                    es_query["bool"]["filter"] = {"bool": {"should": []}}
                es_query["bool"]["filter"]["bool"]["should"].extend(
                    [{"match_phrase": {"file_uuid": file_uuid}} for file_uuid in filter]
                )
                es_query["bool"]["filter"]["bool"]["minimum_should_match"] = 1

            # project_filter가 비어있지 않은 경우에만 토픽 필터 추가
            if project_filter:
                if "filter" not in es_query["bool"]:
                    es_query["bool"]["filter"] = {"bool": {"must": []}}
                if "must" not in es_query["bool"]["filter"]["bool"]:
                    es_query["bool"]["filter"]["bool"]["must"] = []
                es_query["bool"]["filter"]["bool"]["must"].append({"term": {"project_id": project_filter}})
            return es_query

    def _create_match_query(self, query, search_range, part='chunk', num_chunks=5, limit_token_length=0, filter=None, project_filter=None):
        """
        Elasticsearch의 match(BM25) 검색 쿼리를 생성합니다.

        Args:
            query: 검색어
            search_range: 검색 범위. [document, chunk]
            part: 데이터의 어떤 값으로 검색을 할지. [chunk, topic_summary]
            num_chunks: 검색된 문서의 chunk 중에서, 몇 개의 chunk를 사용할지. chunk는 내부 점수를 기준으로 내림차순으로 정렬되어 있습니다.
            limit_token_length: chunk에서 limit_token_length보다 작은 길이의 chunk는 검색에서 제외합니다.
            filter: 검색 결과를 필터링할 때 사용할 file_uuid 리스트
            project_filter: 검색 결과를 필터링할 때 사용할 project_id

        Returns:
            es_query: Elasticsearch의 match(BM25) 검색 쿼리
        """
        # version1: title 또는 summary를 이용해서 검색했을 경우
        if search_range == 'document':
            if part == 'topic_summary':
                raise ValueError("part='topic_summary' is not supported when search_range='document'")
                # es_query = {
                #     "bool": {
                #         "must": [
                #             {"match": {"topic": query}}
                #         ],
                #     }
                # }

                # # filter가 제공되고, 비어있지 않은 경우에만 토픽 필터 추가
                # if filter and len(filter) > 0:
                #     if "filter" not in es_query["bool"]:
                #         es_query["bool"]["filter"] = {"bool": {"should": []}}
                #     es_query["bool"]["filter"]["bool"]["should"].extend(
                #         [{"match_phrase": {"topic": topic}} for topic in filter]
                #     )
                #     es_query["bool"]["filter"]["bool"]["minimum_should_match"] = 1
                
                # return es_query
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

                # filter가 비어있지 않은 경우에만 토픽 필터 추가
                if filter and len(filter) > 0:
                    if "filter" not in es_query["bool"]:
                        es_query["bool"]["filter"] = {"bool": {"should": []}}
                    es_query["bool"]["filter"]["bool"]["should"].extend(
                        [{"match_phrase": {"file_uuid": file_uuid}} for file_uuid in filter]
                    )
                    es_query["bool"]["filter"]["bool"]["minimum_should_match"] = 1

                # project_filter가 비어있지 않은 경우에만 토픽 필터 추가
                if project_filter:
                    if "filter" not in es_query["bool"]:
                        es_query["bool"]["filter"] = {"bool": {"must": []}}
                    if "must" not in es_query["bool"]["filter"]["bool"]:
                        es_query["bool"]["filter"]["bool"]["must"] = []
                    es_query["bool"]["filter"]["bool"]["must"].append({"term": {"project_id": project_filter}})

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

            # filter가 비어있지 않은 경우에만 토픽 필터 추가
            if filter and len(filter) > 0:
                if "filter" not in es_query["bool"]:
                    es_query["bool"]["filter"] = {"bool": {"should": []}}
                es_query["bool"]["filter"]["bool"]["should"].extend(
                    [{"match_phrase": {"file_uuid": file_uuid}} for file_uuid in filter]
                )
                es_query["bool"]["filter"]["bool"]["minimum_should_match"] = 1

            # project_filter가 비어있지 않은 경우에만 토픽 필터 추가
            if project_filter:
                if "filter" not in es_query["bool"]:
                    es_query["bool"]["filter"] = {"bool": {"must": []}}
                if "must" not in es_query["bool"]["filter"]["bool"]:
                    es_query["bool"]["filter"]["bool"]["must"] = []
                es_query["bool"]["filter"]["bool"]["must"].append({"term": {"project_id": project_filter}})

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
               filter=None,
               project_filter=None):
        """
        Elasticsearch에 검색을 요청합니다.

        Args:
            query: 검색어
            query_embedding: 검색어의 임베딩 벡터
            num_results: 최종 결과로 반환할 문서 수
            method: 검색 방법. [similarity, match, hybrid]
            search_range: 검색 범위. [document, chunk]
            part: 데이터의 어떤 값으로 검색을 할지. [chunk, topic_summary]
            num_chunks: 검색된 문서의 chunk 중에서, 몇 개의 chunk를 사용할지. chunk는 내부 점수를 기준으로 내림차순으로 정렬되어 있습니다.
            limit_token_length: chunk에서 limit_token_length보다 작은 길이의 chunk는 검색에서 제외합니다.
            match_weight: hybrid search에서 match search의 가중치
            similarity_weight: hybrid search에서 similarity search의 가중치
            filter: 검색 결과를 필터링할 때 사용할 file_uuid 리스트
            project_filter: 검색 결과를 필터링할 때 사용할 project_id
        
        Returns:
            response: Elasticsearch의 검색 결과
        """
        search_results_num = num_results 
        if method == 'similarity':            
            response = self._similarity_search(query, query_embedding, search_range, part, search_results_num, num_chunks, limit_token_length, filter, project_filter)
        elif method == 'match':
            response = self._match_search(query, search_range, part, search_results_num, num_chunks, limit_token_length, filter, project_filter)
        elif method == 'hybrid':
            response = self._hybrid_search(query, query_embedding, search_range, part, search_results_num, num_chunks, limit_token_length, match_weight, similarity_weight, filter, project_filter)
            
        response = self.post_process_search_results(response, search_range)
        response = response[:num_results] if response is not None else []
        return response
    
    def _create_filter_from_results(self, results):
        """
        이전 검색 결과에서 file_uuid을 추출하여, filter를 생성합니다. 이 작업은 2단계 이상의 검색을 사용할 때 사용됩니다.

        Args:
            results: post_process_search_results 함수 이후의 검색결과

        Returns:
            file_uuid_list: 검색 결과에서 추출한 file_uuid 리스트
        """
        file_uuid_list = [result['document_info']['file_uuid'] for result in results]
        return file_uuid_list

    def parse_input_query(self, search_config, filter):
        """
        검색 config로 부터 검색에 필요한 파라미터들을 추출합니다.

        Args:
            search_config: 검색 config
            filter: 검색 결과를 필터링할 때 사용할 project_id 리스트
        """
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
        filter = search_config.get('filter', filter) # search config에 filter가 있으면 filter를 사용하고, 없으면 입력으로 받은 filter를 사용
        return query, query_embedding, num_results, method, search_range, part, num_chunks, limit_token_length, match_weight, similarity_weight, filter

    def multi_search(self, search_configs):
        """
        여러 단계의 검색을 순차적으로 수행합니다. 이전 검색의 결과를 이후 검색에 사용합니다.

        Args:
            search_configs: 검색 config 리스트

        Returns:
            response: 검색 결과
        """
        filter = None # 첫 단계의 검색에서는 filter를 사용하지 않습니다(단, search config에 filter가 있으면 그 값을 사용). 이후 단계의 검색에서는 이전 검색의 결과에서 추출한 filter를 사용합니다.
        for search_config in search_configs:
            query_params = self.parse_input_query(search_config, filter) # search_config에 filter가 있으면, filter를 사용하고, 없으면 이전 결과에서 추출한 filter를 사용
            response = self.search(*query_params)
            filter = self._create_filter_from_results(response) # 이전 검색 결과에서 file_name을 추출하여, filter를 생성합니다.
        return response

    def _similarity_search(self, query, query_embedding=None, search_range='document', part='chunk', num_results=5, num_chunks=5, limit_token_length=0, filter=None, project_filter=None):
        """
        Elasticsearch의 semantic 검색을 수행합니다.
        """
        query_vector = self.embedding.get_embedding(query) if query_embedding is None else query_embedding
        elastic_query = self._create_similarity_query(query_vector, search_range, part, num_chunks, limit_token_length, filter, project_filter)
        response = self.es.search(index=self.index_name, size=num_results, query=elastic_query)
        return response
    
    def _match_search(self, query, search_range='document', part='chunk', num_results=5, num_chunks=5, limit_token_length=0, filter=None, project_filter=None):
        """
        Elasticsearch의 match(BM25) 검색을 수행합니다.
        """
        elastic_query = self._create_match_query(query, search_range, part, num_chunks, limit_token_length, filter, project_filter)
        response = self.es.search(index=self.index_name, size=num_results, query=elastic_query)
        return response
    
    def _hybrid_search(self, query, query_embedding=None, search_range='document', part='chunk', num_results=5, num_chunks=5, limit_token_length=0, match_weight=1, similarity_weight=1, filter=None, project_filter=None):
        """
        Elasticsearch의 hybrid 검색(similarity + match)을 수행합니다.
        """
        if search_range == 'chunk':
            raise ValueError("search_range='chunk' is not supported when method='hybrid'")
        num_results_multiplier = 4 # 두 개의 검색을 더하는 방법을 사용하므로, 각각의 검색 결과 수를 넉넉하게 N배로 설정
        single_search_num_results = num_results *  num_results_multiplier
        similarity_response = self._similarity_search(query, query_embedding, search_range, part, single_search_num_results, num_chunks, limit_token_length, filter, project_filter)
        match_response = self._match_search(query, search_range, part, single_search_num_results, num_chunks, limit_token_length, filter, project_filter)
        response = self._combine_response(similarity_response, match_response, match_weight, similarity_weight)
        return response
    
    def _combine_response(self, similarity_response, match_response, match_weight=0.02, similarity_weight=1):
        """
        hybrid 검색을 위해 similarity와 match 검색 결과를 합칩니다.
        
        Args:
            similarity_response: Elasticsearch의 semantic 검색 결과
            match_response: Elasticsearch의 match(BM25) 검색 결과
            match_weight: hybrid search에서 match search의 가중치
            similarity_weight: hybrid search에서 similarity search의 가중치

        Returns:
            final_response: hybrid 검색 결과
        """
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
    
    # ---------- create index ---------- #
    es._create_index(settings=es.settings, mappings=es.mappings)
    json_path = '../../modules/test_data/6feb401c-8ab2-4440-8671-fad5e7e1f115.json'
    es.add_document_from_json(json_path) # add single document

    # ---------- delete index ---------- #
    # es._delete_index()

    # ---------- search test ---------- #
    print('11111111')
    response = es.search(
        query="아시아 경제 성장", 
        query_embedding=None,
        num_results=5, # 최종 결과로 반환할 문서 수
        method='similarity', # [similarity, match, hybrid]
        search_range='chunk', # [document, chunk]
        part='chunk', # [chunk, topic_summary]
        num_chunks=5, # reranking을 사용할 경우, 사용할 chunk 수
        limit_token_length=100,
        match_weight=0.02, # hybrid search에서 match search의 가중치
        similarity_weight=1, # hybrid search에서 similarity search의 가중치
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
        print(f"Document file path: {document_info['file_uuid']}")
        if inner_contents:
            for inner_content in inner_contents:
                print(f"\tInner Content Score: {inner_content['score']}, Content: {inner_content['content']}")

    # ---------- search file names by project id ---------- #
    # file_names = es.search_file_names_by_project_id(-1)
    # print(file_names)


    # ---------- get all files ---------- #
    # files = es.get_all_files()
    # print(files)

    # ---------- delete file ---------- #
    # file_uuid = '6feb401c-8ab2-4440-8671-fad5e7e1f115'
    # response = es.delete_document(file_uuid)