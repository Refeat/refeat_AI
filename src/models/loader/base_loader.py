import os
import uuid
import json
import datetime
from abc import ABC, abstractmethod

class BaseLoader(ABC):
    def __init__(self, file_uuid, project_id, file_path, save_dir, screenshot_dir):
        self.file_path = file_path
        self.file_uuid = file_uuid
        self.project_id = project_id
        self.screenshot_dir = screenshot_dir
        self.init_date = self.get_date()
        self.updated_date = None
        self.data = self.get_data(file_path, screenshot_dir)
        self.title = self.get_title(file_path) # web loader에서는 title이 data를 가져오는 과정에서 결정되므로, get_data()보다 뒤에 위치해야 함
        self.screenshot_path = self.get_screenshot(file_path, screenshot_dir) # web loader에서는 screenshot_path가 data를 가져오는 과정에서 결정되므로, get_data()보다 뒤에 위치해야 함
        self.favicon = self.get_favicon(file_path) # web loader에서는 favicon이 data를 가져오는 과정에서 결정되므로, get_data()보다 뒤에 위치해야 함
        self.full_text = self.get_full_text()
        self.processed_path = self.get_save_path(save_dir)

    @abstractmethod
    def get_data(self, file_path, screenshot_dir=None):
        pass

    @abstractmethod
    def get_title(self, file_path):
        pass

    @abstractmethod
    def get_screenshot(self, file_path, screenshot_dir):
        pass

    @abstractmethod
    def get_favicon(self, file_path):
        pass

    def get_date(self):
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def save_json_file(self, data, save_path):
        with open(save_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def save_data(self, save_dir):
        save_data = self.to_dict()
        save_path = self.get_save_path(save_dir)
        self.save_json_file(save_data, save_path)
        return save_path

    def get_save_path(self, save_dir):
        return os.path.join(save_dir, f'{self.file_uuid}.json')
    
    def get_full_text(self):
        return ' '.join([chunk['text'] for chunk in self.data])
        
    def to_dict(self):
        return {
            'file_path': self.file_path,
            'file_uuid': self.file_uuid,
            'project_id': self.project_id,
            'title': self.title,
            'screenshot_path': self.screenshot_path,
            'favicon': self.favicon,
            'init_date': self.init_date,
            'updated_date': self.updated_date,
            'full_text': self.full_text,
            'processed_path': self.processed_path,
            'data': self.data,
        }

    def __str__(self):
        return f'BaseLoader(file_path={self.file_path}, file_uuid={self.file_uuid}, project_id={self.project_id}, init_date={self.init_date}, updated_data={self.updated_date})'

    def __repr__(self):
        return self.__str__()