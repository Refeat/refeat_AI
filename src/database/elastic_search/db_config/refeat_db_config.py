MAPPINGS = {
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
SETTINGS = {
    "number_of_shards": 1,
    "number_of_replicas": 1
}
EMBEDDER = 'openai'