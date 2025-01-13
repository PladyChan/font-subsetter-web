import pytest
from app.utils import process_font
import os

def test_process_font():
    # 基本功能测试
    test_font = "tests/fixtures/test.ttf"  # 需要添加测试字体
    output_path = "tests/output/test_output.ttf"
    
    options = {
        'latin': True,
        'numbers': True,
        'punctuation': True,
        'degree': False,
        'currency': False,
        'math': False,
        'copyright': False,
        'arrows': False,
        'ligatures': False,
        'fractions': False,
        'superscript': False,
        'diacritics': False
    }
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    result = process_font(test_font, output_path, options)
    assert result == True 