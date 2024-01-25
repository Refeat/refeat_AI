MAPPINGS = {
    "properties": {
        "project_id": {
            "type": "keyword"
        },
        "file_path": {
            "type": "text",
            "fields": {
                "keyword": {
                    "type": "keyword"
                }
            }
        },
        "file_uuid": {
            "type": "keyword"
        },
        "title": {
            "type": "text"
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
        'summary': {
            'type': 'text'
        },
        "chunk_list_by_text_rank": {
            "type": "text"
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
SETTINGS = {
    "number_of_shards": 1,
    "number_of_replicas": 1
}
EMBEDDER = 'openai'