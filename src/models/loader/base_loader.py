import os
import re
import json
import datetime
from abc import ABC, abstractmethod

class BaseLoader(ABC):
    def __init__(self, file_path=None):
        self.file_path = file_path
        self.file_name = self.get_base_name(file_path)
        self.init_date = self.get_date()
        self.data = self.get_data(file_path)
        self.updated_data = None

    @abstractmethod
    def get_data(self, file_path):
        pass

    def get_date(self):
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    @abstractmethod
    def get_base_name(self, file_path):
        pass

    def save_json_file(self, data, save_path):
        with open(save_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def save_data(self, save_dir):
        save_data = self.to_dict()
        save_path = self.get_save_path(save_dir)
        self.save_json_file(save_data, save_path)

    def get_save_path(self, save_dir):
        # 파일 이름에서 유효하지 않은 문자를 '_'로 대체
        safe_file_name = re.sub(r'[\\/*?:"<>|]', '_', self.file_name)
        # 날짜 및 시간에서 콜론을 '_'로 대체
        safe_date = self.init_date.replace(':', '_')
        save_path = os.path.join(save_dir, f'{safe_file_name}_{safe_date}.json')
        return save_path
        
    def to_dict(self):
        return {
            'file_path': self.file_path,
            'file_name': self.file_name,
            'init_date': self.init_date,
            'updated_data': self.updated_data,
            'data': self.data
        }

    def __str__(self):
        return f'BaseLoader(file_path={self.file_path}, file_name={self.file_name}, init_date={self.init_date}, updated_data={self.updated_data})'

    def __repr__(self):
        return self.__str__()