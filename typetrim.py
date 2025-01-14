"""
TypeTrim - Smart Font Subsetting Tool
-----------------------------------
Copyright (c) 2024 PladyChan
All rights reserved.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
""" 

from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options
import string
import os
import tempfile
import logging

logging.basicConfig(level=logging.DEBUG)

def process_font_file(input_path, options=None):
    """处理字体文件并返回结果"""
    try:
        # 加载字体文件
        font = TTFont(input_path)
        
        # 根据选项构建字符集
        chars = set()
        
        # 基础字符
        chars.update(string.ascii_letters)  # 英文字母
        chars.update(string.digits)         # 数字
        chars.update(string.punctuation)    # 标点符号
        chars.add('°')                      # 度数符号
        
        # 扩展字符
        chars.update('$€¥£')               # 货币符号
        chars.update('+-×÷=')              # 数学符号
        chars.update('©®™')                # 版权符号
        chars.update('←→↑↓')               # 箭头
        chars.update('éèêëāīūēīō')         # 变音符号
        
        # 添加自定义字符
        if options and 'custom_chars' in options:
            chars.update(options['custom_chars'])
        
        # 设置 subsetter 选项
        subsetter_options = Options()
        subsetter_options.layout_features = ['kern', 'liga', 'frac']
        subsetter_options.ignore_missing_glyphs = True
        subsetter_options.ignore_missing_unicodes = True
        subsetter_options.desubroutinize = True
        
        # 处理字体
        subsetter = Subsetter(options=subsetter_options)
        subsetter.populate(unicodes=[ord(char) for char in chars])
        
        try:
            subsetter.subset(font)
        except Exception as e:
            # 如果出错，尝试不使用布局特性
            subsetter_options.layout_features = []
            subsetter_options.no_subset_tables += ['GSUB', 'GPOS']
            subsetter = Subsetter(options=subsetter_options)
            subsetter.populate(unicodes=[ord(char) for char in chars])
            subsetter.subset(font)
        
        # 使用临时文件保存输出
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(input_path)[1]) as output_temp:
            output_path = output_temp.name
            font.save(output_path)
        
        # 计算文件大小
        original_size = os.path.getsize(input_path) / 1024
        new_size = os.path.getsize(output_path) / 1024
        reduction = ((original_size - new_size) / original_size * 100)
        
        logging.debug(f"接收到的选项: {options}")
        logging.debug(f"生成的字符集: {chars}")
        
        return {
            'success': True,
            'filename': os.path.basename(input_path),
            'original_size': f"{original_size:.1f}KB",
            'new_size': f"{new_size:.1f}KB",
            'reduction': f"{reduction:.1f}%",
            'output_path': output_path
        }
        
    except Exception as e:
        raise Exception(f"处理字体文件时出错: {str(e)}") 