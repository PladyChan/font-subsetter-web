import os
import tempfile

def get_config():
    """获取默认配置"""
    return {
        # 基础字符（默认选中）
        'latin': True,            # 英文字母
        'numbers': True,          # 数字
        'en_punctuation': True,   # 英文标点
        
        # 扩展字符（部分默认选中）
        'currency': True,         # 货币符号
        'math': True,            # 数学符号
        'copyright': False,       # 版权符号
        'arrows': False,         # 箭头
        
        # 特殊功能（默认关闭）
        'ligatures': False,      # 连字
        'fractions': False,      # 分数
        'superscript': False,    # 上标下标
        'diacritics': False      # 变音符号
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