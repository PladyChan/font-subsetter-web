import os
import tempfile

def get_config():
    """获取默认配置"""
    return {
        'latin': True,        # 英文字母
        'numbers': True,      # 数字
        'punctuation': True,  # 标点符号
        'degree': True,       # 度数符号
        'currency': True,     # 货币符号
        'math': True,         # 数学符号
        'copyright': True,    # 版权符号
        'arrows': True,       # 箭头
        'ligatures': True,    # 连字
        'fractions': True,    # 分数
        'superscript': True,  # 上标下标
        'diacritics': True    # 变音符号
    }

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    # 使用临时目录而不是固定目录
    UPLOAD_FOLDER = tempfile.gettempdir()
    OUTPUT_FOLDER = tempfile.gettempdir()
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max-limit

    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
        app.config['SECRET_KEY'] = Config.SECRET_KEY 