class StreamingQueue:
    def __init__(self):
        self.main_queue = list()
        self.content = ""
        self.document_info = None
        self.document_flag = False
        self.end_flag = False
        self.error_flag = False

    def __len__(self):
        return len(self.main_queue)

    def append(self, new_text):
        self.main_queue.append(new_text)
        self.content += new_text

    def get(self):
        """
        return and delete first object of queue
        """
        return self.main_queue.pop(0)
    
    def set_document_info(self, document_info):
        self.document_info = document_info
        
    def document_end(self):
        self.document_flag = True
        
    def is_document_end(self):
        return self.document_flag
    
    def get_document_info(self, ref_name):
        print(self.document_info)
        return str(self.document_info)

    def end_job(self):
        self.end_flag = True

    def is_end(self):
        return self.end_flag and len(self.main_queue) == 0

    def is_empty(self):
        return len(self.main_queue) == 0

    def is_streaming_end(self):
        return self.end_flag and len(self.main_queue) > 0
    
    def __str__(self) -> str:
        if len(self.main_queue)>0:
            return self.main_queue[-1]
        else:
            return "empty"
        
    def error(self):
        self.error_flag = True
        
    def is_error(self):
        return self.error_flag

    def refresh(self):
        return ""