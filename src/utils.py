import os
import sys
import configparser

def get_current_path():
    # 현재 경로를 반환
    return os.path.dirname(os.path.abspath(__file__))

def add_api_key():
    # api key들을 환경변수에 추가
    config = configparser.ConfigParser()
    current_path = get_current_path()
    config.read(os.path.join(current_path, '../.secrets.ini'))
    openai_api_key = config['OPENAI']['OPENAI_API_KEY']
    os.environ.update({'OPENAI_API_KEY': openai_api_key})